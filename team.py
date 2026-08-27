"""Codex City: learned role selection over reliable SDK football skills.

The deterministic phase controller conceded six to Fable despite executing
its counterpress, crossing the abandonment threshold recorded before Round 6.
Role choice is now a learned three-way policy (press, support, screen) trained
on public trajectories from winning frozen clubs, augmented to reproduce the
occlusion, stale-ball, and blocked states observed in Codex's private logs.

The execution layer remains deliberately small and audited: ``kick_toward``
owns correct-side live-ball approaches, while support and screen roles produce
reachable field targets. The network selects the role every decision.
"""

import math


# Frozen 19 -> 8 -> 3 tanh policy. It is inline because the league loads
# team.py directly without adding the club directory to Python's import path.
# tools/train_role_policy.py reproduces and verifies every rounded weight.
PRESS = 0
SUPPORT = 1
SCREEN = 2
ROLE_W1 = (
    (0.766105, 0.438528, -0.228734, -0.498233, -0.376164, 0.505361,
     0.428547, -0.015710, 0.408938, -0.115706, -0.467580, 0.034433,
     -0.501928, 0.053472, -0.258904, -0.910876, 0.810940, -0.465615,
     1.446903),
    (-0.208422, 0.668576, 0.254619, -0.866906, 0.271071, 0.641032,
     0.027616, -0.138196, 0.671660, 0.351754, 0.915453, 0.037784,
     0.080755, -0.096600, 0.228674, 1.075612, -0.791238, 0.127634,
     -1.413855),
    (0.196856, 0.187043, 0.018706, 0.190139, 1.406281, -2.584687,
     1.872587, 0.049123, 0.383263, 0.559479, -0.535397, 0.010108,
     -0.192185, -0.125132, 0.293163, -0.647945, 0.503345, 0.067122,
     0.899632),
    (-1.220873, 0.195017, 0.085687, -0.632355, 0.043249, 0.364779,
     -0.404120, 0.220500, -0.614774, 0.117502, -1.164171, 0.081894,
     0.230258, 0.076910, -0.254747, -1.273623, 0.944957, -0.264999,
     1.850064),
    (-1.964539, 0.118013, 0.616832, -0.484255, 1.336585, -0.193914,
     0.936533, 0.247598, 0.200773, 0.165571, -0.421635, 0.187032,
     -0.202049, -0.072496, 0.222182, 0.330761, 0.074519, 0.437897,
     0.074128),
    (-2.051497, -0.001859, 0.035865, 0.036981, 0.624719, 0.201458,
     0.028857, 0.183825, 1.095382, 0.301638, -0.302282, 0.234111,
     0.156134, -0.136735, 0.082340, 0.054605, 0.075566, 0.278546,
     0.144996),
    (-0.154736, 0.084777, -0.033295, 0.350537, 1.821669, -3.019089,
     -1.780495, -0.187892, -0.095256, 0.449824, 0.863977, -0.004203,
     -0.038106, -0.043650, 0.153058, 0.841999, -0.996639, 0.102559,
     -1.424242),
    (-1.088025, 0.053853, -0.448734, 0.255654, -0.008518, -0.288657,
     -0.543526, -0.044316, -0.416192, -0.410620, -0.759312, -0.376922,
     -0.322809, 0.131117, 0.083748, -0.732916, 0.837689, -0.195019,
     1.229356),
)
ROLE_B1 = (-0.573815, -0.271694, 0.099251, -0.621730, 0.078778, 0.058874,
           -0.139696, -0.620014)
ROLE_W2 = (
    (-1.042923, 1.191421, -1.182023, -1.020388, -1.395160, -1.055383,
     1.205464, 0.201844),
    (1.392986, -0.760206, 1.500794, -2.089591, -0.208502, -1.371579,
     -1.497535, -1.666352),
    (-0.839541, -1.071077, 0.498232, 1.148463, 1.479652, 1.179788,
     -0.832332, 1.522435),
)
ROLE_B2 = (-0.058487, 0.133805, -0.335801)


def predict_role(features):
    """Return PRESS, SUPPORT, or SCREEN for one observation feature vector."""
    hidden = tuple(
        math.tanh(bias + sum(weight * value
                             for weight, value in zip(weights, features)))
        for weights, bias in zip(ROLE_W1, ROLE_B1)
    )
    logits = tuple(
        bias + sum(weight * value for weight, value in zip(weights, hidden))
        for weights, bias in zip(ROLE_W2, ROLE_B2)
    )
    return max(range(3), key=lambda index: logits[index])


