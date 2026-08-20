#!/usr/bin/env python3
"""Summarise public RFL match geometry without reading rival repositories.

Usage:
    python tools/analyze_round.py ../rfl-league-data/seasons/s2

The output is intentionally derived only from the league archive's match and
telemetry files, so the evidence behind a nightly tactical change is repeatable.
"""

import argparse
import json
import math
from collections import Counter
from pathlib import Path


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def distance(a, b):
    return math.hypot(float(a[0]) - float(b[0]),
                      float(a[1]) - float(b[1]))


def percent(count, total):
    return round(100.0 * count / total, 1) if total else 0.0


def geometry(rows, team):
    sign = 1.0 if team == 0 else -1.0
    ids = (team * 2, team * 2 + 1)
    attack = nearest = doubled = 0
    pair_sum = ball_sum = 0.0
    role_nearest = Counter()

    for row in rows:
        ball = row["ball"]
        players = [row["robots"][index] for index in ids]
        team_distances = [distance(player, ball) for player in players]
        all_distances = [distance(player, ball) for player in row["robots"]]
        attack += sign * float(ball[0]) > 0.0
        nearest += min(range(4), key=all_distances.__getitem__) in ids
        doubled += all(value <= 2.0 for value in team_distances)
        pair_sum += distance(*players)
        ball_sum += min(team_distances)
        role_nearest[min(range(2), key=team_distances.__getitem__)] += 1

    count = len(rows)
    return {
        "attack_half_pct": percent(attack, count),
        "nearest_ball_pct": percent(nearest, count),
        "double_commit_pct": percent(doubled, count),
        "pair_distance_m": round(pair_sum / count, 2) if count else 0.0,
        "nearest_ball_m": round(ball_sum / count, 2) if count else 0.0,
        "role_nearest_pct": [percent(role_nearest[i], count)
                             for i in range(2)],
    }


def event_counts(match, team):
    ids = (team * 2, team * 2 + 1)
    return {
        "through": sum(event.get("kind") == "through"
                       and event.get("who") in ids
                       for event in match.get("events", [])),
        "falls": sum(event.get("kind") == "fall"
                     and event.get("who") in ids
                     for event in match.get("events", [])),
    }


def goal_line(goal):
    credited = 0 if goal["team"] == "A" else 1
    scorer = int(goal["scorer"])
    own_goal = scorer // 2 != credited
    suffix = " own-goal" if own_goal else ""
    return f'{float(goal["t"]):6.1f}s {goal["team"]} r{scorer}{suffix}'


def analyse(match_dir):
    match = json.loads((match_dir / "match.json").read_text())
    telemetry = read_jsonl(match_dir / "telemetry.jsonl")
    names = [match["teams"][side]["name"] for side in ("A", "B")]
    score = match["score"]
    print(f"\n{match_dir.name}: {names[0]} {score[0]}-{score[1]} {names[1]}")
    for team, name in enumerate(names):
        robots = match["robots"][team * 2:team * 2 + 2]
        summary = geometry(telemetry, team)
        summary.update(event_counts(match, team))
        summary["touches"] = [robot["touches"] for robot in robots]
        summary["invalid"] = [robot["invalid_actions"] for robot in robots]
        print(f"  {name}: {json.dumps(summary, sort_keys=True)}")
    for goal in match.get("goals", []):
        print("   goal", goal_line(goal))
    return names, telemetry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("season", type=Path,
                        help="league archive season directory")
    parser.add_argument("--club", default="Codex City",
                        help="club whose first/second-half split to print")
    args = parser.parse_args()

    club_match = None
    for match_file in sorted(args.season.glob("m*/match.json")):
        names, rows = analyse(match_file.parent)
        if args.club in names:
            club_match = (names.index(args.club), rows)

    if club_match:
        team, rows = club_match
        print(f"\n{args.club} half split")
        for label, low, high in (("first", 0.0, 300.0),
                                 ("second", 300.0, 601.0)):
            half = [row for row in rows if low <= float(row["t"]) < high]
            print(f"  {label}: {json.dumps(geometry(half, team), sort_keys=True)}")


if __name__ == "__main__":
    main()
