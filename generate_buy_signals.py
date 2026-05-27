import os
import json
import argparse
from datetime import datetime
from config import LEAGUES


def get_floor_value(floor):
    if not floor:
        return None

    if floor.get("eur") is not None:
        return floor.get("eur")

    if floor.get("usd") is not None:
        return floor.get("usd")

    if floor.get("eth") is not None:
        return floor.get("eth")

    return None


def get_floor_currency(floor):
    if not floor:
        return None

    if floor.get("eur") is not None:
        return "EUR"

    if floor.get("usd") is not None:
        return "USD"

    if floor.get("eth") is not None:
        return "ETH"

    return floor.get("referenceCurrency")


def build_price_index(prices):
    index = {}

    for player in prices:
        slug = player.get("slug")
        if slug:
            index[slug] = player

    return index


def base_player(metric, price):
    limited_floor = price.get("limitedFloor", {}) if price else {}
    rare_floor = price.get("rareFloor", {}) if price else {}

    return {
        "slug": metric.get("slug"),
        "displayName": metric.get("displayName"),
        "club": metric.get("club"),
        "club_slug": metric.get("club_slug"),
        "position": metric.get("position"),
        "age": metric.get("age"),
        "u23": metric.get("u23"),

        "l5": metric.get("l5"),
        "l10": metric.get("l10"),
        "l40": metric.get("l40"),
        "aa": metric.get("aa"),
        "decisive": metric.get("decisive"),
        "minutesLast10": metric.get("minutesLast10"),
        "starterRate": metric.get("starterRate"),

        "limitedFloorValue": get_floor_value(limited_floor),
        "limitedFloorCurrency": get_floor_currency(limited_floor),
        "limitedFloorType": limited_floor.get("type"),
        "limitedFloorSeasonYear": limited_floor.get("seasonYear"),

        "rareFloorValue": get_floor_value(rare_floor),
        "rareFloorCurrency": get_floor_currency(rare_floor),
        "rareFloorType": rare_floor.get("type"),
        "rareFloorSeasonYear": rare_floor.get("seasonYear"),
    }


def score_safe_starter(p):
    score = 0

    if (p.get("starterRate") or 0) >= 80:
        score += 35

    if (p.get("minutesLast10") or 0) >= 700:
        score += 25

    if (p.get("l10") or 0) >= 45:
        score += 20

    if (p.get("l40") or 0) >= 45:
        score += 10

    if (p.get("aa") or 0) >= 10:
        score += 10

    return score


def score_aa_value(p):
    score = 0

    floor = p.get("limitedFloorValue")

    if (p.get("aa") or 0) >= 12:
        score += 35

    if (p.get("starterRate") or 0) >= 70:
        score += 25

    if (p.get("l10") or 0) >= 40:
        score += 15

    if floor is not None:
        if floor <= 1:
            score += 25
        elif floor <= 3:
            score += 15
        elif floor <= 5:
            score += 8

    return score


def score_u23_watch(p):
    score = 0

    if p.get("u23") is True:
        score += 35

    if (p.get("starterRate") or 0) >= 50:
        score += 25

    if (p.get("l10") or 0) >= 40:
        score += 20

    if (p.get("aa") or 0) >= 8:
        score += 10

    floor = p.get("limitedFloorValue")
    if floor is not None:
        if floor <= 5:
            score += 10
        elif floor <= 10:
            score += 5

    return score


def score_minutes_risk(p):
    score = 0

    if (p.get("starterRate") or 0) < 40:
        score += 40

    if (p.get("minutesLast10") or 0) < 300:
        score += 35

    if (p.get("l10") or 0) < 35:
        score += 15

    if p.get("limitedFloorValue") is not None and p.get("limitedFloorValue") > 5:
        score += 10

    return score


def score_classic_value(p):
    score = 0

    if p.get("limitedFloorType") == "CLASSIC":
        score += 30

    if (p.get("starterRate") or 0) >= 70:
        score += 25

    if (p.get("l10") or 0) >= 45:
        score += 20

    if (p.get("aa") or 0) >= 10:
        score += 15

    floor = p.get("limitedFloorValue")
    if floor is not None:
        if floor <= 1:
            score += 20
        elif floor <= 3:
            score += 10

    return score


def score_inseason_value(p):
    score = 0

    if p.get("limitedFloorType") == "IN_SEASON":
        score += 20

    if (p.get("starterRate") or 0) >= 70:
        score += 25

    if (p.get("l10") or 0) >= 45:
        score += 20

    if (p.get("aa") or 0) >= 10:
        score += 15

    floor = p.get("limitedFloorValue")
    if floor is not None:
        if floor <= 2:
            score += 20
        elif floor <= 5:
            score += 10

    return score


def add_signal(bucket, player, score, reason):
    item = dict(player)
    item["signalScore"] = score
    item["reason"] = reason
    bucket.append(item)


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
    output_file = f"{base_dir}/buy_signals_latest.json"

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

    signals = {
        "safe_starter": [],
        "aa_value": [],
        "u23_watch": [],
        "minutes_risk": [],
        "classic_value_watch": [],
        "inseason_value_watch": []
    }

    for metric in metrics:
        slug = metric.get("slug")
        price = price_index.get(slug, {})

        p = base_player(metric, price)

        safe_score = score_safe_starter(p)
        if safe_score >= 70:
            add_signal(
                signals["safe_starter"],
                p,
                safe_score,
                "Alta titolarità, minuti solidi e buone medie."
            )

        aa_score = score_aa_value(p)
        if aa_score >= 70:
            add_signal(
                signals["aa_value"],
                p,
                aa_score,
                "Buon AA rispetto al prezzo Limited."
            )

        u23_score = score_u23_watch(p)
        if u23_score >= 65:
            add_signal(
                signals["u23_watch"],
                p,
                u23_score,
                "Profilo U23 con minuti e rendimento interessanti."
            )

        risk_score = score_minutes_risk(p)
        if risk_score >= 70:
            add_signal(
                signals["minutes_risk"],
                p,
                risk_score,
                "Rischio minuti basso o titolarità instabile."
            )

        classic_score = score_classic_value(p)
        if classic_score >= 70:
            add_signal(
                signals["classic_value_watch"],
                p,
                classic_score,
                "Floor Classic interessante con metriche solide."
            )

        inseason_score = score_inseason_value(p)
        if inseason_score >= 70:
            add_signal(
                signals["inseason_value_watch"],
                p,
                inseason_score,
                "Floor In-Season interessante con metriche solide."
            )

    for key in signals:
        signals[key] = sorted(
            signals[key],
            key=lambda x: x["signalScore"],
            reverse=True
        )

    output = {
        "updated_at": datetime.utcnow().isoformat(),
        "league": metrics_data.get("league"),
        "league_key": league_key,
        "seasonStartYear": season,
        "source_metrics": metrics_file,
        "source_prices": prices_file,
        "counts": {
            key: len(value)
            for key, value in signals.items()
        },
        "signals": signals
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("==============================")
    print("DONE")
    print("Signals file:", output_file)
    print("Counts:")
    for key, value in signals.items():
        print(key, len(value))
    print("==============================")


if __name__ == "__main__":
    main()
