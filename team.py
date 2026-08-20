"""Codex City: rotating pressure with a deterministic safety kernel.

Round 1 showed that permanent striker/cover roles stretched the side to 5.21 m
average separation in the second half and left one robot defending alone. Both
players now run the same perception-bound controller: nearest player presses,
the other forms a close goal-side outlet, and roles rotate with the ball.

The final layer is non-negotiable. A player on the attack side of a ball near
its own goal may not drive through it. It first moves laterally, then recovers
goal-side. This directly addresses the 573 s Round 1 own goal.
"""


PITCH_X = 7.0
PITCH_Y = 4.5
GOAL_TARGET_Y = 1.08
GOAL_SIDE_OFFSET = 0.85
SUPPORT_TRAIL = 1.45
SUPPORT_WIDTH = 1.05
OWN_DANGER_DEPTH = 3.1


def _clamp(value, low, high):
    return max(low, min(high, value))


def _distance(a, b):
    return ((float(a[0]) - float(b[0])) ** 2
            + (float(a[1]) - float(b[1])) ** 2) ** 0.5


class CodexPlayer:
    """Symmetric rotating player using only published SDK observations."""

    def __init__(self, index):
        self.index = index
        self.slot = index % 2
        self.name = "codex-city-rotating-press"
        self.begin_episode()

    def begin_episode(self, log_dir=None):
        self._tick = 0
        self._last_radio_tick = -99
        self._last_announced_intent = None

    def _announce(self, reply, intent, message):
        if (intent != self._last_announced_intent
                and self._tick - self._last_radio_tick >= 7):
            reply["say"] = message
            self._last_announced_intent = intent
            self._last_radio_tick = self._tick
        return reply

    @staticmethod
    def _geometry(obs):
        attack_x = float(obs["you"]["attack_goal_xy"][0])
        # rfl-0.3 currently reports the home player's defend_goal_xy as the
        # same +7 coordinate as attack_goal_xy. The pitch is symmetric and
        # attack_goal_xy itself is correct, so derive direction and the
        # opposite pocket from that stable fact instead of trusting ordering.
        attack_sign = 1.0 if attack_x >= 0.0 else -1.0
        defend_x = -attack_x
        return attack_x, defend_x, attack_sign

    @staticmethod
    def _shot_target(ball, opponents, attack_x):
        """Finish away from a visible keeper; otherwise trust the centre."""
        bx, _ = ball["field_xy"]
        if abs(attack_x - float(bx)) > 3.25:
            return [attack_x, 0.0]
        keepers = []
        for opponent in opponents:
            ox, oy = opponent.get("field_xy", [0.0, 0.0])
            if abs(attack_x - float(ox)) < 2.2:
                keepers.append((abs(attack_x - float(ox)), float(oy)))
        if not keepers:
            return [attack_x, 0.0]
        keeper_y = min(keepers)[1]
        return [attack_x, -GOAL_TARGET_Y if keeper_y >= 0.0
                else GOAL_TARGET_Y]

    def _is_primary(self, ball, teammates, progress):
        """Rotate first pressure to the nearer visible player.

        When the teammate is occluded, number 1 keeps the default claim while
        number 2 may take over a nearby ball in our half. This avoids two blind
        claims without leaving a defensive emergency unattended.
        """
        my_distance = float(ball.get("distance_m", 99.0))
        if teammates:
            bx, by = ball["field_xy"]
            mate_distance = min(
                _distance(mate.get("field_xy", [99.0, 99.0]), [bx, by])
                for mate in teammates
            )
            if my_distance + 0.3 < mate_distance:
                return True
            if mate_distance + 0.3 < my_distance:
                return False
            return self.slot == 0
        return self.slot == 0 or (progress < -0.4 and my_distance < 2.6)

    @staticmethod
    def _ball_future(ball):
        bx, by = (float(v) for v in ball["field_xy"])
        vx, vy = (float(v) for v in ball.get("velocity_mps", [0.0, 0.0]))
        horizon = 0.75 if float(ball.get("speed_mps", 0.0)) > 0.35 else 0.0
        return (
            _clamp(bx + vx * horizon, -PITCH_X + 0.45, PITCH_X - 0.45),
            _clamp(by + vy * horizon, -PITCH_Y + 0.45, PITCH_Y - 0.45),
        )

    def _wrong_side_danger(self, px, bx, attack_sign, own_depth):
        return own_depth < OWN_DANGER_DEPTH and attack_sign * (px - bx) > 0.12

    def _recover_goal_side(self, obs, ball, attack_sign):
        """Two-stage route around a dangerous ball, never through it."""
        px, py = (float(v) for v in obs["self"]["field_xy"])
        bx, by = (float(v) for v in ball["field_xy"])
        lateral = py - by
        if abs(lateral) < 0.95:
            if abs(by) > 0.3:
                side = -1.0 if by > 0.0 else 1.0  # escape toward centre
            else:
                side = 1.0 if self.slot == 0 else -1.0
            target = [px, _clamp(by + side * 1.35,
                                 -PITCH_Y + 0.55, PITCH_Y - 0.55)]
            return self._announce(
                {"skill": "walk_to", "target": target},
                "safety_lateral",
                "Wrong side of danger; taking the lateral route.",
            )

        side = 1.0 if lateral > 0.0 else -1.0
        target = [
            _clamp(bx - attack_sign * GOAL_SIDE_OFFSET,
                   -PITCH_X + 0.25, PITCH_X - 0.25),
            _clamp(by + side * 0.62, -PITCH_Y + 0.5, PITCH_Y - 0.5),
        ]
        return self._announce(
            {"skill": "walk_to", "target": target},
            "safety_recover",
            "Routing goal-side before any clearance.",
        )

    def _break_scrum(self, obs, ball, attack_sign):
        px, py = (float(v) for v in obs["self"]["field_xy"])
        _, by = (float(v) for v in ball["field_xy"])
        if abs(by) > 3.25:
            side = -1.0 if by > 0.0 else 1.0
        else:
            side = 1.0 if self.slot == 0 else -1.0
        target = [
            _clamp(px - attack_sign * 0.6, -PITCH_X + 0.55, PITCH_X - 0.55),
            _clamp(py + side * 0.9, -PITCH_Y + 0.55, PITCH_Y - 0.55),
        ]
        return self._announce(
            {"skill": "walk_to", "target": target},
            "disengage",
            "Releasing the collision; rotate onto the loose ball.",
        )

    def _press(self, obs, ball, opponents, attack_x, defend_x, attack_sign):
        px, _ = (float(v) for v in obs["self"]["field_xy"])
        bx, _ = (float(v) for v in ball["field_xy"])
        own_depth = attack_sign * (bx - defend_x)
        if self._wrong_side_danger(px, bx, attack_sign, own_depth):
            return self._recover_goal_side(obs, ball, attack_sign)
        if obs["self"].get("blocked"):
            return self._break_scrum(obs, ball, attack_sign)

        wall = bool(ball.get("against_wall"))
        _, by = (float(v) for v in ball["field_xy"])
        if wall and abs(by) > 3.0:
            # A centre-goal target asks for an unreachable stance behind a
            # side-wall ball. The near-post channel preserves forward motion
            # while peeling it off the boards.
            target = [attack_x, GOAL_TARGET_Y if by > 0.0
                      else -GOAL_TARGET_Y]
        else:
            target = self._shot_target(ball, opponents, attack_x)
        speed = float(ball.get("speed_mps", 0.0))
        lead = 0.8 if speed > 0.65 else (0.45 if speed > 0.35 else 0.0)
        return self._announce(
            {"skill": "kick_toward", "target": target, "lead_s": lead},
            "wall_press" if wall else "first_press",
            ("First pressure on the wall; hold the central outlet."
             if wall else "First pressure; rotate into the goal-side outlet."),
        )

    def _support(self, obs, ball, attack_x, defend_x, attack_sign,
                 progress, leading_late):
        px, py = (float(v) for v in obs["self"]["field_xy"])
        bx, by = (float(v) for v in ball["field_xy"])
        own_depth = attack_sign * (bx - defend_x)
        if self._wrong_side_danger(px, bx, attack_sign, own_depth):
            return self._recover_goal_side(obs, ball, attack_sign)
        if obs["self"].get("blocked"):
            return self._break_scrum(obs, ball, attack_sign)

        # When protecting a late lead, retain a real last player instead of
        # allowing a nominal cover player to be dragged into the same scrum.
        if leading_late and progress < 2.8:
            screen = [defend_x + attack_sign * 1.35,
                      _clamp(by, -1.15, 1.15)]
            return self._announce(
                {"skill": "walk_to", "target": screen},
                "close_game",
                "Lead protected; I am the central last player.",
            )

        # Winners overloaded the final third. Join there, but never add a
        # second body to a wall pin where a central outlet is more valuable.
        my_distance = float(ball.get("distance_m", 99.0))
        if progress > 3.25 and my_distance < 3.2 and not ball.get("against_wall"):
            target = self._shot_target(ball, [], attack_x)
            return self._announce(
                {"skill": "kick_toward", "target": target,
                 "lead_s": 0.35 if float(ball.get("speed_mps", 0.0)) > 0.5
                 else 0.0},
                "overload",
                "Final-third overload; both channels are live.",
            )

        fx, fy = self._ball_future(ball)
        if ball.get("against_wall") and abs(by) > 3.15:
            side = -1.0 if by > 0.0 else 1.0
            support_y = _clamp(by + side * 1.45, -3.3, 3.3)
        else:
            side = -1.0 if fy > 0.0 else 1.0
            if abs(fy) < 0.35:
                side = 1.0 if self.slot == 0 else -1.0
            support_y = _clamp(fy + side * SUPPORT_WIDTH, -3.35, 3.35)
        support_x = _clamp(fx - attack_sign * SUPPORT_TRAIL,
                           -PITCH_X + 0.65, PITCH_X - 0.65)

        # Deep in our half, the support point must remain between ball and net.
        if own_depth < 2.5:
            support_x = _clamp(bx - attack_sign * 1.05,
                               -PITCH_X + 0.55, PITCH_X - 0.55)
            support_y = _clamp(by, -1.35, 1.35)

        target = [support_x, support_y]
        if _distance([px, py], target) < 0.4:
            return self._announce(
                {"skill": "turn_to", "target": [bx, by]},
                "outlet_set",
                "Outlet set; ready for the next phase.",
            )
        return self._announce(
            {"skill": "walk_to", "target": target},
            "wall_outlet" if ball.get("against_wall") else "rotate_support",
            ("Central outlet set; do not double the wall."
             if ball.get("against_wall")
             else "Rotating close and goal-side of first pressure."),
        )

    def _lost_ball(self, obs, defend_x, attack_sign):
        px, py = (float(v) for v in obs["self"]["field_xy"])
        if self.slot == 0:
            return self._announce(
                {"vx": 0.0, "vy": 0.0, "wz": 0.7},
                "scan",
                "Ball index expired; sweeping now.",
            )
        search = [defend_x + attack_sign * 3.0, 0.0]
        if _distance([px, py], search) < 0.45:
            return self._announce(
                {"skill": "turn_to", "target": [0.0, 0.0]},
                "search_set",
                "Search screen set behind the sweep.",
            )
        return self._announce(
            {"skill": "walk_to", "target": search},
            "search_recover",
            "Recovering the midfield search screen.",
        )

    def decide(self, obs):
        self._tick += 1
        if obs["self"].get("fallen"):
            return {"skill": "hold"}

        attack_x, defend_x, attack_sign = self._geometry(obs)
        detections = obs.get("detections") or {}
        ball = detections.get("ball")
        if ball is None:
            return self._lost_ball(obs, defend_x, attack_sign)

        bx, _ = (float(v) for v in ball["field_xy"])
        progress = attack_sign * bx
        teammates = detections.get("teammates") or []
        opponents = detections.get("opponents") or []
        score = obs.get("score") or {}
        leading = int(score.get("you", 0)) > int(score.get("them", 0))
        leading_late = leading and float(obs.get("time_remaining_s", 999.0)) <= 75.0

        if self._is_primary(ball, teammates, progress):
            return self._press(obs, ball, opponents, attack_x,
                               defend_x, attack_sign)
        return self._support(obs, ball, attack_x, defend_x, attack_sign,
                             progress, leading_late)


def build_team(ctx):
    base = int(ctx["team_index"]) * 2
    players = [CodexPlayer(base + offset) for offset in range(2)]
    return {"players": players, "manager": None}
