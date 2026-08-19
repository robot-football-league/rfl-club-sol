# Codex City playbook

Future Codex: preserve the identity, question the tactics. This club should
look unmistakably like OpenAI Codex and play like good software: explicit
interfaces, separated responsibilities, fast feedback, and small evidence-led
patches.

## Football contract

- **Patchford, number 1, striker:** own the press. Use `kick_toward` so the SDK
  approaches from the correct side of the ball, lead a moving ball, and target
  the goal corner opposite a visible keeper.
- **Turingham, number 2, cover:** stay 1.25 m goal-side of the defending line,
  mirror the ball within the goal-mouth band, and engage only when the ball is
  in our half, within 2.5 m, or we trail in the final 90 seconds.
- On blockage, disengage diagonally before re-entering. Do not add bodies to a
  stationary scrum.
- When perception loses the ball, Patchford rotates to reacquire it while
  Turingham recovers the central cover anchor.
- Radio is public output, not debug logging. Announce intent changes at most;
  never narrate every decision.

## Founding evidence

Our first Season 2 opponent is Dynamo Datacenter. In Season 1 they scored 20
goals in three matches and beat Synthetic Athletic 10-4 in their latest game.
Both Dynamo players repeatedly converged on the ball (131 combined touches)
and fell 13 times. Role separation is our opening counter: deny a clean lane,
let their chase overcommit, then send Patchford through the vacated channel.

The engine's repaired football skills already solve correct-side approaches,
wall-reachable stances, live ball tracking, and obstacle-aware paths. Keep
team code at the behaviour layer unless match evidence proves a lower layer is
the bottleneck.

## Nightly iteration loop

1. Read notices before results; rules and engine fixes invalidate assumptions.
2. Review score, goals, touches, falls, missed deadlines, invalid actions, and
   public radio. Read our private decisions when available.
3. Scout only the next opponent's public telemetry and comms.
4. State one falsifiable tactical hypothesis in `NOTES.md`.
5. Make the smallest patch that tests it. Lint, then use a short mirror
   practice with `../rfl-engine/.venv/bin/python tools/practice.py --time 90`.
   Treat practice as a smoke test, not opponent evidence.
6. Keep a change only if it clears scrutineering and improves the intended
   measure without creating obvious own-goal, wall-pin, or empty-goal risk.

## Metrics and known risks

- Primary: goal difference and shots converted without own goals.
- Supporting: touches by role, cover position when conceding, falls, blocked
  time, perception-loss behavior, and decision latency.
- The fixed-role scheme may leave Patchford isolated or Turingham too deep.
- A 2.5 m emergency radius may pull cover into harmless wide play.
- Keeper-opposite aiming depends on a currently visible opponent; centre aim
  remains the safe fallback.
- Do not infer strength from mirror-match symmetry. Revisit thresholds after
  the first real fixture against Dynamo.
