"""
client.py - Binance Futures Testnet API client.
Handles auth signing, clock sync, and all HTTP calls to the exchange.
"""

import time
import hmac
import hashlib
import logging
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, base_url: str = TESTNET_BASE_URL):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self._clock_offset_ms = 0
        self._client = httpx.Client(
            headers={
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=10.0,
        )
        self._sync_clock()
        logger.info("BinanceClient initialised (base_url=%s)", self.base_url)

    def _sign(self, params: dict) -> dict:
        params["timestamp"] = int(time.time() * 1000) + self._clock_offset_ms
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _sync_clock(self) -> None:
        try:
            resp = httpx.get("https://testnet.binancefuture.com/fapi/v1/time", timeout=5.0)
            resp.raise_for_status()
            server_ts = resp.json()["serverTime"]
            local_ts = int(time.time() * 1000)
            self._clock_offset_ms = server_ts - local_ts
            logger.debug("Clock offset set to %d ms", self._clock_offset_ms)
        except Exception:
            logger.warning("Could not sync clock offset; using local system time")

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"

    def get_exchange_info(self) -> dict:
        url = self._url("/fapi/v1/exchangeInfo")
        logger.debug("GET %s", url)
        response = self._client.get(url)
        response.raise_for_status()
        return response.json()

    def get_account(self) -> dict:
        params = self._sign({})
        url = self._url("/fapi/v2/account")
        logger.debug("GET %s params=%s", url, params)
        response = self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_price(self, symbol: str) -> dict:
        url = self._url("/fapi/v1/ticker/price")
        logger.debug("GET %s symbol=%s", url, symbol)
        response = self._client.get(url, params={"symbol": symbol})
        response.raise_for_status()
        return response.json()

    def get_depth(self, symbol: str, limit: int = 20) -> dict:
        url = self._url("/fapi/v1/depth")
        logger.debug("GET %s symbol=%s limit=%s", url, symbol, limit)
        response = self._client.get(
            url, params={"symbol": symbol, "limit": min(limit, 500)}
        )
        response.raise_for_status()
        return response.json()

    def get_open_orders(self, symbol: str | None = None) -> list[dict]:
        params = self._sign({})
        url = self._url("/fapi/v1/openOrders")
        logger.debug("GET %s symbol=%s", url, symbol)
        response = self._client.get(
            url,
            params={**params, **({"symbol": symbol} if symbol else {})},
        )
        response.raise_for_status()
        return response.json()

    def get_position_risk(self) -> list[dict]:
        params = self._sign({})
        url = self._url("/fapi/v2/positionRisk")
        logger.debug("GET %s", url)
        response = self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_order(self, symbol: str, order_id: int) -> dict:
        params = self._sign({"symbol": symbol, "orderId": order_id})
        url = self._url("/fapi/v1/order")
        logger.debug("GET %s symbol=%s orderId=%s", url, symbol, order_id)
        response = self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        params = self._sign({"symbol": symbol, "orderId": order_id})
        url = self._url("/fapi/v1/order")
        logger.info("DELETE %s | symbol=%s orderId=%s", url, symbol, order_id)
        response = self._client.delete(url, params=params)
        logger.debug("Response status=%s body=%s", response.status_code, response.text)
        if not response.is_success:
            logger.error("Binance API error %s: %s", response.status_code, response.text)
        response.raise_for_status()
        return response.json()

    def place_order(self, **kwargs) -> dict:
        params = self._sign(dict(kwargs))
        url = self._url("/fapi/v1/order")
        logger.info(
            "POST %s | symbol=%s side=%s type=%s qty=%s price=%s",
            url,
            kwargs.get("symbol"),
            kwargs.get("side"),
            kwargs.get("type"),
            kwargs.get("quantity"),
            kwargs.get("price", "N/A"),
        )
        response = self._client.post(url, data=params)
        logger.debug("Response status=%s body=%s", response.status_code, response.text)
        if not response.is_success:
            logger.error("Binance API error %s: %s", response.status_code, response.text)
        response.raise_for_status()
        return response.json()

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
