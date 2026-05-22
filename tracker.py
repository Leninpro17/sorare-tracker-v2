import json
import os
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

with open("scores.json", "r") as f:
    scores = json.load(f)

ranking = sorted(
    scores.items(),
    key=lambda x: x[1],
    reverse=True
)

report = "📊 EUROPE LIMITED REPORT\n\n"

for i, (player, score) in enumerate(ranking[:10], start=1):
    report += f"{i}. {player} — BUY SCORE {score}\n"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": report
    }
)
