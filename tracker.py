import json
import os
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

with open("player_data.json", "r") as f:
    players = json.load(f)

results = []

for player, data in players.items():

    age = data["age"]
    u23 = data["u23"]
    starter = data["starter"]
    price = data["price"]

    # TRADING SCORE
    trading = 0

    if u23:
        trading += 30

    if age <= 21:
        trading += 20

    if starter:
        trading += 20

    if price <= 5:
        trading += 30
    elif price <= 10:
        trading += 20
    elif price <= 20:
        trading += 10

    # UTILITY SCORE
    utility = 0

    if starter:
        utility += 50

    if u23:
        utility += 15

    if price <= 10:
        utility += 15
    elif price <= 20:
        utility += 10

    if age <= 25:
        utility += 10

    results.append({
        "player": player,
        "trading": trading,
        "utility": utility
    })

trading_rank = sorted(
    results,
    key=lambda x: x["trading"],
    reverse=True
)

utility_rank = sorted(
    results,
    key=lambda x: x["utility"],
    reverse=True
)

report = "📊 EUROPE LIMITED REPORT\n\n"

report += "📈 TRADING SCORE\n"

for p in trading_rank[:5]:
    report += f"• {p['player']} ({p['trading']})\n"

report += "\n🏆 UTILITY SCORE\n"

for p in utility_rank[:5]:
    report += f"• {p['player']} ({p['utility']})\n"

report += "\n🔥 STRONG BUY\n"

strong_buy = []

for p in results:
    if p["trading"] >= 60 and p["utility"] >= 70:
        strong_buy.append(p["player"])

if strong_buy:
    for player in strong_buy:
        report += f"• {player}\n"
else:
    report += "Nessuno\n"

report += "\n⚠️ WATCHLIST\n"

watchlist = []

for p in results:
    if p["trading"] >= 40 and p["trading"] < 60:
        watchlist.append(p["player"])

if watchlist:
    for player in watchlist:
        report += f"• {player}\n"
else:
    report += "Nessuno\n"

report += "\n🔴 SELL CANDIDATES\n"

sell = []

for p in results:
    if p["trading"] < 30 and p["utility"] >= 60:
        sell.append(p["player"])

if sell:
    for player in sell:
        report += f"• {player}\n"
else:
    report += "Nessuno\n"

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
