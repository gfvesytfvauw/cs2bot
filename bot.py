"""
CS2 Skin Sniper Bot - CSFloat only
"""

import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import aiohttp

from marketplaces.csfloat import CSFloat
from notifier import Notifier
from utils import load_config, log

config = load_config("config.json")
notifier = Notifier(config["discord_webhook"])
MARKET = CSFloat(config["api_keys"]["csfloat"])
BOUGHT_IDS: set[str] = set()


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log(f"🌐 Health server on port {port}")


async def process_listing(session, listing, skin):
    lid = listing["id"]
    if lid in BOUGHT_IDS:
        return

    BOUGHT_IDS.add(lid)
    float_val = listing["float"]
    price_usd = listing["price_usd"]

    log(f"🎯 Found: {skin['name']} | float {float_val:.6f} | ${price_usd:.2f}")

    if skin.get("notify_only", False):
        await notifier.send_deal_found(session, skin["name"], float_val, price_usd, "CSFloat", listing.get("inspect_url"))
        return

    success, result = await MARKET.buy(session, listing)

    if success:
        log(f"✅ Bought {skin['name']} for ${price_usd:.2f}")
        await notifier.send_purchase(session, skin["name"], float_val, price_usd, "CSFloat", listing.get("inspect_url"))
    else:
        BOUGHT_IDS.discard(lid)
        log(f"❌ Buy failed: {result}")
        await notifier.send_error(session, skin["name"], "CSFloat", str(result))


async def check_skin(session, skin):
    try:
        listings = await MARKET.get_listings(
            session,
            name=skin["name"],
            max_float=skin.get("max_float", 1.0),
            min_float=skin.get("min_float", 0.0),
            max_price=skin["max_price"],
            min_price=skin.get("min_price", 0.0),
        )
        log(f"📋 CSFloat: {len(listings)} listings for {skin['name']}")
        for listing in listings:
            await process_listing(session, listing, skin)
    except Exception as e:
        log(f"⚠️  Error checking {skin['name']}: {e}")


async def bot_loop():
    async with aiohttp.ClientSession() as session:
        await notifier.send_startup(session, ["CSFloat"], len(config["watchlist"]))

        cycle = 0
        while True:
            start = asyncio.get_event_loop().time()
            cycle += 1
            tasks = [check_skin(session, skin) for skin in config["watchlist"]]
            await asyncio.gather(*tasks)
            log(f"✅ Cycle {cycle} complete")
            elapsed = asyncio.get_event_loop().time() - start
            sleep_for = max(0, config.get("poll_interval", 20) - elapsed)
            await asyncio.sleep(sleep_for)


def main():
    start_health_server()
    log("🤖 CS2 Sniper Bot starting (CSFloat only)...")
    log(f"   Watching {len(config['watchlist'])} skins")
    log(f"   Poll interval: {config.get('poll_interval', 20)}s")
    asyncio.run(bot_loop())


if __name__ == "__main__":
    main()
