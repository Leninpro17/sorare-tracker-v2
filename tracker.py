import json
import os
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

with open("watchlist.json", "r") as f:
    data = json.load(f)

players = data["players"]

report = "📊 SORARE BUY/SELL REPORT\n\n"

for player in players:
    report += f"⚪ HOLD - {player}\n"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": report
    }
)
