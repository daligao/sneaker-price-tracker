#!/usr/bin/env python3
"""
Sneaker Price Tracker — JJ专属版
Runs daily via GitHub Actions, saves price history to data/prices.json

Sources (in order of preference):
  1. 得物 (dewu.com) — China's primary sneaker resale market
  2. 闲鱼 (xianyu) — secondhand market, real transaction prices
  3. Demo mode — realistic mock prices for testing
"""

import json
import random
import datetime
import os
import re
import time

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


DATA_FILE = "data/prices.json"
CONFIG_FILE = "config.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


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


# ── Demo mode ────────────────────────────────────────────────────────────────
BASE_PRICES = {
    "Nike Air Jordan 1 Retro High OG": 2800,
    "New Balance 990v6 Made in USA": 1800,
    "Adidas Samba OG": 1200,
}

def fetch_demo_price(sneaker):
    base = BASE_PRICES.get(sneaker["name"], sneaker.get("retailPriceCNY", 1500) * 1.4 or 1500)
    day = datetime.date.today().timetuple().tm_yday
    trend = base * 0.001 * (day % 30 - 15)
    noise = random.uniform(-0.03, 0.03) * base
    return {"price": round(base + trend + noise), "source": "demo", "url": "#"}


# ── 得物 (Dewu) ───────────────────────────────────────────────────────────────
def fetch_dewu_price(sneaker):
    """
    Searches dewu.com (得物) for lowest ask price.
    Dewu has anti-bot measures; this works in demo GitHub Actions environment
    but may need a rotating proxy for heavy usage.

    To improve: add your own proxy in the requests.get() call:
        proxies={"https": "http://YOUR_PROXY:PORT"}
    """
    if not HAS_REQUESTS:
        raise RuntimeError("requests not installed")

    keywords = sneaker.get("keywords") or sneaker.get("name", "")
    url = f"https://www.dewu.com/search?keyword={requests.utils.quote(keywords)}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # Dewu renders prices in JSON within a script tag
        scripts = soup.find_all("script")
        for script in scripts:
            text = script.string or ""
            if "lowestPrice" in text or "lowest_price" in text:
                # Try to extract price
                match = re.search(r'"lowestPrice"\s*:\s*"?(\d+\.?\d*)"?', text)
                if not match:
                    match = re.search(r'"lowest_price"\s*:\s*"?(\d+\.?\d*)"?', text)
                if match:
                    price = float(match.group(1))
                    return {"price": round(price), "source": "dewu", "url": url}

        # Fallback: look for price in visible elements
        price_el = soup.select_one(".price, .product-price, [class*=price]")
        if price_el:
            text = re.sub(r"[^\d.]", "", price_el.get_text())
            if text:
                return {"price": round(float(text)), "source": "dewu", "url": url}

        raise ValueError("price not found in page")

    except Exception as e:
        raise RuntimeError(f"dewu fetch failed: {e}")


# ── 闲鱼 (Xianyu / Idle Fish) ─────────────────────────────────────────────────
def fetch_xianyu_price(sneaker):
    """
    Searches xianyu.taobao.com for average sold price.
    Xianyu is Taobao's secondhand platform — real transaction prices.

    Note: Xianyu requires login for full data. This approach uses the
    public search page which shows listing prices without login.
    For actual sold prices, you need Selenium + logged-in session.

    How to add Selenium support:
        pip install selenium webdriver-manager
        from selenium.webdriver import Chrome
        from selenium.webdriver.chrome.options import Options
        opts = Options(); opts.add_argument("--headless"); opts.add_argument("--no-sandbox")
        driver = Chrome(options=opts)
        driver.get("https://www.xianyu.com/...")
        # Login with cookies saved from your browser session
    """
    if not HAS_REQUESTS:
        raise RuntimeError("requests not installed")

    keywords = sneaker.get("keywords") or sneaker.get("name", "")
    url = f"https://www.xianyu.com/search-result?q={requests.utils.quote(keywords)}&sortValue=price_asc"

    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    # Xianyu embeds data in JSON inside script tags
    for script in soup.find_all("script"):
        text = script.string or ""
        prices = re.findall(r'"price"\s*:\s*"?(\d+\.?\d*)"?', text)
        if prices:
            nums = sorted([float(p) for p in prices if 100 < float(p) < 50000])
            if nums:
                # Use the median to avoid outliers
                mid = nums[len(nums) // 2]
                return {"price": round(mid), "source": "xianyu", "url": url}

    raise RuntimeError("xianyu: price not found")


# ── Main fetch with fallback chain ────────────────────────────────────────────
def fetch_price(sneaker, demo_mode):
    if demo_mode or not HAS_REQUESTS:
        return fetch_demo_price(sneaker)

    for fetcher, name in [(fetch_dewu_price, "dewu"), (fetch_xianyu_price, "xianyu")]:
        try:
            result = fetcher(sneaker)
            print(f"     [{name}] ¥{result['price']:,}")
            return result
        except Exception as e:
            print(f"     [{name}] failed: {e}")

    print("     [demo] fallback")
    return fetch_demo_price(sneaker)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    config = load_config()
    history = load_history()
    today = datetime.date.today().isoformat()
    demo_mode = config.get("demo_mode", True)

    print(f"👟 JJ球鞋价格追踪器 — {today}")
    print(f"   追踪 {len(config['sneakers'])} 款球鞋 {'(demo模式)' if demo_mode else '(实时抓取)'}")
    print()

    for sneaker in config["sneakers"]:
        name = sneaker["name"]
        print(f"  → {name[:50]}")

        result = fetch_price(sneaker, demo_mode)
        price = result["price"]

        if name not in history:
            history[name] = {
                "sku": sneaker.get("sku", ""),
                "brand": sneaker.get("brand", ""),
                "colorway": sneaker.get("colorway", ""),
                "records": []
            }

        existing = [r["date"] for r in history[name]["records"]]
        if today not in existing:
            history[name]["records"].append({
                "date": today,
                "price": price,
                "source": result["source"],
                "url": result.get("url", "")
            })

        time.sleep(0.8)

    save_history(history)
    print(f"\n✅ 保存到 {DATA_FILE}")
    print("\n当前价格:")
    for name, data in history.items():
        if data["records"]:
            r = data["records"][-1]
            print(f"  {name[:40]:<40} ¥{r['price']:>8,}  [{r['source']}]")


if __name__ == "__main__":
    main()
