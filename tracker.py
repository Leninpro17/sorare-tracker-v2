import json
import os
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

with open("trading_scores.json", "r") as f:
    trading = json.load(f)

with open("utility_scores.json", "r") as f:
    utility = json.load(f)

trading_rank = sorted(
    trading.items(),
    key=lambda x: x[1],
    reverse=True
)

utility_rank = sorted(
    utility.items(),
    key=lambda x: x[1],
    reverse=True
)

report = "📊 EUROPE LIMITED REPORT\n\n"

report += "📈 TRADING SCORE\n"

for i, (player, score) in enumerate(trading_rank[:5], start=1):
    report += f"{i}. {player} - {score}\n"

report += "\n"

report += "🏆 UTILITY SCORE\n"

for i, (player, score) in enumerate(utility_rank[:5], start=1):
    report += f"{i}. {player} - {score}\n"

report += "\n"

report += "🚨 BUY TARGETS\n"

for player, score in trading_rank[:3]:
    report += f"• {player}\n"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

response = requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": report
    }
)

print(response.status_code)
print(response.text)
