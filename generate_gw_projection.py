import os
import json
import argparse
from datetime import datetime
from config import LEAGUES


def safe_number(value, default=0):
    if value is None:
        return default

    try:
        return float(value)
    except Exception:
        return default


def clean_scores(scores):
    if not scores:
        return []

    return [
        float(score)
        for score in scores
        if score is not None
    ]


def average(values):
    if not values:
        return None

    return sum(values) / len(values)


def top_average(values, count=3):
    if not values:
        return None

    sorted_values = sorted(values, reverse=True)
    top_values = sorted_values[:count]

    return average(top_values)


def calculate_consistency(scores):
    """
    Consistency alta = punteggi vicini tra loro.
    Scala semplice 0-100.
    """
    if len(scores) < 3:
        return 40

    avg = average(scores)

    if avg is None or avg <= 0:
        return 30

    variance = sum((x - avg) ** 2 for x in scores) / len(scores)
    std_dev = variance ** 0.5

    volatility_ratio = std_dev / avg

    consistency = 100 - (volatility_ratio * 100)

    return max(0, min(100, round(consistency, 1)))


def calculate_spike_rating(scores, decisive, position):
    """
    Spike rating = possibilità di fare punteggio alto.
    Attaccanti e centrocampisti decisivi ricevono leggero bonus.
    """
    if not scores:
        return 30

    max_score = max(scores)
    top3 = top_average(scores, 3) or 0
    decisive = safe_number(decisive)

    score = 0

    score += min(max_score, 100) * 0.45
    score += min(top3, 100) * 0.35
    score += min(decisive, 60) * 0.20

    if position == "Forward":
        score += 5
    elif position == "Midfielder":
        score += 3
    elif position == "Goalkeeper":
        score += 2

    return max(0, min(100, round(score, 1)))


def calculate_risk_level(starter_rate, minutes_last10, consistency):
    starter_rate = safe_number(starter_rate)
    minutes_last10 = safe_number(minutes_last10)
    consistency = safe_number(consistency)

    if starter_rate >= 80 and minutes_last10 >= 700 and consistency >= 60:
        return "LOW"

    if starter_rate >= 50 and minutes_last10 >= 400:
        return "MEDIUM"

    return "HIGH"


def calculate_floor_projected(l10, l40, aa, starter_rate, minutes_last10):
    """
    Floor = stima prudente.
    Favorisce AA, titolarità e minuti.
    """
    l10 = safe_number(l10)
    l40 = safe_number(l40)
    aa = safe_number(aa)
    starter_rate = safe_number(starter_rate)
    minutes_last10 = safe_number(minutes_last10)

    base = (
        l10 * 0.40
        + l40 * 0.30
        + aa * 0.20
        + 10 * 0.10
    )

    if starter_rate < 50:
        base *= 0.75
    elif starter_rate < 70:
        base *= 0.90

    if minutes_last10 < 300:
        base *= 0.75
    elif minutes_last10 < 600:
        base *= 0.90

    return round(base, 1)


def calculate_base_projected(l5, l10, l40, aa, starter_rate, minutes_last10):
    """
    Base projection = stima centrale.
    """
    l5 = safe_number(l5)
    l10 = safe_number(l10)
    l40 = safe_number(l40)
    aa = safe_number(aa)
    starter_rate = safe_number(starter_rate)
    minutes_last10 = safe_number(minutes_last10)

    projected = (
        l10 * 0.45
        + l5 * 0.25
        + l40 * 0.20
        + aa * 0.10
    )

    if starter_rate >= 90:
        projected *= 1.05
    elif starter_rate < 50:
        projected *= 0.80
    elif starter_rate < 70:
        projected *= 0.92

    if minutes_last10 >= 800:
        projected *= 1.03
    elif minutes_last10 < 300:
        projected *= 0.75
    elif minutes_last10 < 600:
        projected *= 0.90

    return round(projected, 1)


def calculate_ceiling_projected(scores, base_projected, spike_rating):
    """
    Ceiling = scenario alto.
    Usa max e top3 lastScores.
    """
    if not scores:
        return round(base_projected * 1.20, 1)

    max_score = max(scores)
    top3 = top_average(scores, 3) or max_score

    ceiling = (
        max_score * 0.45
        + top3 * 0.35
        + base_projected * 0.20
    )

    if spike_rating >= 75:
        ceiling *= 1.08
    elif spike_rating >= 60:
        ceiling *= 1.04

    return round(ceiling, 1)


