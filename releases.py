#!/usr/bin/env python3
"""
New Release Tracker — JJ专属版
Fetches upcoming sneaker releases from:
  1. Sneaker Database API (global, free, no auth)
  2. 得物 latest arrivals per brand keyword
Saves to data/releases.json
"""

import json
import datetime
import os
import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

RELEASES_FILE = "data/releases.json"
CONFIG_FILE = "config.json"

SNEAKER_DB_API = "https://api.thesneakerdatabase.com/v1/sneakers"
DEWU_SEARCH_API = "https://app.dewu.com/api/v1/h5/search/product/list"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://m.dewu.com/",
    "Origin": "https://m.dewu.com",
}

BRANDS = [
    "Nike", "Jordan", "Adidas", "New Balance",
    "ASICS", "Puma", "Converse", "Vans", "Reebok",
]


# ── Sneaker Database: upcoming 60 days ────────────────────────────────────────
def fetch_sneakerdb_releases():
    today = datetime.date.today()
    sixty_days = today + datetime.timedelta(days=60)
    results = []

    for brand in BRANDS:
        try:
            params = {
                "limit": 10,
                "brand": brand,
                "releaseDate": f"gte:{today.isoformat()}",
            }
            r = requests.get(SNEAKER_DB_API, params=params, timeout=12)
            r.raise_for_status()
            data = r.json()
            items = data.get("results", [])

            for s in items:
                release_str = s.get("releaseDate", "")
                try:
                    rd = datetime.date.fromisoformat(release_str[:10])
                    if rd > sixty_days:
                        continue
                except (ValueError, TypeError):
                    pass  # keep if date unparseable

                retail_usd = s.get("retailPrice", 0) or 0
                results.append({
                    "id": s.get("id", ""),
                    "name": s.get("title") or s.get("name", ""),
                    "brand": s.get("brand", brand),
                    "sku": s.get("sku", ""),
                    "colorway": s.get("colorway", ""),
                    "releaseDate": release_str[:10] if release_str else "",
                    "retailPrice": retail_usd,
                    "retailPriceCNY": round(retail_usd * 7.1) if retail_usd else 0,
                    "imageUrl": s.get("media", {}).get("imageUrl", "") or s.get("thumbnail", ""),
                    "thumbUrl": s.get("media", {}).get("thumbUrl", "") or s.get("thumbnail", ""),
                    "source": "sneakerdb",
                    "url": s.get("links", {}).get("stockX", "") or "",
                })

            print(f"  [SneakerDB] {brand}: {len(items)} 款")
            time.sleep(0.5)
        except Exception as e:
            print(f"  [SneakerDB] {brand} 失败: {e}")

    return results


# ── 得物: newest arrivals per brand ───────────────────────────────────────────
def fetch_dewu_new_arrivals():
    results = []
    seen_ids = set()

    for brand in BRANDS[:6]:  # top brands only to stay under rate limit
        try:
            params = {
                "page": 1,
                "limit": 6,
                "keyword": brand,
                "sort": 4,      # 最新上架
                "is_new": 1,
            }
            r = requests.get(DEWU_SEARCH_API, params=params, headers=HEADERS, timeout=12)
            r.raise_for_status()
            data = r.json()

            products = (
                data.get("data", {}).get("productList")
                or data.get("data", {}).get("list")
                or []
            )

            for p in products:
                pid = str(p.get("productId") or p.get("id") or "")
                if not pid or pid in seen_ids:
                    continue
                seen_ids.add(pid)

                price_raw = (
                    p.get("lowestPrice") or p.get("price")
                    or p.get("salePrice") or p.get("lowest_price")
                )
                price = 0
                if price_raw:
                    price = float(str(price_raw).replace(",", ""))
                    if price > 100000:
                        price = price / 100

                results.append({
                    "id": f"dewu_{pid}",
                    "name": p.get("title") or p.get("name", ""),
                    "brand": brand,
                    "sku": p.get("articleNumber") or p.get("sku") or "",
                    "colorway": "",
                    "releaseDate": "",
                    "retailPrice": 0,
                    "retailPriceCNY": int(price) if price else 0,
                    "imageUrl": p.get("img") or p.get("picUrl") or p.get("image") or "",
                    "thumbUrl": p.get("img") or p.get("picUrl") or p.get("image") or "",
                    "source": "dewu",
                    "url": f"https://m.dewu.com/product/{pid}",
                })

            print(f"  [得物新品] {brand}: {len(products)} 款")
            time.sleep(1)
        except Exception as e:
            print(f"  [得物新品] {brand} 失败: {e}")

    return results


