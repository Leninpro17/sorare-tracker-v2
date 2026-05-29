import os
import json
import argparse
from datetime import datetime
from config import LEAGUES


def get_floor_value(floor):
    """
    Ritorna sempre il prezzo normalizzato in EUR quando disponibile.
    Richiede che update_player_prices.py abbia creato eurNormalized.
    """
    if not floor:
        return None

    if floor.get("eurNormalized") is not None:
        return floor.get("eurNormalized")

    if floor.get("eur") is not None:
        return floor.get("eur")

    return None


def get_floor_currency(floor):
    """
    Ora il valore principale usato per gli score è EUR normalizzato.
    Qui teniamo comunque la valuta originale per debug/report.
    """
    if not floor:
        return None

    if floor.get("eurNormalized") is not None:
        return "EUR"

    if floor.get("eur") is not None:
        return "EUR"

    if floor.get("usd") is not None:
        return "USD"

    if floor.get("eth") is not None:
        return "ETH"

    return floor.get("referenceCurrency")


def build_index(items):
    index = {}

    for item in items:
        slug = item.get("slug")
        if slug:
            index[slug] = item

    return index


def normalize_signal_score(raw_score):
    """
    Evita troppi 100 nel report.

    70-79 = watch
    80-89 = good
    90-97 = top
    98+ = elite raro
    """
    if raw_score <= 70:
        return raw_score

    if raw_score <= 90:
        return 70 + (raw_score - 70) * 0.75

    if raw_score <= 110:
        return 85 + (raw_score - 90) * 0.5

    return min(99, 95 + (raw_score - 110) * 0.15)


def base_player(metric, price, projection):
    limited_floor = price.get("limitedFloor", {}) if price else {}
    rare_floor = price.get("rareFloor", {}) if price else {}

    limited_floor_value = get_floor_value(limited_floor)
    rare_floor_value = get_floor_value(rare_floor)

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

        "floorProjected": projection.get("floorProjected"),
        "baseProjected": projection.get("baseProjected"),
        "ceilingProjected": projection.get("ceilingProjected"),
        "spikeRating": projection.get("spikeRating"),
        "consistencyScore": projection.get("consistencyScore"),
        "volatilityScore": projection.get("volatilityScore"),
        "riskLevel": projection.get("riskLevel"),
        "profileType": projection.get("profileType"),
        "lineupUse": projection.get("lineupUse"),

        # Prezzo normalizzato in EUR
        "limitedFloorValue": limited_floor_value,
        "limitedFloorEur": limited_floor_value,
        "limitedFloorCurrency": get_floor_currency(limited_floor),
        "limitedFloorOriginalCurrency": limited_floor.get("referenceCurrency"),
        "limitedFloorType": limited_floor.get("type"),
        "limitedFloorSeasonYear": limited_floor.get("seasonYear"),

        "rareFloorValue": rare_floor_value,
        "rareFloorEur": rare_floor_value,
        "rareFloorCurrency": get_floor_currency(rare_floor),
        "rareFloorOriginalCurrency": rare_floor.get("referenceCurrency"),
        "rareFloorType": rare_floor.get("type"),
        "rareFloorSeasonYear": rare_floor.get("seasonYear"),
    }


def add_signal(bucket, player, score, reason):
    item = dict(player)
    item["rawSignalScore"] = round(score, 1)
    item["signalScore"] = round(normalize_signal_score(score), 1)
    item["reason"] = reason
    bucket.append(item)


def score_safe_starter(p):
    score = 0

    if (p.get("starterRate") or 0) >= 80:
        score += 30

    if (p.get("minutesLast10") or 0) >= 700:
        score += 20

    if (p.get("l10") or 0) >= 45:
        score += 15

    if (p.get("l40") or 0) >= 45:
        score += 10

    if (p.get("aa") or 0) >= 10:
        score += 10

    if p.get("riskLevel") == "LOW":
        score += 15

    return score


def score_aa_value(p):
    score = 0
    floor = p.get("limitedFloorEur")

    if (p.get("aa") or 0) >= 12:
        score += 30

    if (p.get("starterRate") or 0) >= 70:
        score += 20

    if (p.get("baseProjected") or 0) >= 45:
        score += 20

    if floor is not None:
        if floor <= 1:
            score += 30
        elif floor <= 3:
            score += 20
        elif floor <= 5:
            score += 10

    return score


