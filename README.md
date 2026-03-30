# CS2 Skin Sniper Bot

Auto-buys CS2 skins matching your float and price criteria across multiple marketplaces.
Sends Discord notifications for every purchase, deal alert, and error.

## Supported Marketplaces
- **CSFloat** — best for float-specific sniping
- **DMarket** — large liquidity, HMAC auth
- **Waxpeer** — good P2P listings

---

## Setup

### 1. Install Python & dependencies
```bash
# Requires Python 3.11+
pip install -r requirements.txt
```

### 2. Get your API keys

**CSFloat**
1. Go to https://csfloat.com/profile
2. Settings → API Key → Generate

**DMarket**
1. Go to https://dmarket.com/account
2. API → Create API Key (gives you a public + secret key pair)

**Waxpeer**
1. Go to https://waxpeer.com/profile
2. Settings → API → Generate key

**Discord Webhook**
1. Open a Discord channel → Edit Channel → Integrations → Webhooks
2. New Webhook → Copy URL

### 3. Edit config.json
```json
{
  "discord_webhook": "https://discord.com/api/webhooks/...",
  "api_keys": {
    "csfloat": "your_key_here",
    "dmarket": {
      "public": "your_public_key",
      "secret": "your_secret_key"
    },
    "waxpeer": "your_key_here"
  },
  "poll_interval": 20,
  "max_spend_per_session": 200.00,
  "watchlist": [...]
}
```

You can leave out any market you don't use — the bot skips markets with no key.

### 4. Configure your watchlist

Each skin entry supports:

| Field | Required | Description |
|---|---|---|
| `name` | ✅ | Exact market_hash_name (e.g. "AK-47 \| Redline") |
| `max_price` | ✅ | Max price in USD |
| `max_float` | ❌ | Default: 1.0 |
| `min_float` | ❌ | Default: 0.0 |
| `min_price` | ❌ | Useful to filter out suspiciously cheap/duped items |
| `notify_only` | ❌ | Set `true` to alert without auto-buying |
| `note` | ❌ | Just a label for yourself |

### 5. Run the bot
```bash
python bot.py
```

---

## Hosting (cheapest options)

### Oracle Cloud Free Tier (recommended — genuinely free)
1. Sign up at https://cloud.oracle.com/
2. Create an Always Free ARM VM (Ampere A1)
3. SSH in and run:
```bash
sudo apt update && sudo apt install python3-pip -y
pip install -r requirements.txt
# Run in background with nohup:
nohup python bot.py > bot.log 2>&1 &
```

### Railway (~$5/mo, easiest)
1. Push this folder to a GitHub repo
2. Connect repo at https://railway.app
3. Set start command: `python bot.py`
4. Add your config.json secrets as environment variables

### Hetzner VPS (€3.29/mo, most reliable)
- Cheapest CX11 plan, Ubuntu 22.04
- Same setup as Oracle above

---

## Tips

- **poll_interval**: Don't go below 15s on CSFloat or you'll hit rate limits
- **notify_only**: Use this for expensive skins where you want to decide manually
- **max_spend_per_session**: Safety net to avoid runaway buying
- **Float ranges for trade-ups**: Use both `min_float` and `max_float` to target exact trade-up ranges
- **Balance**: Make sure you have funds loaded on each marketplace before running
