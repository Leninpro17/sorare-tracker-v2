import json
import os
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

with open("trading_scores.json", "r") as f:
    trading = json.load(f)

with open("utility_scores.json", "r") as f:
    utility = json.load(f)

report = "📊 EUROPE LIMITED REPORT\n\n"

# Ranking Trading
trading_rank = sorted(
    trading.items(),
    key=lambda x: x[1],
    reverse=True
)

report += "📈 TRADING SCORE\n"

for i, (player, score) in enumerate(trading_rank[:5], start=1):
    report += f"{i}. {player} - {score}\n"

report += "\n"

# Ranking Utility
utility_rank = sorted(
    utility.items(),
    key=lambda x: x[1],
    reverse=True
)

report += "🏆 UTILITY SCORE\n"

for i, (player, score) in enumerate(utility_rank[:5], start=1):
    report += f"{i}. {player} - {score}\n"

report += "\n"

# Strong Buy
strong_buy = []

for player in trading:

    trading_score = trading.get(player, 0)
    utility_score = utility.get(player, 0)

    if trading_score >= 85 and utility_score >= 75:
        strong_buy.append(
            (player, trading_score, utility_score)
        )

report += "🔥 STRONG BUY\n"

if strong_buy:
    for player, t, u in strong_buy:
        report += f"• {player} (T:{t} U:{u})\n"
else:
    report += "Nessuno\n"

report += "\n"

# Watchlist
watchlist = []

for player in trading:

    trading_score = trading.get(player, 0)
    utility_score = utility.get(player, 0)

    if (
        trading_score >= 75
        and utility_score >= 60
        and trading_score < 85
    ):
        watchlist.append(player)

report += "⚠️ WATCHLIST\n"

if watchlist:
    for player in watchlist:
        report += f"• {player}\n"
else:
    report += "Nessuno\n"

report += "\n"

# Sell Candidates
sell_candidates = []

for player in trading:

    trading_score = trading.get(player, 0)
    utility_score = utility.get(player, 0)

    if trading_score < 70 and utility_score >= 80:
        sell_candidates.append(player)

report += "🔴 SELL CANDIDATES\n"

if sell_candidates:
    for player in sell_candidates:
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
