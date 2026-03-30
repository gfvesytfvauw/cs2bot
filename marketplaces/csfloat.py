import aiohttp
from utils import log


class CSFloat:
    NAME = "CSFloat"
    BASE = "https://csfloat.com/api/v1"

    def __init__(self, api_key):
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

    async def get_listings(self, session, name, max_float=1.0, min_float=0.0, max_price=99999, min_price=0.0):
        params = {
            "market_hash_name": name,
            "sort_by": "lowest_price",
            "limit": 50,
            "type": "buy_now",
            "max_float": max_float,
            "min_float": min_float,
        }
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
                    text = await r.text()
                    log(f"⚠️  CSFloat {r.status}: {text[:200]}")
                    return []
                try:
                    data = await r.json(content_type=None)
                    listings = data.get("data", [])
                    log(f"🔍 CSFloat raw: {len(listings)} listings before filter")
                    if listings:
                        fv = listings[0]["item"].get("float_value", 0)
                        price = listings[0]["price"] / 100
                        log(f"🔍 First listing: float={fv:.6f} price=${price:.2f}")
                    results = []
                    for l in listings:
                        fv = l["item"].get("float_value", 0)
                        price = l["price"] / 100
                        if min_float <= fv <= max_float and min_price <= price <= max_price:
                            results.append(self._normalize(l))
                    return results
                except Exception as e:
                    log(f"⚠️  CSFloat parse error: {e}")
                    return []
        except Exception as e:
            log(f"CSFloat error: {e}")
            return []

    def _normalize(self, listing):
        return {
            "id": f"csf_{listing['id']}",
            "raw_id": listing["id"],
            "market": self.NAME,
            "name": listing["item"].get("market_hash_name", ""),
            "float": listing["item"].get("float_value", 0),
            "price_usd": listing["price"] / 100,
            "raw_price": listing["price"],
            "inspect_url": listing["item"].get("inspect_link"),
            "wear": listing["item"].get("wear_name", ""),
        }

    async def buy(self, session, listing):
    try:
        async with session.post(
            f"{self.BASE}/listings/{listing['raw_id']}/buy",
            headers=self.headers,
            json={"price": listing["raw_price"]},
            timeout=aiohttp.ClientTimeout(total=15)
        ) as r:
            try:
                result = await r.json(content_type=None)
            except Exception:
                result = {"status": r.status}
            log(f"🔍 Buy response {r.status}: {result}")
            return r.status == 200, result
    except Exception as e:
        return False, {"error": str(e)}
