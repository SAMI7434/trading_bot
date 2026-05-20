"""
orders.py - High-level order placement logic.
"""

from __future__ import annotations

import logging

from .client import BinanceClient
from .validators import validate_order_params

logger = logging.getLogger(__name__)


def _format_order_summary(params: dict) -> str:
    lines = [
        "+--- Order Request --------------------------",
        f"|  Symbol    : {params['symbol']}",
        f"|  Side      : {params['side']}",
        f"|  Type      : {params['type']}",
        f"|  Quantity  : {params['quantity']}",
    ]
    if "price" in params:
        lines.append(f"|  Price     : {params['price']}")
    if "timeInForce" in params:
        lines.append(f"|  TIF       : {params['timeInForce']}")
    lines.append("+-------------------------------------------")
    return "\n".join(lines)


def _format_order_response(response: dict) -> str:
    lines = [
        "+--- Order Response -------------------------",
        f"|  Order ID      : {response.get('orderId', 'N/A')}",
        f"|  Client OID    : {response.get('clientOrderId', 'N/A')}",
        f"|  Status        : {response.get('status', 'N/A')}",
        f"|  Executed Qty  : {response.get('executedQty', 'N/A')}",
        f"|  Avg Price     : {response.get('avgPrice', 'N/A')}",
        f"|  Symbol        : {response.get('symbol', 'N/A')}",
        f"|  Side          : {response.get('side', 'N/A')}",
        f"|  Type          : {response.get('type', 'N/A')}",
    ]
    if response.get("price"):
        lines.append(f"|  Price         : {response['price']}")
    lines.append("+-------------------------------------------")
    return "\n".join(lines)


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
) -> dict:
    params = validate_order_params(symbol, side, order_type, quantity, price)

    summary = _format_order_summary(params)
    print(summary)
    logger.info("Placing order: %s", params)

    response = client.place_order(**params)

    response_summary = _format_order_response(response)
    print(response_summary)
    logger.info(
        "Order placed: orderId=%s status=%s",
        response.get("orderId"), response.get("status"),
    )

    return response
