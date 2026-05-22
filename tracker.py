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

    # -------------------
    # VALUE SCORE
    # -------------------

    value = 0

    value += int(utility * 0.4)

    if price <= 5:
        value += 40
    elif price <= 10:
        value += 35
    elif price <= 15:
        value += 25
    elif price <= 20:
        value += 15
    else:
        value += 5

    if u23:
        value += 25

    if position == "GK":
        value += 15

    if age >= 30:
        value -= 15

    results.append({
        "player": player,
        "position": position,
        "trading": trading,
        "utility": utility,
        "value": value,
        "price": price,
        "l15": l15,
        "owned": data["owned"]
    })

# -------------------
# RANKINGS
# -------------------

value_rank = sorted(
    results,
    key=lambda x: x["value"],
    reverse=True
)

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

# -------------------
# PORTFOLIO LOGIC
# -------------------

owned_cards = []
buy_targets = []
switch_targets = []

for p in results:

    if p["owned"]:
        owned_cards.append(p)

    if (not p["owned"]) and p["value"] >= 75:
        buy_targets.append(p)

    if p["owned"] and p["value"] < 50:
        switch_targets.append(p)

# -------------------
# REPORT
# -------------------

report = "📊 EUROPE LIMITED REPORT\n\n"

# PORTFOLIO

report += "💼 MY PORTFOLIO\n"

if owned_cards:
    for p in owned_cards:
        report += f"• {p['player']}\n"
else:
    report += "Nessuna carta posseduta configurata\n"

report += "\n"

# BUY TARGETS

report += "🛒 BUY TARGETS\n"

for p in sorted(
    buy_targets,
    key=lambda x: x["value"],
    reverse=True
)[:5]:
    report += (
        f"• {p['player']} "
        f"(V:{p['value']})\n"
    )

report += "\n"

# SWITCH

report += "🔄 SWITCH CANDIDATES\n"

if switch_targets:
    for p in switch_targets:
        report += f"• {p['player']}\n"
else:
    report += "Nessuno\n"

report += "\n"

# VALUE

report += "💎 VALUE SCORE\n"

for p in value_rank[:5]:
    report += (
        f"• {p['player']} "
        f"(V:{p['value']} €{p['price']})\n"
    )

report += "\n"

# BEST BUYS

report += "🛒 BEST BUYS TODAY\n"

for p in value_rank[:3]:
    report += f"• {p['player']}\n"

report += "\n"

# TRADING

report += "📈 TRADING SCORE\n"

for p in trading_rank[:5]:
    report += f"• {p['player']} ({p['trading']})\n"

report += "\n"

# UTILITY

report += "🏆 UTILITY SCORE\n"

for p in utility_rank[:5]:
    report += f"• {p['player']} ({p['utility']})\n"

report += "\n"

# GK

report += "🥅 TOP GK\n"

for p in gk_rank[:3]:
    report += f"• {p['player']} (U:{p['utility']})\n"

report += "\n"

# STRONG BUY

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

# WATCHLIST

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

# SELL CANDIDATES

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

# -------------------
# TELEGRAM
# -------------------

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
