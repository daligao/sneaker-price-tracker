#!/usr/bin/env python3
"""
Sneaker Price Tracker — JJ专属版
Runs daily via GitHub Actions, saves price history to data/prices.json
"""

import json
import random
import datetime
import os
import re
import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


DATA_FILE = "data/prices.json"
CONFIG_FILE = "config.json"

# Dewu H5 API — same endpoint the mobile app uses
DEWU_SEARCH_API = "https://app.dewu.com/api/v1/h5/search/product/list"
DEWU_PRODUCT_URL = "https://m.dewu.com/product/{product_id}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://m.dewu.com/",
    "Origin": "https://m.dewu.com",
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


# ── Demo mode ─────────────────────────────────────────────────────────────────
def fetch_demo_price(sneaker):
    base = sneaker.get("retailPriceCNY", 0) * 1.5 or 1800
    day = datetime.date.today().timetuple().tm_yday
    trend = base * 0.001 * (day % 30 - 15)
    noise = random.uniform(-0.03, 0.03) * base
    return {"price": int(round(base + trend + noise)), "source": "demo", "url": "#", "product_id": ""}


# ── 得物 H5 API ───────────────────────────────────────────────────────────────
def fetch_dewu_price(sneaker):
    """
    Calls 得物's internal H5 search API (same one used by m.dewu.com).
    Returns lowest ask price and direct product link.

    sort values: 0=综合  1=价格升序  2=价格降序  4=最新上架
    """
    keywords = sneaker.get("keywords") or sneaker.get("name", "")

    params = {
        "page": 1,
        "limit": 5,
        "keyword": keywords,
        "sort": 1,          # price ascending → get lowest ask
        "is_new": 1,        # brand new condition
    }

    r = requests.get(DEWU_SEARCH_API, params=params, headers=HEADERS, timeout=12)
    r.raise_for_status()
    data = r.json()

    # Response structure: {"code":200, "data":{"productList":[{...}]}}
    products = (
        data.get("data", {}).get("productList")
        or data.get("data", {}).get("list")
        or []
    )

    if not products:
        raise ValueError("empty product list from dewu API")

    # Pick first result (lowest price due to sort=1)
    first = products[0]

    # Price field varies by API version
    price_raw = (
        first.get("lowestPrice")
        or first.get("price")
        or first.get("salePrice")
        or first.get("lowest_price")
    )
    if price_raw is None:
        raise ValueError(f"no price field in: {list(first.keys())}")

    # Price may be in fen (cents) or yuan
    price = float(str(price_raw).replace(",", ""))
    if price > 100000:   # likely in fen
        price = price / 100

    product_id = str(first.get("productId") or first.get("id") or "")
    url = DEWU_PRODUCT_URL.format(product_id=product_id) if product_id else "https://m.dewu.com"

    return {"price": int(round(price)), "source": "dewu", "url": url, "product_id": product_id}


# ── Main fetch with fallback ───────────────────────────────────────────────────
def fetch_price(sneaker, demo_mode):
    if demo_mode or not HAS_REQUESTS:
        return fetch_demo_price(sneaker)

    try:
        result = fetch_dewu_price(sneaker)
        print(f"     [得物] ¥{result['price']:,}  {result['url']}")
        return result
    except Exception as e:
        print(f"     [得物] 失败: {e} → 使用demo价格")
        return fetch_demo_price(sneaker)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    config = load_config()
    history = load_history()
    today = datetime.date.today().isoformat()
    demo_mode = config.get("demo_mode", True)

    print(f"👟 JJ球鞋价格追踪器 — {today}")
    print(f"   追踪 {len(config['sneakers'])} 款  {'demo模式' if demo_mode else '得物实时'}")
    print()

    for sneaker in config["sneakers"]:
        name = sneaker["name"]
        print(f"  → {name[:55]}")

        result = fetch_price(sneaker, demo_mode)

        if name not in history:
            history[name] = {"sku": sneaker.get("sku", ""), "records": []}

        existing = [r["date"] for r in history[name]["records"]]
        if today not in existing:
            history[name]["records"].append({
                "date": today,
                "price": result["price"],
                "source": result["source"],
                "url": result.get("url", ""),
            })

        time.sleep(1)

    save_history(history)
    print(f"\n✅ 保存到 {DATA_FILE}")
    print("\n当前价格:")
    for name, data in history.items():
        if data["records"]:
            r = data["records"][-1]
            print(f"  {name[:40]:<40} ¥{r['price']:>8,}  [{r['source']}]")


if __name__ == "__main__":
    main()
