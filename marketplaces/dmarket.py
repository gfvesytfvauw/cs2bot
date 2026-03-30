"""
DMarket marketplace module.
Docs: https://docs.dmarket.com
Uses HMAC-SHA256 signature auth on buy requests.
"""

import hashlib
import hmac
import time

import aiohttp
from utils import log


class DMarket:
    NAME = "DMarket"
    BASE = "https://api.dmarket.com"

    def __init__(self, public_key: str, secret_key: str):
        self.public_key = public_key
        self.secret_key = secret_key

    def _sign(self, method: str, path: str, body: str = "") -> dict:
        """Generate HMAC-SHA256 signature headers required by DMarket."""
        ts = str(int(time.time()))
        string_to_sign = method.upper() + path + body + ts
        signature = hmac.new(
            self.secret_key.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()
        return {
            "X-Api-Key": self.public_key,
            "X-Request-Sign": f"dmar ed25519 {signature}",
            "X-Sign-Date": ts,
            "Content-Type": "application/json",
        }

    async def get_listings(
        self,
        session: aiohttp.ClientSession,
        name: str,
        max_float: float = 1.0,
        min_float: float = 0.0,
        max_price: float = 99999,
        min_price: float = 0.0,
    ) -> list[dict]:
        path = "/exchange/v1/market/items"
        params = {
            "title": name,
            "gameId": "a8db",  # CS2 game ID on DMarket
            "limit": 10,
            "orderBy": "price",
            "orderDir": "asc",
            "priceFrom": int(min_price * 100),
            "priceTo": int(max_price * 100),
            "floatFrom": min_float,
            "floatTo": max_float,
            "currency": "USD",
        }

        try:
            async with session.get(
                f"{self.BASE}{path}",
                headers=self._sign("GET", path),
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as r:
                if r.status == 429:
                    log("⚠️  DMarket rate limited")
                    return []
                if r.status != 200:
                    return []
                data = await r.json()
                return [self._normalize(obj) for obj in data.get("objects", [])]
        except Exception as e:
            log(f"DMarket fetch error: {e}")
            return []

    async def buy(self, session: aiohttp.ClientSession, listing: dict) -> tuple[bool, dict]:
        path = "/exchange/v1/offers-buy"
        body_dict = {"offers": [{"offerId": listing["raw_id"], "price": {"amount": str(listing["raw_price"]), "currency": "USD"}}]}
        import json
        body = json.dumps(body_dict, separators=(",", ":"))

        try:
            async with session.post(
                f"{self.BASE}{path}",
                headers=self._sign("POST", path, body),
                data=body,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as r:
                result = await r.json()
                return r.status == 200, result
        except Exception as e:
            return False, {"error": str(e)}

    def _normalize(self, obj: dict) -> dict:
        extra = obj.get("extra", {})
        price_cents = int(obj.get("price", {}).get("USD", "0"))
        return {
            "id": f"dm_{obj.get('offerId', '')}",
            "market": self.NAME,
            "name": obj.get("title", ""),
            "float": float(extra.get("floatValue", 0) or 0),
            "price_usd": price_cents / 100,
            "raw_price": price_cents,
            "raw_id": obj.get("offerId", ""),
            "inspect_url": extra.get("inspectInGame"),
            "wear": extra.get("exterior", ""),
        }
