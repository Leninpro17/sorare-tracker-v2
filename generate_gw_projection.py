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


def bottom_average(values, count=3):
    if not values:
        return None

    sorted_values = sorted(values)
    bottom_values = sorted_values[:count]

    return average(bottom_values)


def calculate_consistency(scores):
    """
    0-100.
    Più alto = giocatore più costante.
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


def calculate_volatility(scores):
    """
    0-100.
    Più alto = più volatile/spike.
    """
    if len(scores) < 3:
        return 50

    consistency = calculate_consistency(scores)
    volatility = 100 - consistency

    return max(0, min(100, round(volatility, 1)))


def position_group(position):
    if position == "Goalkeeper":
        return "GK"

    if position == "Defender":
        return "DEF"

    if position == "Midfielder":
        return "MID"

    if position == "Forward":
        return "FWD"

    return "UNK"


def calculate_spike_rating(scores, decisive, position):
    """
    Spike rating 0-100.
    Più alto = più potenziale di punteggio alto.
    """
    if not scores:
        return 30

    pos = position_group(position)

    max_score = max(scores)
    top3 = top_average(scores, 3) or 0
    decisive = safe_number(decisive)

    score = 0

    if pos == "GK":
        score += min(max_score, 100) * 0.40
        score += min(top3, 100) * 0.35
        score += min(decisive, 60) * 0.15
        score += 5

    elif pos == "DEF":
        score += min(max_score, 100) * 0.40
        score += min(top3, 100) * 0.35
        score += min(decisive, 60) * 0.20
        score += 3

    elif pos == "MID":
        score += min(max_score, 100) * 0.42
        score += min(top3, 100) * 0.35
        score += min(decisive, 60) * 0.20
        score += 4

    elif pos == "FWD":
        score += min(max_score, 100) * 0.45
        score += min(top3, 100) * 0.30
        score += min(decisive, 60) * 0.25
        score += 7

    else:
        score += min(max_score, 100) * 0.45
        score += min(top3, 100) * 0.35
        score += min(decisive, 60) * 0.20

    return max(0, min(100, round(score, 1)))


def minutes_factor(starter_rate, minutes_last10):
    starter_rate = safe_number(starter_rate)
    minutes_last10 = safe_number(minutes_last10)

    factor = 1.0

    if starter_rate >= 90:
        factor *= 1.06
    elif starter_rate >= 80:
        factor *= 1.03
    elif starter_rate >= 60:
        factor *= 0.95
    elif starter_rate >= 40:
        factor *= 0.85
    else:
        factor *= 0.70

    if minutes_last10 >= 850:
        factor *= 1.04
    elif minutes_last10 >= 700:
        factor *= 1.02
    elif minutes_last10 >= 500:
        factor *= 0.95
    elif minutes_last10 >= 300:
        factor *= 0.85
    else:
        factor *= 0.70

    return factor


def calculate_risk_level(starter_rate, minutes_last10, consistency, base_projected):
    starter_rate = safe_number(starter_rate)
    minutes_last10 = safe_number(minutes_last10)
    consistency = safe_number(consistency)
    base_projected = safe_number(base_projected)

    if starter_rate >= 80 and minutes_last10 >= 700 and consistency >= 60 and base_projected >= 40:
        return "LOW"

    if starter_rate >= 55 and minutes_last10 >= 450 and base_projected >= 35:
        return "MEDIUM"

    return "HIGH"


def calculate_floor_projected(position, l10, l40, aa, starter_rate, minutes_last10, scores):
    """
    Floor = stima prudente.
    Diversa per ruolo.
    """
    pos = position_group(position)

    l10 = safe_number(l10)
    l40 = safe_number(l40)
    aa = safe_number(aa)

    bottom3 = bottom_average(scores, 3)
    bottom3 = safe_number(bottom3, l10 * 0.75)

    if pos == "GK":
        base = (
            l10 * 0.35
            + l40 * 0.35
            + bottom3 * 0.20
            + aa * 0.10
        )

    elif pos == "DEF":
        base = (
            l10 * 0.35
            + l40 * 0.25
            + bottom3 * 0.20
            + aa * 0.20
        )

    elif pos == "MID":
        base = (
            l10 * 0.35
            + l40 * 0.25
            + bottom3 * 0.15
            + aa * 0.25
        )

    elif pos == "FWD":
        base = (
            l10 * 0.40
            + l40 * 0.25
            + bottom3 * 0.20
            + aa * 0.15
        )

    else:
        base = (
            l10 * 0.40
            + l40 * 0.30
            + bottom3 * 0.20
            + aa * 0.10
        )

    base *= minutes_factor(starter_rate, minutes_last10)

    return round(base, 1)


def calculate_base_projected(position, l5, l10, l40, aa, starter_rate, minutes_last10):
    """
    Base projection = stima centrale.
    Diversa per ruolo.
    """
    pos = position_group(position)

    l5 = safe_number(l5)
    l10 = safe_number(l10)
    l40 = safe_number(l40)
    aa = safe_number(aa)

    if pos == "GK":
        projected = (
            l10 * 0.45
            + l5 * 0.20
            + l40 * 0.25
            + aa * 0.10
        )

    elif pos == "DEF":
        projected = (
            l10 * 0.40
            + l5 * 0.20
            + l40 * 0.20
            + aa * 0.20
        )

    elif pos == "MID":
        projected = (
            l10 * 0.40
            + l5 * 0.20
            + l40 * 0.20
            + aa * 0.20
        )

    elif pos == "FWD":
        projected = (
            l10 * 0.45
            + l5 * 0.25
            + l40 * 0.20
            + aa * 0.10
        )

    else:
        projected = (
            l10 * 0.45
            + l5 * 0.25
            + l40 * 0.20
            + aa * 0.10
        )

    projected *= minutes_factor(starter_rate, minutes_last10)

    return round(projected, 1)


def calculate_ceiling_projected(position, scores, base_projected, spike_rating, decisive, aa):
    """
    Ceiling = scenario alto.
    Diverso per ruolo.
    """
    pos = position_group(position)

    base_projected = safe_number(base_projected)
    decisive = safe_number(decisive)
    aa = safe_number(aa)

    if not scores:
        return round(base_projected * 1.20, 1)

    max_score = max(scores)
    top3 = top_average(scores, 3) or max_score

    if pos == "GK":
        ceiling = (
            max_score * 0.40
            + top3 * 0.35
            + base_projected * 0.25
        )

    elif pos == "DEF":
        ceiling = (
            max_score * 0.42
            + top3 * 0.33
            + base_projected * 0.20
            + aa * 0.05
        )

    elif pos == "MID":
        ceiling = (
            max_score * 0.40
            + top3 * 0.30
            + base_projected * 0.20
            + aa * 0.10
        )

    elif pos == "FWD":
        ceiling = (
            max_score * 0.45
            + top3 * 0.30
            + base_projected * 0.15
            + decisive * 0.10
        )

    else:
        ceiling = (
            max_score * 0.45
            + top3 * 0.35
            + base_projected * 0.20
        )

    if spike_rating >= 80:
        ceiling *= 1.10
    elif spike_rating >= 70:
        ceiling *= 1.07
    elif spike_rating >= 60:
        ceiling *= 1.04

    return round(ceiling, 1)


def classify_profile(floor_projected, base_projected, ceiling_projected, spike_rating, consistency, risk_level):
    floor_projected = safe_number(floor_projected)
    base_projected = safe_number(base_projected)
    ceiling_projected = safe_number(ceiling_projected)
    spike_rating = safe_number(spike_rating)
    consistency = safe_number(consistency)

    if risk_level == "HIGH":
        if spike_rating >= 70 or ceiling_projected >= 65:
            return "RISKY_SPIKE"
        return "MINUTES_RISK"

    if floor_projected >= 40 and consistency >= 65 and risk_level == "LOW":
        return "FLOOR_PLAYER"

    if ceiling_projected >= 70 or spike_rating >= 75:
        return "CEILING_PLAYER"

    if base_projected >= 45:
        return "BALANCED_PLAYER"

    return "DEPTH_PLAYER"


def classify_lineup_use(profile_type, floor_projected, ceiling_projected, risk_level):
    floor_projected = safe_number(floor_projected)
    ceiling_projected = safe_number(ceiling_projected)

    if profile_type == "MINUTES_RISK":
        return "AVOID"

    if profile_type == "FLOOR_PLAYER":
        return "SAFE"

    if profile_type in ["CEILING_PLAYER", "RISKY_SPIKE"]:
        if ceiling_projected >= 65:
            return "TARGET_360"
        return "UPSIDE"

    if risk_level == "LOW" and floor_projected >= 35:
        return "SAFE"

    return "UPSIDE"


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


def get_floor_currency(price):
    if not price:
        return None

    floor = price.get("limitedFloor", {})

    if floor.get("eur") is not None:
        return "EUR"

    if floor.get("usd") is not None:
        return "USD"

    if floor.get("eth") is not None:
        return "ETH"

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
        volatility = calculate_volatility(scores)

        spike_rating = calculate_spike_rating(
            scores=scores,
            decisive=decisive,
            position=position
        )

        floor_projected = calculate_floor_projected(
            position=position,
            l10=l10,
            l40=l40,
            aa=aa,
            starter_rate=starter_rate,
            minutes_last10=minutes_last10,
            scores=scores
        )

        base_projected = calculate_base_projected(
            position=position,
            l5=l5,
            l10=l10,
            l40=l40,
            aa=aa,
            starter_rate=starter_rate,
            minutes_last10=minutes_last10
        )

        ceiling_projected = calculate_ceiling_projected(
            position=position,
            scores=scores,
            base_projected=base_projected,
            spike_rating=spike_rating,
            decisive=decisive,
            aa=aa
        )

        risk_level = calculate_risk_level(
            starter_rate=starter_rate,
            minutes_last10=minutes_last10,
            consistency=consistency,
            base_projected=base_projected
        )

        profile_type = classify_profile(
            floor_projected=floor_projected,
            base_projected=base_projected,
            ceiling_projected=ceiling_projected,
            spike_rating=spike_rating,
            consistency=consistency,
            risk_level=risk_level
        )

        lineup_use = classify_lineup_use(
            profile_type=profile_type,
            floor_projected=floor_projected,
            ceiling_projected=ceiling_projected,
            risk_level=risk_level
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
            "volatilityScore": volatility,
            "riskLevel": risk_level,
            "profileType": profile_type,
            "lineupUse": lineup_use,

            "limitedFloorValue": get_floor_value(price),
            "limitedFloorType": limited_floor.get("type"),
            "limitedFloorCurrency": get_floor_currency(price),

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
            "version": "v2_role_adjusted",
            "description": "Role-adjusted Floor/Base/Ceiling projection. Uses L5, L10, L40, AA, decisive, minutes, starterRate, lastScores, consistency and spike rating. No matchup yet."
        },
        "players": projections
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("==============================")
    print("DONE")
    print("Projection file:", output_file)
    print("Players projected:", len(projections))
    print("Model: v2_role_adjusted")
    print("==============================")


if __name__ == "__main__":
    main()
