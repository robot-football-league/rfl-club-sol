#!/usr/bin/env python3
"""Reproduce Codex City's compact press/support/screen role policy.

Only public telemetry from successful frozen-club performances is used. The
labels describe the role demonstrated over the next three seconds; six camera
availability variants make the small network face Codex's measured occlusion,
stale-ball, and blocked-player states. The script prints metrics and verifies
that training reproduces the frozen pure-Python weights used at match time.
"""

import argparse
import json
import math
import random
import sys
from pathlib import Path

import torch


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import team  # noqa: E402


FROZEN_CLUBS = {
    "Real Machina",
    "Singularity United",
    "Dynamo Datacenter",
    "Synthetic Athletic",
}
HOLDOUT_FIXTURES = {10, 15, 17}
HORIZON = 3
FEATURE_COUNT = 19
MASK_MODES = range(6)


def distance(first, second):
    return math.hypot(first[0] - second[0], first[1] - second[1])


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def feature_vector(row, previous, player, side, mask_mode):
    sign = 1.0 if side == 0 else -1.0
    own = row["robots"][player]
    mate = row["robots"][side * 2 + (1 - (player % 2))]
    opponents = row["robots"][2:4] if side == 0 else row["robots"][0:2]
    ball = row["ball"]
    velocity_x = sign * (ball[0] - previous["ball"][0])
    velocity_y = ball[1] - previous["ball"][1]
    teammate_visible = mask_mode in (0, 3)
    opponent_count = (2, 1, 0, 0, 0, 0)[mask_mode]

    if teammate_visible:
        mate_x = sign * (mate[0] - ball[0]) / 7.0
        mate_y = (mate[1] - ball[1]) / 4.5
        mate_distance = distance(mate, ball) / 8.0
    else:
        mate_x = mate_y = mate_distance = 0.0

    if opponent_count:
        visible = sorted(opponents, key=lambda item: distance(item, ball))[
            :opponent_count]
        opponent_distance = min(distance(item, ball) for item in visible) / 8.0
    else:
        opponent_distance = 0.0

    score_diff = (row["score"][side] - row["score"][1 - side]) / 5.0
    return [
        sign * ball[0] / 7.0,
        ball[1] / 4.5,
        max(-1.5, min(1.5, velocity_x / 2.0)),
        max(-1.5, min(1.5, velocity_y / 2.0)),
        sign * (own[0] - ball[0]) / 7.0,
        (own[1] - ball[1]) / 4.5,
        distance(own, ball) / 8.0,
        1.0 if teammate_visible else 0.0,
        mate_x,
        mate_y,
        mate_distance,
        opponent_count / 2.0,
        opponent_distance,
        max(-2.0, min(2.0, score_diff)),
        max(0.0, min(1.0, (600.0 - row["t"]) / 600.0)),
        0.0 if mask_mode == 4 else 1.0,
        0.8 if mask_mode == 4 else 0.0,
        1.0 if abs(ball[0]) > 6.35 or abs(ball[1]) > 3.85 else 0.0,
        1.0 if mask_mode == 5 else 0.0,
    ]


def demonstrated_role(rows, index, player, side, touches):
    row = rows[index]
    future = rows[index + HORIZON]
    if row["score"] != future["score"]:
        return None

    own = row["robots"][player]
    future_own = future["robots"][player]
    ball = row["ball"]
    future_ball = future["ball"]
    if distance(own, future_own) > 3.2:
        return None  # reject fall/restart discontinuities

    sign = 1.0 if side == 0 else -1.0
    progress = sign * ball[0]
    upcoming = [who for time, who in touches
                if row["t"] <= time <= future["t"] + 1.0]
    if player in upcoming:
        return team.PRESS

    mate_id = side * 2 + (1 - (player % 2))
    if mate_id in upcoming:
        return team.SCREEN if progress < -1.5 else team.SUPPORT

    now_distance = distance(own, ball)
    future_distance = distance(future_own, future_ball)
    own_goal = [-7.0, 0.0] if side == 0 else [7.0, 0.0]
    goal_gain = distance(own, own_goal) - distance(future_own, own_goal)
    if now_distance <= 1.35 or now_distance - future_distance > 0.35:
        return team.PRESS
    if progress < -0.8 and goal_gain > 0.2:
        return team.SCREEN
    return team.SUPPORT