def score_u23_watch(p):
    score = 0
    floor = p.get("limitedFloorEur")

    if p.get("u23") is True:
        score += 30

    if (p.get("starterRate") or 0) >= 50:
        score += 20

    if (p.get("baseProjected") or 0) >= 40:
        score += 20

    if (p.get("ceilingProjected") or 0) >= 60:
        score += 15

    if floor is not None:
        if floor <= 5:
            score += 15
        elif floor <= 10:
            score += 8

    return score


def score_minutes_risk(p):
    score = 0

    if (p.get("starterRate") or 0) < 40:
        score += 35

    if (p.get("minutesLast10") or 0) < 300:
        score += 35

    if (p.get("baseProjected") or 0) < 35:
        score += 15

    if p.get("riskLevel") == "HIGH":
        score += 15

    return score


def score_classic_value(p):
    score = 0
    floor = p.get("limitedFloorEur")

    if p.get("limitedFloorType") == "CLASSIC":
        score += 25

    if (p.get("starterRate") or 0) >= 70:
        score += 20

    if (p.get("baseProjected") or 0) >= 45:
        score += 20

    if (p.get("aa") or 0) >= 10:
        score += 15

    if floor is not None:
        if floor <= 1:
            score += 20
        elif floor <= 3:
            score += 10

    return score


def score_inseason_value(p):
    score = 0
    floor = p.get("limitedFloorEur")

    if p.get("limitedFloorType") == "IN_SEASON":
        score += 20

    if (p.get("starterRate") or 0) >= 70:
        score += 20

    if (p.get("baseProjected") or 0) >= 45:
        score += 20

    if (p.get("aa") or 0) >= 10:
        score += 15

    if floor is not None:
        if floor <= 2:
            score += 25
        elif floor <= 5:
            score += 12

    return score


def score_safe_floor(p):
    score = 0

    if (p.get("floorProjected") or 0) >= 40:
        score += 30

    if (p.get("baseProjected") or 0) >= 45:
        score += 20

    if (p.get("starterRate") or 0) >= 80:
        score += 20

    if (p.get("consistencyScore") or 0) >= 65:
        score += 15

    if p.get("riskLevel") == "LOW":
        score += 15

    return score


def score_ceiling_value(p):
    score = 0
    floor = p.get("limitedFloorEur")

    if (p.get("ceilingProjected") or 0) >= 65:
        score += 35

    if (p.get("spikeRating") or 0) >= 65:
        score += 25

    if (p.get("starterRate") or 0) >= 60:
        score += 15

    if floor is not None:
        if floor <= 2:
            score += 25
        elif floor <= 5:
            score += 15
        elif floor <= 10:
            score += 8

    return score


def score_target_360_watch(p):
    """
    Non significa che il singolo fa 360.
    Significa che può essere utile in team target 360:
    ceiling alto, spike alto, prezzo accessibile.
    """
    score = 0
    floor = p.get("limitedFloorEur")

    if (p.get("ceilingProjected") or 0) >= 70:
        score += 35
    elif (p.get("ceilingProjected") or 0) >= 60:
        score += 20

    if (p.get("spikeRating") or 0) >= 70:
        score += 25
    elif (p.get("spikeRating") or 0) >= 60:
        score += 15

    if (p.get("baseProjected") or 0) >= 45:
        score += 15

    if (p.get("starterRate") or 0) >= 70:
        score += 15

    if floor is not None:
        if floor <= 5:
            score += 10
        elif floor <= 10:
            score += 5

    return score


def score_low_risk_value(p):
    score = 0
    floor = p.get("limitedFloorEur")

    if p.get("riskLevel") == "LOW":
        score += 25

    if (p.get("starterRate") or 0) >= 80:
        score += 20

    if (p.get("floorProjected") or 0) >= 40:
        score += 20

    if (p.get("baseProjected") or 0) >= 45:
        score += 15

    if floor is not None:
        if floor <= 3:
            score += 20
        elif floor <= 6:
            score += 10

    return score


