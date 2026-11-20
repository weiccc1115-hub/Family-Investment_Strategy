import json
import os
from datetime import datetime, timedelta, timezone
import yfinance as yf

OUTPUT_FILE = "prices.json"

TICKERS = {
    "0050": ("0050.TW", "TWD"),
    "0056": ("0056.TW", "TWD"),
    "2330": ("2330.TW", "TWD"),
    "VOO": ("VOO", "USD"),
    "QQQ": ("QQQ", "USD"),
}


def fetch_latest_close(symbol: str):
    try:
        hist = yf.Ticker(symbol).history(period="5d")
        if hist is None or hist.empty or "Close" not in hist.columns:
            return None
        valid_closes = hist["Close"].dropna()
        if valid_closes.empty:
            return None
        value = float(valid_closes.iloc[-1])
        return value if value > 0 else None
    except Exception as exc:
        print(f"[WARN] Failed to fetch {symbol}: {exc}")
        return None


def load_existing_data():
    if not os.path.exists(OUTPUT_FILE):
        return {"usdTwd": 32.5, "prices": {}, "usdPrices": {}}
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"usdTwd": 32.5, "prices": {}, "usdPrices": {}}


def main():
    existing = load_existing_data()
    prices = existing.get("prices", {})
    usd_prices = existing.get("usdPrices", {})

    fx_rate = fetch_latest_close("TWD=X")
    if fx_rate is None:
        fx_rate = float(existing.get("usdTwd", 32.5))
    else:
        fx_rate = round(fx_rate, 2)

    for asset_id, (symbol, currency) in TICKERS.items():
        close_price = fetch_latest_close(symbol)
        if close_price is None:
            print(f"[WARN] Keeping previous price for {asset_id}")
            continue

        if currency == "USD":
            usd_prices[asset_id] = round(close_price, 2)
            prices[asset_id] = round(close_price * fx_rate, 2)
        else:
            prices[asset_id] = round(close_price, 2)

    tz_tw = timezone(timedelta(hours=8))
    now_tw = datetime.now(tz_tw)

    payload = {
        "updatedAt": now_tw.strftime("%Y-%m-%d %H:%M"),
        "usdTwd": fx_rate,
        "prices": prices,
        "usdPrices": usd_prices,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] Updated {OUTPUT_FILE}: {json.dumps(payload, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
