import os
import json
import argparse
from datetime import datetime
from config import LEAGUES


def fmt(value, default="-"):
    if value is None:
        return default

    if isinstance(value, float):
        return round(value, 2)

    return value


def format_floor(value, currency):
    if value is None:
        return "-"

    if currency == "EUR":
        return f"€{value}"

    if currency == "USD":
        return f"${value}"

    if currency == "ETH":
        return f"{value} ETH"

    return str(value)


def player_line(player, index):
    limited_price = format_floor(
        player.get("limitedFloorValue"),
        player.get("limitedFloorCurrency")
    )

    return (
        f"| {index} "
        f"| {player.get('displayName', '-')} "
        f"| {player.get('club', '-')} "
        f"| {player.get('position', '-')} "
        f"| {fmt(player.get('age'))} "
        f"| {fmt(player.get('l10'))} "
        f"| {fmt(player.get('aa'))} "
        f"| {fmt(player.get('starterRate'))}% "
        f"| {fmt(player.get('floorProjected'))} "
        f"| {fmt(player.get('baseProjected'))} "
        f"| {fmt(player.get('ceilingProjected'))} "
        f"| {fmt(player.get('spikeRating'))} "
        f"| {player.get('riskLevel') or '-'} "
        f"| {limited_price} "
        f"| {player.get('limitedFloorType') or '-'} "
        f"| {player.get('signalScore', '-')} "
        f"|"
    )


def section(title, players, limit):
    lines = []

    lines.append(f"\n## {title}\n")

    if not players:
        lines.append("_Nessun giocatore trovato._\n")
        return lines

    lines.append(
        "| # | Player | Club | Pos | Age | L10 | AA | Starter | Floor Proj | Base Proj | Ceiling Proj | Spike | Risk | Limited Floor | Type | Score |"
    )
    lines.append(
        "|---|--------|------|-----|-----|-----|----|---------|------------|-----------|--------------|-------|------|---------------|------|-------|"
    )

    for i, player in enumerate(players[:limit], start=1):
        lines.append(player_line(player, i))

    lines.append("")
    return lines


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

    parser.add_argument(
        "--limit",
        required=False,
        type=int,
        default=15
    )

    args = parser.parse_args()

    league_key = args.league
    season = args.season
    limit = args.limit

    base_dir = f"data/{league_key}/{season}"
    signals_file = f"{base_dir}/buy_signals_latest.json"

    reports_dir = f"{base_dir}/reports"
    os.makedirs(reports_dir, exist_ok=True)

    output_file = f"{reports_dir}/report_latest.md"

    if not os.path.exists(signals_file):
        raise Exception(f"buy_signals_latest.json non trovato: {signals_file}")

    with open(signals_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    signals = data.get("signals", {})
    counts = data.get("counts", {})

    lines = []

    lines.append(f"# Sorare Report - {data.get('league', league_key)} {season}")
    lines.append("")
    lines.append(f"Generated at: `{datetime.utcnow().isoformat()}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Safe Starter: **{counts.get('safe_starter', 0)}**")
    lines.append(f"- AA Value: **{counts.get('aa_value', 0)}**")
    lines.append(f"- U23 Watch: **{counts.get('u23_watch', 0)}**")
    lines.append(f"- Minutes Risk: **{counts.get('minutes_risk', 0)}**")
    lines.append(f"- Classic Value Watch: **{counts.get('classic_value_watch', 0)}**")
    lines.append(f"- In-Season Value Watch: **{counts.get('inseason_value_watch', 0)}**")
    lines.append(f"- Safe Floor: **{counts.get('safe_floor', 0)}**")
    lines.append(f"- Ceiling Value: **{counts.get('ceiling_value', 0)}**")
    lines.append(f"- Target 360 Watch: **{counts.get('target_360_watch', 0)}**")
    lines.append(f"- Low Risk Value: **{counts.get('low_risk_value', 0)}**")
    lines.append(f"- High Spike Cheap: **{counts.get('high_spike_cheap', 0)}**")
    lines.append("")

    lines += section(
        "🔥 TOP SAFE STARTER",
        signals.get("safe_starter", []),
        limit
    )

    lines += section(
        "💎 TOP AA VALUE",
        signals.get("aa_value", []),
        limit
    )

    lines += section(
        "🟢 TOP U23 WATCH",
        signals.get("u23_watch", []),
        limit
    )

    lines += section(
        "🧱 TOP SAFE FLOOR",
        signals.get("safe_floor", []),
        limit
    )

    lines += section(
        "🚀 TOP CEILING VALUE",
        signals.get("ceiling_value", []),
        limit
    )

    lines += section(
        "🎯 TOP TARGET 360 WATCH",
        signals.get("target_360_watch", []),
        limit
    )

    lines += section(
        "🛡️ TOP LOW RISK VALUE",
        signals.get("low_risk_value", []),
        limit
    )

    lines += section(
        "⚡ TOP HIGH SPIKE CHEAP",
        signals.get("high_spike_cheap", []),
        limit
    )

    lines += section(
        "📉 TOP CLASSIC VALUE WATCH",
        signals.get("classic_value_watch", []),
        limit
    )

    lines += section(
        "🟣 TOP IN-SEASON VALUE WATCH",
        signals.get("inseason_value_watch", []),
        limit
    )

    lines += section(
        "⚠️ TOP MINUTES RISK",
        signals.get("minutes_risk", []),
        limit
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("==============================")
    print("DONE")
    print("Report file:", output_file)
    print("==============================")


if __name__ == "__main__":
    main()
