"""
Discord webhook notifier.
Sends rich embeds for purchases, deals, errors, and startup.
"""

import aiohttp
from datetime import datetime
from utils import log


class Notifier:
    def __init__(self, webhook_url: str):
        self.url = webhook_url

    async def _send(self, session: aiohttp.ClientSession, payload: dict):
        if not self.url or "YOUR_WEBHOOK" in self.url:
            return
        try:
            async with session.post(self.url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status not in (200, 204):
                    log(f"Discord webhook error: {r.status}")
        except Exception as e:
            log(f"Discord send error: {e}")

    async def send_purchase(self, session, name, float_val, price_usd, market, inspect_url=None):
        embed = {
            "title": "✅ Purchase Successful",
            "color": 0x00FF00,
            "fields": [
                {"name": "Skin", "value": f"`{name}`", "inline": True},
                {"name": "Market", "value": market, "inline": True},
                {"name": "Price", "value": f"${price_usd:.2f}", "inline": True},
                {"name": "Float", "value": f"`{float_val:.8f}`", "inline": True},
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "CS2 Sniper Bot"}
        }
        if inspect_url:
            embed["fields"].append({"name": "Inspect", "value": f"[Click to inspect]({inspect_url})", "inline": False})
        await self._send(session, {"embeds": [embed]})

    async def send_deal_found(self, session, name, float_val, price_usd, market, inspect_url=None):
        """For notify_only skins — alert without buying."""
        embed = {
            "title": "🔔 Deal Found (Notify Only)",
            "color": 0xFFAA00,
            "fields": [
                {"name": "Skin", "value": f"`{name}`", "inline": True},
                {"name": "Market", "value": market, "inline": True},
                {"name": "Price", "value": f"${price_usd:.2f}", "inline": True},
                {"name": "Float", "value": f"`{float_val:.8f}`", "inline": True},
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "CS2 Sniper Bot — notify_only mode"}
        }
        if inspect_url:
            embed["fields"].append({"name": "Inspect", "value": f"[Click to inspect]({inspect_url})", "inline": False})
        await self._send(session, {"embeds": [embed]})

    async def send_error(self, session, name, market, error_msg):
        embed = {
            "title": "❌ Buy Failed",
            "color": 0xFF0000,
            "fields": [
                {"name": "Skin", "value": f"`{name}`", "inline": True},
                {"name": "Market", "value": market, "inline": True},
                {"name": "Error", "value": f"```{error_msg[:200]}```", "inline": False},
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "CS2 Sniper Bot"}
        }
        await self._send(session, {"embeds": [embed]})

    async def send_startup(self, session, markets: list[str], watchlist_count: int):
        embed = {
            "title": "🤖 CS2 Sniper Bot Online",
            "color": 0x5865F2,
            "fields": [
                {"name": "Markets", "value": ", ".join(markets) or "None", "inline": True},
                {"name": "Watching", "value": f"{watchlist_count} skins", "inline": True},
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "CS2 Sniper Bot"}
        }
        await self._send(session, {"embeds": [embed]})
