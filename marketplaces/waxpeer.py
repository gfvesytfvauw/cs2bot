"""
Waxpeer marketplace module.
Docs: https://docs.waxpeer.com
Simple bearer token auth.
"""

import aiohttp
from utils import log


class Waxpeer:
    NAME = "Waxpeer"
    BASE = "https://api.waxpeer.com/v1"

    def __init__(self, api_key: str):
        self.headers = {
            "Authorization": f"Bearer {api_key}",
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
        params = {
            "name": name,
            "game": "csgo",
            "sort": "price",
            "order": "asc",
            "limit": 10,
            "minPrice": int(min_price * 1000),   # Waxpeer uses 1/1000 USD
            "maxPrice": int(max_price * 1000),
            "minFloat": min_float,
            "maxFloat": max_float,
        }

        try:
            async with session.get(
                f"{self.BASE}/buy-orders",
                headers=self.headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as r:
                if r.status == 429:
                    log("⚠️  Waxpeer rate limited")
                    return []
                if r.status != 200:
                    return []
                data = await r.json()
                items = data.get("items", [])
                return [self._normalize(i) for i in items if self._in_float_range(i, min_float, max_float)]
        except Exception as e:
            log(f"Waxpeer fetch error: {e}")
            return []

    async def buy(self, session: aiohttp.ClientSession, listing: dict) -> tuple[bool, dict]:
        try:
            async with session.post(
                f"{self.BASE}/buy-one-p2p-name",
                headers=self.headers,
                json={"name": listing["name"], "max_price": listing["raw_price"], "id": listing["raw_id"]},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as r:
                result = await r.json()
                return r.status == 200 and result.get("success", False), result
        except Exception as e:
            return False, {"error": str(e)}

    def _in_float_range(self, item: dict, min_f: float, max_f: float) -> bool:
        f = float(item.get("float", 1.0) or 1.0)
        return min_f <= f <= max_f

    def _normalize(self, item: dict) -> dict:
        price_raw = item.get("price", 0)  # in 1/1000 USD
        return {
            "id": f"wp_{item.get('item_id', '')}",
            "market": self.NAME,
            "name": item.get("name", ""),
            "float": float(item.get("float", 0) or 0),
            "price_usd": price_raw / 1000,
            "raw_price": price_raw,
            "raw_id": item.get("item_id", ""),
            "inspect_url": item.get("inspect_link"),
            "wear": item.get("wear", ""),
        }
