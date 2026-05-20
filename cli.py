#!/usr/bin/env python3

import argparse
import logging
import os
import sys

import httpx

from bot.logging_config import setup_logging
from bot.client import BinanceClient
from bot.orders import place_order

logger = logging.getLogger(__name__)


def get_credentials() -> tuple[str, str]:
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print(
            "\n[ERROR] BINANCE_API_KEY and BINANCE_API_SECRET environment variables "
            "must be set.\n"
            "  export BINANCE_API_KEY='your_key'\n"
            "  export BINANCE_API_SECRET='your_secret'\n",
            file=sys.stderr,
        )
        sys.exit(1)

    return api_key, api_secret


def cmd_place(args: argparse.Namespace) -> None:
    api_key, api_secret = get_credentials()

    try:
        with BinanceClient(api_key, api_secret) as client:
            place_order(
                client=client,
                symbol=args.symbol,
                side=args.side,
                order_type=args.type,
                quantity=args.quantity,
                price=args.price,
            )
        print("\nOrder placed successfully.")
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        print(f"\n[VALIDATION ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        logger.error("API error: %s", exc)
        print(f"\n[API ERROR] {exc}", file=sys.stderr)
        err_detail = exc.response.text.strip()
        if err_detail:
            print(f"  Binance response: {err_detail}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unexpected error while placing order")
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_account(args: argparse.Namespace) -> None:
    api_key, api_secret = get_credentials()

    try:
        with BinanceClient(api_key, api_secret) as client:
            info = client.get_account()

        print("\n-- Account Summary -")
        total_wallet = info.get("totalWalletBalance", "N/A")
        total_unrealised = info.get("totalUnrealizedProfit", "N/A")
        total_margin = info.get("totalMarginBalance", "N/A")
        print(f"  Wallet Balance      : {total_wallet} USDT")
        print(f"  Unrealised PnL      : {total_unrealised} USDT")
        print(f"  Margin Balance      : {total_margin} USDT")

        assets = [a for a in info.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
        if assets:
            print("\n  Non-zero assets:")
            for asset in assets:
                print(f"    {asset['asset']:10s}  wallet={asset['walletBalance']}")
        print("--------------------------------------------\n")

    except Exception as exc:
        logger.exception("Failed to fetch account info")
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_price(args: argparse.Namespace) -> None:
    api_key, api_secret = get_credentials()
    try:
        with BinanceClient(api_key, api_secret) as client:
            data = client.get_price(args.symbol)
        print(f"\n  {data['symbol']:12s} : ${float(data['price']):,.2f}\n")
    except Exception as exc:
        logger.exception("Failed to fetch price")
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_book(args: argparse.Namespace) -> None:
    api_key, api_secret = get_credentials()
    try:
        with BinanceClient(api_key, api_secret) as client:
            data = client.get_depth(args.symbol, limit=args.limit)
        bids = data.get("bids", [])[:args.limit]
        asks = data.get("asks", [])[:args.limit]
        print(f"\n  Order Book - {args.symbol}\n")
        w = 14
        print(f"  {'BIDS':>{w}}  |  {'ASKS':<{w}}")
        print(f"  {'-' * (w + 3 + w)}")
        for i in range(max(len(bids), len(asks))):
            bid = f"${float(bids[i][0]):,.2f}  x{bids[i][1]}" if i < len(bids) else ""
            ask = f"${float(asks[i][0]):,.2f}  x{asks[i][1]}" if i < len(asks) else ""
            print(f"  {bid:>{w}}  |  {ask:<{w}}")
        print()
    except Exception as exc:
        logger.exception("Failed to fetch order book")
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_open_orders(args: argparse.Namespace) -> None:
    api_key, api_secret = get_credentials()
    try:
        with BinanceClient(api_key, api_secret) as client:
            orders = client.get_open_orders(args.symbol)
        if not orders:
            print("\n  No open orders.\n")
            return
        sym_w, id_w, side_w = 12, 12, 6
        print(f"\n  {'Symbol':<{sym_w}} {'OrderID':<{id_w}} {'Side':<{side_w}} {'Type':>10} {'Qty':>10} {'Price':>12}")
        print(f"  {'-' * (sym_w + id_w + side_w + 10 + 10 + 12)}")
        for o in orders:
            price = float(o.get("price", 0)) if o.get("price") != "0.00000000" else None
            if price is not None:
                print(
                    f"  {o['symbol']:<{sym_w}} "
                    f"{o['orderId']:<{id_w}} "
                    f"{o['side']:<{side_w}} "
                    f"{o['type']:>10} "
                    f"{o.get('origQty', 0):>10} "
                    f"${price:>11,.2f}"
                )
            else:
                print(
                    f"  {o['symbol']:<{sym_w}} "
                    f"{o['orderId']:<{id_w}} "
                    f"{o['side']:<{side_w}} "
                    f"{o['type']:>10} "
                    f"{o.get('origQty', 0):>10}  {'MARKET':>12}"
                )
        print()
    except Exception as exc:
        logger.exception("Failed to fetch open orders")
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_positions(args: argparse.Namespace) -> None:
    api_key, api_secret = get_credentials()
    try:
        with BinanceClient(api_key, api_secret) as client:
            positions = client.get_position_risk()
        active = [p for p in positions if float(p.get("positionAmt", 0)) != 0]
        if not active:
            print("\n  No open positions.\n")
            return
        sym_w, amt_w, ep_w, mp_w, pnl_w = 12, 12, 14, 14, 14
        print(f"\n  {'Symbol':<{sym_w}} {'Amt':<{amt_w}} {'EntryPrice':>{ep_w}} {'MarkPrice':>{mp_w}} {'UnrealisedPnL':>{pnl_w}}")
        print(f"  {'-' * (sym_w + amt_w + ep_w + mp_w + pnl_w)}")
        for p in active:
            amt = float(p.get("positionAmt", 0))
            ep = float(p.get("entryPrice", 0))
            mp = float(p.get("markPrice", 0))
            pnl = float(p.get("unRealizedProfit", 0))
            side = "LONG" if amt > 0 else "SHORT"
            print(
                f"  {p['symbol']:<{sym_w}} "
                f"{side:<{amt_w}} "
                f"${ep:>12,.2f} "
                f"${mp:>12,.2f} "
                f"${pnl:>12,.2f}"
            )
        print()
    except Exception as exc:
        logger.exception("Failed to fetch positions")
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_cancel(args: argparse.Namespace) -> None:
    api_key, api_secret = get_credentials()
    try:
        with BinanceClient(api_key, api_secret) as client:
            resp = client.cancel_order(args.symbol, args.order_id)
        print(f"\n  Cancelled order {args.order_id} on {args.symbol}.")
        print(f"  Status : {resp.get('status', 'N/A')}\n")
    except Exception as exc:
        logger.exception("Failed to cancel order")
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_order_status(args: argparse.Namespace) -> None:
    api_key, api_secret = get_credentials()
    try:
        with BinanceClient(api_key, api_secret) as client:
            o = client.get_order(args.symbol, args.order_id)
        print(f"\n  Symbol      : {o['symbol']}")
        print(f"  OrderID     : {o['orderId']}")
        print(f"  Side        : {o['side']}")
        print(f"  Type        : {o['type']}")
        print(f"  Qty         : {o.get('origQty', 'N/A')}")
        print(f"  ExecutedQty : {o.get('executedQty', 0)}")
        print(f"  Status      : {o['status']}")
        price = o.get("price", "0")
        avg = o.get("avgPrice", "0")
        print(f"  Price       : {price if price != '0.00000000' else 'N/A'}")
        print(f"  AvgPrice    : {avg if float(avg) > 0 else 'N/A'}\n")
    except Exception as exc:
        logger.exception("Failed to fetch order status")
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log level",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    place_parser = sub.add_parser("place", help="Place a new order")
    place_parser.add_argument("--symbol", required=True, help="Trading symbol, e.g. BTCUSDT")
    place_parser.add_argument("--side", required=True, choices=["BUY", "SELL"], help="Order side")
    place_parser.add_argument("--type", required=True, choices=["MARKET", "LIMIT"], help="Order type")
    place_parser.add_argument("--quantity", required=True, type=float, help="Order quantity")
    place_parser.add_argument("--price", type=float, default=None, help="Limit price (LIMIT only)")
    place_parser.set_defaults(func=cmd_place)

    account_parser = sub.add_parser("account", help="Show account balance")
    account_parser.set_defaults(func=cmd_account)

    price_parser = sub.add_parser("price", help="Show last traded price")
    price_parser.add_argument("--symbol", required=True, help="Trading symbol, e.g. BTCUSDT")
    price_parser.set_defaults(func=cmd_price)

    book_parser = sub.add_parser("book", help="Show order book")
    book_parser.add_argument("--symbol", required=True, help="Trading symbol, e.g. BTCUSDT")
    book_parser.add_argument("--limit", type=int, default=20, help="Depth (default 20)")
    book_parser.set_defaults(func=cmd_book)

    oo_parser = sub.add_parser("open-orders", help="List open orders")
    oo_parser.add_argument("--symbol", default=None, help="Filter by symbol")
    oo_parser.set_defaults(func=cmd_open_orders)

    pos_parser = sub.add_parser("positions", help="Show open positions")
    pos_parser.set_defaults(func=cmd_positions)

    cancel_parser = sub.add_parser("cancel", help="Cancel an open order")
    cancel_parser.add_argument("--symbol", required=True, help="Trading symbol, e.g. BTCUSDT")
    cancel_parser.add_argument("--order-id", required=True, type=int, help="Order ID")
    cancel_parser.set_defaults(func=cmd_cancel)

    status_parser = sub.add_parser("order-status", help="Check order status")
    status_parser.add_argument("--symbol", required=True, help="Trading symbol, e.g. BTCUSDT")
    status_parser.add_argument("--order-id", required=True, type=int, help="Order ID")
    status_parser.set_defaults(func=cmd_order_status)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    setup_logging(level=log_level)

    logger.debug("CLI args: %s", args)
    args.func(args)


if __name__ == "__main__":
    main()