# ── Demo fallback ─────────────────────────────────────────────────────────────
DEMO_RELEASES = [
    {
        "id": "demo_1",
        "name": "Nike Air Max 95 OG Neon",
        "brand": "Nike", "sku": "AT2865-001", "colorway": "Neon Yellow/Black",
        "releaseDate": (datetime.date.today() + datetime.timedelta(days=7)).isoformat(),
        "retailPrice": 180, "retailPriceCNY": 1279,
        "imageUrl": "https://images.stockx.com/images/Nike-Air-Max-95-OG-Neon-Yellow-2020-Product.jpg",
        "thumbUrl": "https://images.stockx.com/images/Nike-Air-Max-95-OG-Neon-Yellow-2020-Product.jpg",
        "source": "demo", "url": "#",
    },
    {
        "id": "demo_2",
        "name": "Adidas Samba OG \"Cream\"",
        "brand": "Adidas", "sku": "IG6170", "colorway": "Cream White/Gold",
        "releaseDate": (datetime.date.today() + datetime.timedelta(days=14)).isoformat(),
        "retailPrice": 100, "retailPriceCNY": 710,
        "imageUrl": "https://images.stockx.com/images/adidas-Samba-OG-Cream-White-Gold-Metallic-2023-Product.jpg",
        "thumbUrl": "https://images.stockx.com/images/adidas-Samba-OG-Cream-White-Gold-Metallic-2023-Product.jpg",
        "source": "demo", "url": "#",
    },
    {
        "id": "demo_3",
        "name": "New Balance 1906R Protection Pack",
        "brand": "New Balance", "sku": "M1906RD", "colorway": "Rain Cloud",
        "releaseDate": (datetime.date.today() + datetime.timedelta(days=21)).isoformat(),
        "retailPrice": 150, "retailPriceCNY": 1065,
        "imageUrl": "https://images.stockx.com/images/New-Balance-1906R-Protection-Pack-Rain-Cloud-Product.jpg",
        "thumbUrl": "https://images.stockx.com/images/New-Balance-1906R-Protection-Pack-Rain-Cloud-Product.jpg",
        "source": "demo", "url": "#",
    },
    {
        "id": "demo_4",
        "name": "Jordan 4 Retro Military Blue 2024",
        "brand": "Jordan", "sku": "FV5029-141", "colorway": "White/Military Blue",
        "releaseDate": (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
        "retailPrice": 210, "retailPriceCNY": 1491,
        "imageUrl": "https://images.stockx.com/images/Air-Jordan-4-Retro-Military-Blue-2024-Product.jpg",
        "thumbUrl": "https://images.stockx.com/images/Air-Jordan-4-Retro-Military-Blue-2024-Product.jpg",
        "source": "demo", "url": "#",
    },
    {
        "id": "demo_5",
        "name": "ASICS Gel-Kayano 14 \"Cream\"",
        "brand": "ASICS", "sku": "1201A019-108", "colorway": "Cream/Puce",
        "releaseDate": (datetime.date.today() + datetime.timedelta(days=45)).isoformat(),
        "retailPrice": 120, "retailPriceCNY": 852,
        "imageUrl": "https://images.stockx.com/images/Asics-Gel-Kayano-14-Cream-Puce-Product.jpg",
        "thumbUrl": "https://images.stockx.com/images/Asics-Gel-Kayano-14-Cream-Puce-Product.jpg",
        "source": "demo", "url": "#",
    },
]


# ── Deduplicate by id ─────────────────────────────────────────────────────────
def deduplicate(items):
    seen = {}
    for item in items:
        key = item["id"] or item["name"]
        if key not in seen:
            seen[key] = item
    return list(seen.values())


# ── Sort: by releaseDate, empty dates last ────────────────────────────────────
def sort_releases(items):
    def key(r):
        d = r.get("releaseDate", "")
        return d if d else "9999-99-99"
    return sorted(items, key=key)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    config = {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        pass

    demo_mode = config.get("demo_mode", True)
    today = datetime.date.today().isoformat()

    print(f"👟 JJ新品发布追踪器 — {today}")
    print(f"   {'demo模式' if demo_mode else '实时抓取'}")
    print()

    if demo_mode or not HAS_REQUESTS:
        releases = DEMO_RELEASES
        print("  使用内置 demo 数据（5 款即将发售）")
    else:
        all_items = []
        print("— Sneaker Database (全球发售预告) —")
        all_items.extend(fetch_sneakerdb_releases())
        print()
        print("— 得物新品 —")
        all_items.extend(fetch_dewu_new_arrivals())

        releases = sort_releases(deduplicate(all_items))
        if not releases:
            print("  实时抓取结果为空，使用 demo 数据")
            releases = DEMO_RELEASES

    os.makedirs("data", exist_ok=True)
    with open(RELEASES_FILE, "w", encoding="utf-8") as f:
        json.dump({"updated": today, "releases": releases}, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 保存 {len(releases)} 款到 {RELEASES_FILE}")
    print("\n即将发售:")
    for r in releases[:8]:
        date_str = r.get("releaseDate") or "日期待定"
        print(f"  {r['brand']:<12} {r['name'][:40]:<40} {date_str}  [{r['source']}]")


if __name__ == "__main__":
    main()
