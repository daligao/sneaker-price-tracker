#!/usr/bin/env python3
"""
Sneaker Price Tracker
Runs daily via GitHub Actions, saves price history to data/prices.json
"""

import json
import random
import datetime
import os
import time

# ── Optional: real scraping libs (pip install requests beautifulsoup4)
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


DATA_FILE = "data/prices.json"
CONFIG_FILE = "config.json"


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── DEMO MODE: generates realistic mock prices ──────────────────────────────
# Base prices in CNY (approximate market value)
BASE_PRICES = {
    "Nike Air Jordan 1 Retro High OG": 2800,
    "New Balance 990v6 Made in USA": 1800,
    "Adidas Samba OG": 1200,
}

def fetch_demo_price(sneaker):
    """Simulates price with realistic daily fluctuation (±3%)"""
    base = BASE_PRICES.get(sneaker["name"], 1500)
    # Add day-based trend so graph looks interesting
    day_of_year = datetime.date.today().timetuple().tm_yday
    trend = base * 0.001 * (day_of_year % 30 - 15)  # slow cycle
    noise = random.uniform(-0.03, 0.03) * base
    price = round(base + trend + noise, 0)
    return {
        "price": price,
        "source": "demo",
        "url": "#"
    }


# ── REAL MODE: plug in actual scraping here ──────────────────────────────────
def fetch_real_price(sneaker):
    """
    Replace this with actual scraping logic.

    Option A — eBay (easiest, free API):
        Register at developer.ebay.com → get App ID → use Finding API
        endpoint: https://svcs.ebay.com/services/search/FindingService/v1
        params: keywords=sneaker["keywords"], sortOrder=EndTimeSoonest

    Option B — Scrape a public page:
        url = f"https://www.klekt.com/search?q={sneaker['keywords']}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 ..."})
        soup = BeautifulSoup(r.text, "html.parser")
        price_tag = soup.select_one(".price")  # inspect element to find selector
        ...

    Option C — Use Selenium for JS-heavy sites (StockX, GOAT):
        pip install selenium webdriver-manager
        from selenium import webdriver
        driver = webdriver.Chrome()
        driver.get("https://stockx.com/search?s=" + sneaker["keywords"])
        ...
    """
    raise NotImplementedError("Add real scraping logic here")


def fetch_price(sneaker, demo_mode):
    if demo_mode or not HAS_REQUESTS:
        return fetch_demo_price(sneaker)
    try:
        return fetch_real_price(sneaker)
    except Exception as e:
        print(f"  [warn] real fetch failed: {e}, falling back to demo")
        return fetch_demo_price(sneaker)


def main():
    config = load_config()
    history = load_history()
    today = datetime.date.today().isoformat()
    demo_mode = config.get("demo_mode", True)

    print(f"🔍 Tracking {len(config['sneakers'])} sneakers — {today}")
    if demo_mode:
        print("   (demo mode — edit config.json to disable)")

    for sneaker in config["sneakers"]:
        name = sneaker["name"]
        print(f"\n  → {name}")

        result = fetch_price(sneaker, demo_mode)
        price = result["price"]
        print(f"     ¥{price:,.0f}  [{result['source']}]")

        if name not in history:
            history[name] = {"sku": sneaker.get("sku", ""), "records": []}

        # Avoid duplicate entries for same day
        existing_dates = [r["date"] for r in history[name]["records"]]
        if today not in existing_dates:
            history[name]["records"].append({
                "date": today,
                "price": price,
                "source": result["source"],
                "url": result.get("url", "")
            })

        time.sleep(0.5)

    save_history(history)
    print(f"\n✅ Saved to {DATA_FILE}")

    # Print quick summary
    print("\n📊 Current prices:")
    for name, data in history.items():
        if data["records"]:
            latest = data["records"][-1]
            print(f"   {name[:40]:<40} ¥{latest['price']:>8,.0f}")


if __name__ == "__main__":
    main()