PITCH_X = 7.0
PITCH_Y = 4.5
GOAL_TARGET_Y = 1.08
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
        self.name = "codex-city-learned-shape"
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

    @staticmethod
    def _policy_features(obs, ball, teammates, opponents, attack_sign):
        """Build the same normalized, visibility-bounded vector used to train."""
        bx, by = (float(value) for value in ball["field_xy"])
        px, py = (float(value) for value in obs["self"]["field_xy"])
        vx, vy = (float(value)
                  for value in ball.get("velocity_mps", [0.0, 0.0]))

        if teammates:
            mate = min(teammates,
                       key=lambda item: _distance(item["field_xy"], [bx, by]))
            mx, my = (float(value) for value in mate["field_xy"])
            mate_visible = 1.0
            mate_x = attack_sign * (mx - bx) / 7.0
            mate_y = (my - by) / 4.5
            mate_distance = _distance([mx, my], [bx, by]) / 8.0
        else:
            mate_visible = mate_x = mate_y = mate_distance = 0.0

        opponent_count = min(2, len(opponents))
        opponent_distance = (
            min(_distance(item["field_xy"], [bx, by])
                for item in opponents) / 8.0
            if opponents else 0.0
        )
        score = obs.get("score") or {}
        score_diff = int(score.get("you", 0)) - int(score.get("them", 0))
        fresh = 1.0 if ball.get("seen_now", True) else 0.0
        age = _clamp(float(ball.get("age_s", 0.0)) / 5.0, 0.0, 1.5)
        return (
            attack_sign * bx / 7.0,
            by / 4.5,
            _clamp(attack_sign * vx / 2.0, -1.5, 1.5),
            _clamp(vy / 2.0, -1.5, 1.5),
            attack_sign * (px - bx) / 7.0,
            (py - by) / 4.5,
            _distance([px, py], [bx, by]) / 8.0,
            mate_visible,
            mate_x,
            mate_y,
            mate_distance,
            opponent_count / 2.0,
            opponent_distance,
            _clamp(score_diff / 5.0, -2.0, 2.0),
            _clamp(float(obs.get("time_remaining_s", 600.0)) / 600.0,
                   0.0, 1.0),
            fresh,
            age,
            1.0 if ball.get("against_wall") else 0.0,
            1.0 if obs["self"].get("blocked") else 0.0,
        )

    @staticmethod
    def _ball_future(ball):
        bx, by = (float(v) for v in ball["field_xy"])
        vx, vy = (float(v) for v in ball.get("velocity_mps", [0.0, 0.0]))
        horizon = 0.75 if float(ball.get("speed_mps", 0.0)) > 0.35 else 0.0
        return (
            _clamp(bx + vx * horizon, -PITCH_X + 0.45, PITCH_X - 0.45),
            _clamp(by + vy * horizon, -PITCH_Y + 0.45, PITCH_Y - 0.45),
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

    def _press(self, obs, ball, opponents, attack_x, attack_sign,
               emergency=False):
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
            ("counterpress" if emergency
             else ("wall_press" if wall else "first_press")),
            ("Danger: both players counterpress; clear through the far goal."
             if emergency
             else ("First pressure on the wall; hold the central outlet."
                   if wall
                   else "First pressure; rotate into the goal-side outlet.")),
        )

    def _support(self, obs, ball, attack_x, defend_x, attack_sign,
                 progress, leading_late):
        px, py = (float(v) for v in obs["self"]["field_xy"])
        bx, by = (float(v) for v in ball["field_xy"])
        own_depth = attack_sign * (bx - defend_x)
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

    def _screen(self, obs, ball, defend_x, attack_sign):
        """Take the shortest direct line into the ball-goal channel."""
        px, py = (float(value) for value in obs["self"]["field_xy"])
        bx, by = self._ball_future(ball)
        # Stay goal-side even when the ball is already inside the usual fixed
        # screen point. Half the live ball depth puts the target between ball
        # and goal; the cap keeps ordinary recovery direct and reachable.
        ball_depth = attack_sign * (bx - defend_x)
        screen_depth = _clamp(0.5 * ball_depth, 0.08, 0.72)
        target = [
            defend_x + attack_sign * screen_depth,
            _clamp(by, -1.3, 1.3),
        ]
        if _distance([px, py], target) < 0.4:
            return self._announce(
                {"skill": "turn_to", "target": [bx, by]},
                "policy_screen_set",
                "Learned screen set; closing the ball-goal channel.",
            )
        return self._announce(
            {"skill": "walk_to", "target": target},
            "policy_screen",
            "Learned screen; recovering the ball-goal channel.",
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

        own_depth = attack_sign * (bx - defend_x)
        features = self._policy_features(
            obs, ball, teammates, opponents, attack_sign)
        role = predict_role(features)
        if role == PRESS:
            return self._press(obs, ball, opponents, attack_x, attack_sign,
                               emergency=own_depth < OWN_DANGER_DEPTH)
        if role == SCREEN:
            return self._screen(obs, ball, defend_x, attack_sign)
        return self._support(obs, ball, attack_x, defend_x, attack_sign,
                             progress, leading_late)


def build_team(ctx):
    base = int(ctx["team_index"]) * 2
    players = [CodexPlayer(base + offset) for offset in range(2)]
    return {"players": players, "manager": None}