def build_dataset(season_root):
    train = []
    validation = []
    sources = []
    for match_file in sorted(season_root.glob("m*/match.json")):
        fixture = int(match_file.parent.name.split("_")[0][1:])
        match = json.loads(match_file.read_text())
        names = [match["teams"]["A"]["name"], match["teams"]["B"]["name"]]
        score = match["score"]
        rows = load_jsonl(match_file.parent / "telemetry.jsonl")
        touches = [(event["t"], event["who"])
                   for event in match["events"] if event["kind"] == "touch"]
        for side, name in enumerate(names):
            if name not in FROZEN_CLUBS or score[side] < score[1 - side]:
                continue
            target = validation if fixture in HOLDOUT_FIXTURES else train
            for index in range(1, len(rows) - HORIZON):
                for player in (side * 2, side * 2 + 1):
                    label = demonstrated_role(rows, index, player, side, touches)
                    if label is None:
                        continue
                    progress = (1.0 if side == 0 else -1.0) * rows[index]["ball"][0]
                    for mask_mode in MASK_MODES:
                        augmented_label = label
                        if mask_mode in (4, 5):
                            augmented_label = (team.SCREEN if progress < 0.0
                                               else team.SUPPORT)
                        target.append((feature_vector(
                            rows[index], rows[index - 1], player, side, mask_mode),
                            augmented_label))
            sources.append((fixture, name,
                            "validation" if fixture in HOLDOUT_FIXTURES else "train"))
    return train, validation, sources


def confusion(truth, predictions):
    result = torch.zeros(3, 3, dtype=torch.int64)
    for actual, predicted in zip(truth, predictions):
        result[actual, predicted] += 1
    return result


def maximum_frozen_delta(model):
    expected = (team.ROLE_W1, team.ROLE_B1, team.ROLE_W2, team.ROLE_B2)
    maximum = 0.0
    for parameter, frozen in zip(model.parameters(), expected):
        actual = parameter.detach().flatten().tolist()
        wanted = torch.tensor(frozen, dtype=torch.float32).flatten().tolist()
        maximum = max(maximum, *(abs(a - b) for a, b in zip(actual, wanted)))
    return maximum


def main():
    default_root = Path(__file__).resolve().parents[2] / "rfl-league-data/seasons/s2"
    parser = argparse.ArgumentParser()
    parser.add_argument("season_root", type=Path, nargs="?", default=default_root)
    parser.add_argument("--epochs", type=int, default=301)
    args = parser.parse_args()

    torch.manual_seed(7)
    random.seed(7)
    train, validation, sources = build_dataset(args.season_root)
    print("sources:", sources)
    for name, samples in (("train", train), ("validation", validation)):
        counts = [sum(label == role for _, label in samples) for role in range(3)]
        print(f"{name}: {len(samples)} samples, classes {counts}")

    train_x = torch.tensor([item for item, _ in train], dtype=torch.float32)
    train_y = torch.tensor([label for _, label in train], dtype=torch.long)
    validation_x = torch.tensor(
        [item for item, _ in validation], dtype=torch.float32)
    validation_y = torch.tensor(
        [label for _, label in validation], dtype=torch.long)
    model = torch.nn.Sequential(
        torch.nn.Linear(FEATURE_COUNT, 8),
        torch.nn.Tanh(),
        torch.nn.Linear(8, 3),
    )
    class_weights = torch.tensor([1.0, 1.05, 1.15])
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.012, weight_decay=0.002)
    for _ in range(args.epochs):
        optimizer.zero_grad()
        loss = torch.nn.functional.cross_entropy(
            model(train_x), train_y, weight=class_weights)
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        train_predictions = model(train_x).argmax(1)
        validation_predictions = model(validation_x).argmax(1)
    train_accuracy = (train_predictions == train_y).float().mean().item()
    validation_accuracy = (
        (validation_predictions == validation_y).float().mean().item())
    matrix = confusion(validation_y, validation_predictions)
    delta = maximum_frozen_delta(model)
    print(f"loss: {loss.item():.6f}")
    print(f"accuracy: train {train_accuracy:.3%}, validation {validation_accuracy:.3%}")
    print("validation confusion [actual][predicted]:", matrix.tolist())
    print(f"maximum frozen-weight delta: {delta:.9f}")
    if args.epochs == 301 and delta > 5e-6:
        raise SystemExit("training no longer reproduces the policy in team.py")


if __name__ == "__main__":
    main()
