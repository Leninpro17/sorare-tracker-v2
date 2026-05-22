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
    position = data["position"]
    l15 = data["l15"]
    l40 = data["l40"]

    # -------------------
    # TRADING SCORE
    # -------------------

    trading = 0

    if u23:
        trading += 30

    if age <= 21:
        trading += 20
    elif age <= 24:
        trading += 10

    if starter:
        trading += 20

    if position == "GK":
        trading += 15

    if price <= 5:
        trading += 30
    elif price <= 10:
        trading += 20
    elif price <= 15:
        trading += 10

    # -------------------
    # UTILITY SCORE
    # -------------------

    utility = 0

    if starter:
        utility += 50

    utility += int(l15 / 2)

    utility += int((l40 - 40) / 2)

    if position == "GK":
        utility += 15

    results.append({
        "player": player,
        "position": position,
        "trading": trading,
        "utility": utility,
        "price": price,
        "l15": l15
    })

# Ranking

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

gk_rank = sorted(
    [p for p in results if p["position"] == "GK"],
    key=lambda x: x["utility"],
    reverse=True
)

# Report

report = "📊 EUROPE LIMITED REPORT\n\n"

# Trading

report += "📈 TRADING SCORE\n"

for p in trading_rank[:5]:
    report += f"• {p['player']} ({p['trading']})\n"

report += "\n"

# Utility

report += "🏆 UTILITY SCORE\n"

for p in utility_rank[:5]:
    report += f"• {p['player']} ({p['utility']})\n"

report += "\n"

# GK

report += "🥅 TOP GK\n"

for p in gk_rank[:3]:
    report += f"• {p['player']} (U:{p['utility']})\n"

report += "\n"

# Strong Buy

report += "🔥 STRONG BUY\n"

strong_buy = []

for p in results:
    if p["trading"] >= 60 and p["utility"] >= 80:
        strong_buy.append(p)

if strong_buy:
    for p in strong_buy:
        report += (
            f"• {p['player']} "
            f"(T:{p['trading']} U:{p['utility']})\n"
        )
else:
    report += "Nessuno\n"

report += "\n"

# Watchlist

report += "⚠️ WATCHLIST\n"

watchlist = []

for p in results:
    if 45 <= p["trading"] < 60:
        watchlist.append(p)

if watchlist:
    for p in watchlist:
        report += f"• {p['player']}\n"
else:
    report += "Nessuno\n"

report += "\n"

# Sell Candidates

report += "🔴 SELL CANDIDATES\n"

sell = []

for p in results:
    if p["trading"] < 40 and p["utility"] >= 80:
        sell.append(p)

if sell:
    for p in sell:
        report += f"• {p['player']}\n"
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
