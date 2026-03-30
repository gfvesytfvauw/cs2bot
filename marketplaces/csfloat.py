"""
CSFloat marketplace module.
"""

import aiohttp
from utils import log


class CSFloat:
    NAME = "CSFloat"
    BASE = "https://csfloat.com/api/v1"

    def __init__(self, api_key: str):
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

    async def get_listings(self, session, name, max_float=1.0, min_float=0.0, max_price=99999, min_price=0.0):
        params = {
            "market_hash_name": name,
            "sort_by": "price",
            "order": "asc",
            "max_float": max_float,
            "min_float": min_float,
            "max_price": int(max_price * 100),
            "limit": 10,
            "type": "buy_now",
        }
        if min_price > 0:
            params["min_price"] = int(min_price * 100)

        try:
            async with session.get(
                f"{self.BASE}/listings",
                headers=self.headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as r:
                if r.status == 429:
                    log("⚠️  CSFloat rate limited")
                    return []
                if r.status != 200:
                    log(f"⚠️  CSFloat returned status {r.status}")
                    return []
                try:
                    data = await r.json(content_type=None)
                    return [self._normalize(l) for l in data.get("data", [])]
                except Exception as e:
                    log(f"⚠️  CSFloat JSON parse error: {e}")
                    return []
        except Exception as e:
            log(f"CSFloat fetch error: {e}")
            return []

    async def buy(self, session, listing):
        try:
            async with session.post(
                f"{self.BASE}/listings/{listing['id'].replace('csf_', '')}/buy",
                headers=self.headers,
                json={"price": listing["raw_price"]},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as r:
                try:
                    result = await r.json(content_type=None)
                except Exception:
                    result = {"status": r.status}
                return r.status == 200, result
        except Exception as e:
            return False, {"error": str(e)}

    def _normalize(self, listing):
        return {
            "id": f"csf_{listing['id']}",
            "market": self.NAME,
            "name": listing["item"].get("market_hash_name", ""),
            "float": listing["item"].get("float_value", 0),
            "price_usd": listing["price"] / 100,
            "raw_price": listing["price"],
            "inspect_url": listing["item"].get("inspect_link"),
            "wear": listing["item"].get("wear_name", ""),
        }