def get_floor_value(price):
    if not price:
        return None

    floor = price.get("limitedFloor", {})

    if floor.get("eur") is not None:
        return floor.get("eur")

    if floor.get("usd") is not None:
        return floor.get("usd")

    if floor.get("eth") is not None:
        return floor.get("eth")

    return None


def build_price_index(prices):
    index = {}

    for player in prices:
        slug = player.get("slug")
        if slug:
            index[slug] = player

    return index


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--league",
        required=True,
        choices=LEAGUES.keys()
    )

    parser.add_argument(
        "--season",
        required=True,
        type=int
    )

    args = parser.parse_args()

    league_key = args.league
    season = args.season

    base_dir = f"data/{league_key}/{season}"

    metrics_file = f"{base_dir}/player_metrics_latest.json"
    prices_file = f"{base_dir}/player_prices_latest.json"
    output_file = f"{base_dir}/gw_projection_latest.json"

    if not os.path.exists(metrics_file):
        raise Exception(f"Metriche non trovate: {metrics_file}")

    if not os.path.exists(prices_file):
        raise Exception(f"Prezzi non trovati: {prices_file}")

    with open(metrics_file, "r", encoding="utf-8") as f:
        metrics_data = json.load(f)

    with open(prices_file, "r", encoding="utf-8") as f:
        prices_data = json.load(f)

    metrics = metrics_data.get("players", [])
    prices = prices_data.get("players", [])

    price_index = build_price_index(prices)

    projections = []

    for player in metrics:
        slug = player.get("slug")
        scores = clean_scores(player.get("lastScores"))

        l5 = player.get("l5")
        l10 = player.get("l10")
        l40 = player.get("l40")
        aa = player.get("aa")
        decisive = player.get("decisive")
        starter_rate = player.get("starterRate")
        minutes_last10 = player.get("minutesLast10")
        position = player.get("position")

        consistency = calculate_consistency(scores)
        spike_rating = calculate_spike_rating(
            scores=scores,
            decisive=decisive,
            position=position
        )

        floor_projected = calculate_floor_projected(
            l10=l10,
            l40=l40,
            aa=aa,
            starter_rate=starter_rate,
            minutes_last10=minutes_last10
        )

        base_projected = calculate_base_projected(
            l5=l5,
            l10=l10,
            l40=l40,
            aa=aa,
            starter_rate=starter_rate,
            minutes_last10=minutes_last10
        )

        ceiling_projected = calculate_ceiling_projected(
            scores=scores,
            base_projected=base_projected,
            spike_rating=spike_rating
        )

        risk_level = calculate_risk_level(
            starter_rate=starter_rate,
            minutes_last10=minutes_last10,
            consistency=consistency
        )

        price = price_index.get(slug, {})
        limited_floor = price.get("limitedFloor", {}) if price else {}

        projections.append({
            "slug": slug,
            "displayName": player.get("displayName"),
            "club": player.get("club"),
            "club_slug": player.get("club_slug"),
            "position": position,
            "age": player.get("age"),
            "u23": player.get("u23"),

            "l5": l5,
            "l10": l10,
            "l40": l40,
            "aa": aa,
            "decisive": decisive,
            "starterRate": starter_rate,
            "minutesLast10": minutes_last10,
            "lastScores": player.get("lastScores"),

            "floorProjected": floor_projected,
            "baseProjected": base_projected,
            "ceilingProjected": ceiling_projected,
            "spikeRating": spike_rating,
            "consistencyScore": consistency,
            "riskLevel": risk_level,

            "limitedFloorValue": get_floor_value(price),
            "limitedFloorType": limited_floor.get("type"),
            "limitedFloorCurrency": (
                "EUR" if limited_floor.get("eur") is not None
                else "USD" if limited_floor.get("usd") is not None
                else "ETH" if limited_floor.get("eth") is not None
                else None
            ),

            "updated_at": datetime.utcnow().isoformat()
        })

    projections = sorted(
        projections,
        key=lambda x: x.get("baseProjected") or 0,
        reverse=True
    )

    output = {
        "updated_at": datetime.utcnow().isoformat(),
        "league": metrics_data.get("league"),
        "league_key": league_key,
        "seasonStartYear": season,
        "source_metrics": metrics_file,
        "source_prices": prices_file,
        "total_players": len(projections),
        "model": {
            "version": "v1",
            "description": "Floor/Base/Ceiling projection based on L5, L10, L40, AA, minutes, starterRate and lastScores. No matchup yet."
        },
        "players": projections
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("==============================")
    print("DONE")
    print("Projection file:", output_file)
    print("Players projected:", len(projections))
    print("==============================")


if __name__ == "__main__":
    main()
