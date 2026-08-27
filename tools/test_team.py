#!/usr/bin/env python3
"""Contract regressions for Codex City's learned match controller."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import team  # noqa: E402


def danger_observation(attack_x, number, *, stale=False, blocked=False):
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
            "blocked": blocked,
        },
        "detections": {
            "ball": {
                "field_xy": [ball_x, 0.0],
                "distance_m": 0.65,
                "against_wall": False,
                "velocity_mps": [0.0, 0.0],
                "speed_mps": 0.0,
                "seen_now": not stale,
                "age_s": 4.0 if stale else 0.0,
            },
            "teammates": [],
            "opponents": [],
        },
    }


def main():
    assert len(team.ROLE_W1) == 8
    assert all(len(row) == 19 for row in team.ROLE_W1)
    assert len(team.ROLE_W2) == 3
    assert all(len(row) == 8 for row in team.ROLE_W2)

    # Fresh, mobile players close an own-goal danger immediately. This proves
    # the learned selector retains the attacking pressure that scored all four
    # Codex goals against Fable, in both engine coordinate orientations.
    for attack_x, base in ((7.0, 0), (-7.0, 2)):
        for offset in (0, 1):
            player = team.CodexPlayer(base + offset)
            reply = player.decide(danger_observation(attack_x, offset + 1))
            assert reply["skill"] == "kick_toward", reply
            assert reply["target"][0] == attack_x, reply

        # The trained occlusion and collision cases must recover the direct
        # central screen instead of blindly joining a two-player scrum. Screen
        # targets are on our side of the live ball in either orientation.
        defend_x = -attack_x
        sign = 1.0 if attack_x > 0.0 else -1.0
        ball_x = danger_observation(attack_x, 1)["detections"]["ball"]["field_xy"][0]
        expected_x = defend_x + sign * (0.5 * sign * (ball_x - defend_x))
        for stale, blocked in ((True, False), (False, True), (True, True)):
            player = team.CodexPlayer(base)
            reply = player.decide(danger_observation(
                attack_x, 1, stale=stale, blocked=blocked))
            assert reply["skill"] == "walk_to", reply
            assert abs(reply["target"][0] - expected_x) < 1e-9, reply

    print("learned roles, home/away orientation, and defensive screen: clear")


if __name__ == "__main__":
    main()
