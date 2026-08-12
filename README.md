# Sneaker Price Tracker 球鞋价格追踪器

> Track sneaker resale prices automatically, for free, using GitHub Actions.

**Zero cost. Zero server. Runs every day on its own.**

![dashboard preview](https://img.shields.io/badge/status-auto--tracking-7c6af7)
![GitHub Actions](https://img.shields.io/badge/powered%20by-GitHub%20Actions-2088FF)

---

## How It Works

```
GitHub Actions (free cron)
    ↓  runs every day at 17:00 Beijing time
tracker.py
    ↓  fetches prices
data/prices.json
    ↓  committed back to repo automatically
index.html
    ↓  reads JSON, draws charts
GitHub Pages (free hosting)
```

No cloud bills. No VPS. The repo itself is the database.

---

## Quick Start

**Step 1 — Fork this repo**
```
Click "Fork" → it's now yours
```

**Step 2 — Edit config.json**
```json
{
  "sneakers": [
    {
      "name": "Your sneaker name",
      "sku": "AB1234-567",
      "keywords": "search keywords for scraping",
      "size": "US 10"
    }
  ],
  "demo_mode": true
}
```

**Step 3 — Run manually once**
```
GitHub → Actions tab → "Daily Price Tracker" → Run workflow
```

**Step 4 — Enable GitHub Pages**
```
Settings → Pages → Source: Deploy from branch → Branch: main → / (root)
```

Your dashboard is live at `https://YOUR-USERNAME.github.io/sneaker-price-tracker/`

---

## Add Real Price Data

The tracker runs in `demo_mode: true` by default (generates realistic fake data so the chart looks good immediately).

To track real prices, set `"demo_mode": false` in `config.json` and implement `fetch_real_price()` in `tracker.py`.

**Options explained in the code:**
- **eBay API** (easiest) — free, just need a developer account
- **BeautifulSoup scraping** — works on sites without heavy JS protection
- **Selenium** — for JS-heavy sites like StockX (needs more setup)

The code has detailed comments in the `fetch_real_price()` function explaining exactly how to do each one.

---

## What You Learn Building This

| Concept | Where It Appears |
|---|---|
| HTTP requests | `requests.get()` fetching web pages |
| HTML parsing | `BeautifulSoup` finding price tags |
| JSON as a database | `data/prices.json` storing history |
| CI/CD pipelines | `.github/workflows/track.yml` |
| Data visualization | Chart.js drawing the price chart |
| Git automation | Actions committing data back to repo |

These are the same skills used at every tech company. You are not doing a tutorial — you are building a real system.

---

## Project Structure

```
sneaker-price-tracker/
├── tracker.py              ← main Python script (edit this)
├── config.json             ← your sneaker list (edit this)
├── index.html              ← dashboard (Chart.js)
├── data/
│   └── prices.json         ← auto-generated, do not edit manually
└── .github/
    └── workflows/
        └── track.yml       ← GitHub Actions schedule
```

---

## Extend It

Ideas once the basics work:

- **Price alerts** — send a WeChat/email notification when price drops below a threshold
- **Multi-size tracking** — track multiple sizes, find the cheapest
- **Market comparison** — compare StockX vs GOAT vs Klekt for the same shoe
- **Trend prediction** — use linear regression to predict next week's price (5 lines of Python with NumPy)

---

*Built as a learning project. Real engineering, not a tutorial.*

## Related

- [awesome-algorithm-thinking](https://github.com/daligao/awesome-algorithm-thinking) — Learn algorithmic thinking
- [gaokao-tools](https://github.com/daligao/gaokao-tools) — Study tools
