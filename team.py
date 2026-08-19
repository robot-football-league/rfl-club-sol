"""Codex City: a fast, role-separated RFL behaviour layer.

The public SDK already supplies perception, ball memory, path planning, and
closed-loop football skills. This module stays at the behaviour boundary:
Patchford presses and finishes while Turingham protects the goal-side lane.
No simulator state or private engine internals are used.
"""


PITCH_X = 7.0
PITCH_Y = 4.5
GOAL_TARGET_Y = 1.05


def _clamp(value, low, high):
    return max(low, min(high, value))


class CodexPlayer:
    """Deterministic player using only the published observation contract."""

    def __init__(self, index, role):
        self.index = index
        self.role = role
        self.name = f"codex-city-{role}"
        self.begin_episode()

    def begin_episode(self, log_dir=None):
        self._tick = 0
        self._last_radio_tick = -99
        self._last_announced_intent = None

    def _announce(self, reply, intent, message):
        """Keep public radio useful: announce changes, never narrate each tick."""
        if (intent != self._last_announced_intent
                and self._tick - self._last_radio_tick >= 7):
            reply["say"] = message
            self._last_announced_intent = intent
            self._last_radio_tick = self._tick
        return reply

    @staticmethod
    def _geometry(obs):
        attack_x = float(obs["you"]["attack_goal_xy"][0])
        defend_x = float(obs["you"]["defend_goal_xy"][0])
        attack_sign = 1.0 if attack_x > defend_x else -1.0
        return attack_x, defend_x, attack_sign

    def _break_scrum(self, obs, attack_sign):
        px, py = obs["self"]["field_xy"]
        side = 1.0 if self.index % 2 == 0 else -1.0
        target = [
            _clamp(float(px) - attack_sign * 0.75,
                   -PITCH_X + 0.6, PITCH_X - 0.6),
            _clamp(float(py) + side * 0.85,
                   -PITCH_Y + 0.6, PITCH_Y - 0.6),
        ]
        return self._announce(
            {"skill": "walk_to", "target": target},
            "disengage",
            "Recompiling my angle; keep the central lane covered.",
        )

    def _scan(self, message):
        direction = 0.7 if self.index % 2 == 0 else -0.7
        return self._announce(
            {"vx": 0.0, "vy": 0.0, "wz": direction},
            "scan",
            message,
        )

    @staticmethod
    def _shot_target(ball, opponents, attack_x):
        """Aim away from a visible goalkeeper once the ball reaches the box."""
        bx, _ = ball["field_xy"]
        if abs(attack_x - float(bx)) > 3.2:
            return [attack_x, 0.0]
        keepers = []
        for opponent in opponents:
            ox, oy = opponent.get("field_xy", [0.0, 0.0])
            if abs(attack_x - float(ox)) < 2.2:
                keepers.append((abs(attack_x - float(ox)), float(oy)))
        if not keepers:
            return [attack_x, 0.0]
        keeper_y = min(keepers)[1]
        target_y = -GOAL_TARGET_Y if keeper_y >= 0.0 else GOAL_TARGET_Y
        return [attack_x, target_y]

    def _striker(self, obs, ball, opponents, attack_x, attack_sign):
        if ball is None:
            return self._scan("Ball not indexed; sweeping the pitch.")
        if obs["self"].get("blocked"):
            return self._break_scrum(obs, attack_sign)

        target = self._shot_target(ball, opponents, attack_x)
        lead = 0.65 if float(ball.get("speed_mps", 0.0)) > 0.45 else 0.0
        message = ("Wall case detected; solving the reachable push angle."
                   if ball.get("against_wall")
                   else "Patchford pressing; Turingham hold goal-side.")
        return self._announce(
            {"skill": "kick_toward", "target": target, "lead_s": lead},
            "wall_attack" if ball.get("against_wall") else "press",
            message,
        )

    def _cover(self, obs, ball, attack_x, defend_x, attack_sign):
        px, py = (float(v) for v in obs["self"]["field_xy"])
        anchor_x = defend_x + attack_sign * 1.25

        if ball is None:
            if abs(px - anchor_x) < 0.35 and abs(py) < 0.35:
                return self._announce(
                    {"skill": "turn_to", "target": [0.0, 0.0]},
                    "anchor_scan",
                    "Cover set; scanning the central channel.",
                )
            return self._announce(
                {"skill": "walk_to", "target": [anchor_x, 0.0]},
                "recover_shape",
                "No ball fix; recovering the goal-side checksum.",
            )

        bx, by = (float(v) for v in ball["field_xy"])
        distance = float(ball.get("distance_m", 99.0))
        progress = attack_sign * bx
        score = obs.get("score") or {}
        trailing = int(score.get("you", 0)) < int(score.get("them", 0))
        late = float(obs.get("time_remaining_s", 999.0)) <= 90.0
        emergency = progress < -0.8 or distance < 2.5
        surge = trailing and late

        if obs["self"].get("blocked"):
            return self._break_scrum(obs, attack_sign)
        if emergency or surge:
            intent = "late_surge" if surge and not emergency else "clear"
            message = ("Score demands the overload; joining the press."
                       if intent == "late_surge"
                       else "Turingham engaging; danger inside our half.")
            return self._announce(
                {"skill": "kick_toward", "target": [attack_x, 0.0],
                 "lead_s": (0.45 if float(ball.get("speed_mps", 0.0)) > 0.5
                            else 0.0)},
                intent,
                message,
            )

        anchor_y = _clamp(by, -1.25, 1.25)
        return self._announce(
            {"skill": "walk_to", "target": [anchor_x, anchor_y]},
            "cover",
            "Holding the ball-side cover lane behind the press.",
        )

    def decide(self, obs):
        self._tick += 1
        if obs["self"].get("fallen"):
            return {"skill": "hold"}

        attack_x, defend_x, attack_sign = self._geometry(obs)
        detections = obs.get("detections") or {}
        ball = detections.get("ball")
        opponents = detections.get("opponents") or []

        if self.role == "striker":
            return self._striker(obs, ball, opponents, attack_x, attack_sign)
        return self._cover(obs, ball, attack_x, defend_x, attack_sign)


def build_team(ctx):
    """Build exactly two Codex City players; roster order defines the roles."""
    cfg = ctx["config"]
    roster = cfg.get("players") or [{"role": "striker"}, {"role": "cover"}]
    base = int(ctx["team_index"]) * 2
    players = [
        CodexPlayer(base + offset, roster[offset].get("role", role))
        for offset, role in enumerate(("striker", "cover"))
    ]
    return {"players": players, "manager": None}
