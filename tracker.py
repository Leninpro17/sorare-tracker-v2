import json
import os
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

with open("prices.json", "r") as f:
    prices = json.load(f)

buy = []
sell = []
hold = []

for player, data in prices.items():

    old_price = data["old"]
    new_price = data["new"]

    change = ((new_price - old_price) / old_price) * 100

    if change <= -10:
        buy.append(f"{player} ({change:.1f}%)")

    elif change >= 15:
        sell.append(f"{player} (+{change:.1f}%)")

    else:
        hold.append(player)

report = "📊 SORARE BUY/SELL REPORT\n\n"

report += "🟢 BUY\n"
report += "\n".join(buy) if buy else "Nessuno"
report += "\n\n"

report += "🔴 SELL\n"
report += "\n".join(sell) if sell else "Nessuno"
report += "\n\n"

report += "⚪ HOLD\n"
report += "\n".join(hold) if hold else "Nessuno"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": report
    }
)