def score_high_spike_cheap(p):
    score = 0
    floor = p.get("limitedFloorEur")

    if (p.get("spikeRating") or 0) >= 70:
        score += 35

    if (p.get("ceilingProjected") or 0) >= 65:
        score += 30

    if floor is not None:
        if floor <= 2:
            score += 25
        elif floor <= 5:
            score += 15

    if (p.get("starterRate") or 0) >= 50:
        score += 10

    return score


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
    projections_file = f"{base_dir}/gw_projection_latest.json"
    output_file = f"{base_dir}/buy_signals_latest.json"

    if not os.path.exists(metrics_file):
        raise Exception(f"Metriche non trovate: {metrics_file}")

    if not os.path.exists(prices_file):
        raise Exception(f"Prezzi non trovati: {prices_file}")

    if not os.path.exists(projections_file):
        raise Exception(f"Projection non trovata: {projections_file}")

    with open(metrics_file, "r", encoding="utf-8") as f:
        metrics_data = json.load(f)

    with open(prices_file, "r", encoding="utf-8") as f:
        prices_data = json.load(f)

    with open(projections_file, "r", encoding="utf-8") as f:
        projections_data = json.load(f)

    metrics = metrics_data.get("players", [])
    prices = prices_data.get("players", [])
    projections = projections_data.get("players", [])

    price_index = build_index(prices)
    projection_index = build_index(projections)

    signals = {
        "safe_starter": [],
        "aa_value": [],
        "u23_watch": [],
        "minutes_risk": [],
        "classic_value_watch": [],
        "inseason_value_watch": [],

        "safe_floor": [],
        "ceiling_value": [],
        "target_360_watch": [],
        "low_risk_value": [],
        "high_spike_cheap": []
    }

    for metric in metrics:
        slug = metric.get("slug")
        price = price_index.get(slug, {})
        projection = projection_index.get(slug, {})

        p = base_player(metric, price, projection)

        safe_score = score_safe_starter(p)
        if safe_score >= 70:
            add_signal(
                signals["safe_starter"],
                p,
                safe_score,
                "Alta titolarità, minuti solidi e rischio basso."
            )

        aa_score = score_aa_value(p)
        if aa_score >= 70:
            add_signal(
                signals["aa_value"],
                p,
                aa_score,
                "Buon AA rispetto al prezzo Limited normalizzato in EUR e projection solida."
            )

        u23_score = score_u23_watch(p)
        if u23_score >= 65:
            add_signal(
                signals["u23_watch"],
                p,
                u23_score,
                "Profilo U23 con minuti, projection e upside interessanti."
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
                "Floor Classic interessante con metriche/projection solide."
            )

        inseason_score = score_inseason_value(p)
        if inseason_score >= 70:
            add_signal(
                signals["inseason_value_watch"],
                p,
                inseason_score,
                "Floor In-Season interessante con metriche/projection solide."
            )

        safe_floor_score = score_safe_floor(p)
        if safe_floor_score >= 70:
            add_signal(
                signals["safe_floor"],
                p,
                safe_floor_score,
                "Profilo con buon floor projected, consistenza e rischio basso."
            )

        ceiling_score = score_ceiling_value(p)
        if ceiling_score >= 70:
            add_signal(
                signals["ceiling_value"],
                p,
                ceiling_score,
                "Ceiling interessante rispetto al prezzo Limited normalizzato in EUR."
            )

        target_score = score_target_360_watch(p)
        if target_score >= 70:
            add_signal(
                signals["target_360_watch"],
                p,
                target_score,
                "Profilo utile per team target 360 grazie a ceiling/spike."
            )

        low_risk_score = score_low_risk_value(p)
        if low_risk_score >= 70:
            add_signal(
                signals["low_risk_value"],
                p,
                low_risk_score,
                "Value con rischio basso, buon floor e titolarità."
            )

        spike_score = score_high_spike_cheap(p)
        if spike_score >= 70:
            add_signal(
                signals["high_spike_cheap"],
                p,
                spike_score,
                "Profilo economico con alto potenziale spike."
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
        "source_projections": projections_file,
        "price_note": "limitedFloorValue and limitedFloorEur use eurNormalized when available.",
        "score_note": "signalScore is normalized to avoid too many 100s. rawSignalScore keeps the original score.",
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
