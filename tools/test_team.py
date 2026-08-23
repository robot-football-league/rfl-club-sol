#!/usr/bin/env python3
"""Small contract regressions for the Codex City match controller."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import team  # noqa: E402


def danger_observation(attack_x, number):
    sign = 1.0 if attack_x > 0.0 else -1.0
    defend_x = -attack_x
    ball_x = defend_x + sign * 0.7
    # Deliberately put the robot attack-side of a ball by its own goal. The
    # SDK skill—not club-level retreat code—must perform the safe orbit.
    player_x = ball_x + sign * 0.6
    return {
        "time_remaining_s": 300.0,
        "you": {
            "number": number,
            "attack_goal_xy": [attack_x, 0.0],
            "defend_goal_xy": [attack_x, 0.0],  # live home-coordinate quirk
        },
        "score": {"you": 0, "them": 0},
        "self": {
            "field_xy": [player_x, 0.2],
            "fallen": False,
            "blocked": False,
        },
        "detections": {
            "ball": {
                "field_xy": [ball_x, 0.0],
                "distance_m": 0.65,
                "against_wall": False,
                "velocity_mps": [0.0, 0.0],
                "speed_mps": 0.0,
            },
            "teammates": [],
            "opponents": [],
        },
    }


def main():
    for attack_x, base in ((7.0, 0), (-7.0, 2)):
        for offset in (0, 1):
            player = team.CodexPlayer(base + offset)
            reply = player.decide(danger_observation(attack_x, offset + 1))
            assert reply["skill"] == "kick_toward", reply
            assert reply["target"][0] == attack_x, reply
    print("home/away two-player danger counterpress: clear")


if __name__ == "__main__":
    main()
