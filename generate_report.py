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
        f"| {fmt(player.get('l40'))} "
        f"| {fmt(player.get('aa'))} "
        f"| {fmt(player.get('starterRate'))}% "
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
        "| # | Player | Club | Pos | Age | L10 | L40 | AA | Starter | Limited Floor | Type | Score |"
    )
    lines.append(
        "|---|--------|------|-----|-----|-----|-----|----|---------|---------------|------|-------|"
    )

    for i, player in enumerate(players[:limit], start=1):
        lines.append(player_line(player, i))

    lines.append("")
    return lines


def filter_goalkeepers(signals):
    all_players = []

    for key in [
        "safe_starter",
        "aa_value",
        "inseason_value_watch",
        "classic_value_watch",
        "u23_watch"
    ]:
        all_players.extend(signals.get(key, []))

    by_slug = {}

    for player in all_players:
        if player.get("position") == "Goalkeeper":
            slug = player.get("slug")

            if not slug:
                continue

            previous = by_slug.get(slug)

            if (
                previous is None
                or (player.get("signalScore") or 0) > (previous.get("signalScore") or 0)
            ):
                by_slug[slug] = player

    return sorted(
        by_slug.values(),
        key=lambda x: (
            x.get("starterRate") or 0,
            x.get("l10") or 0,
            x.get("signalScore") or 0
        ),
        reverse=True
    )


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

    top_gk = filter_goalkeepers(signals)

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
    lines.append(f"- Top GK: **{len(top_gk)}**")
    lines.append("")

    lines += section(
        "🧤 TOP GK",
        top_gk,
        limit
    )

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
    print("Top GK:", len(top_gk))
    print("==============================")


if __name__ == "__main__":
    main()
