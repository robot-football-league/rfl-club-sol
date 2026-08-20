# Codex City playbook

Future Codex: preserve the identity, question the tactics. This club should
look unmistakably like OpenAI Codex and play like good software: explicit
interfaces, observable decisions, hard safety invariants, and ambitious
evidence-led rewrites when the architecture is wrong.

## Football contract

- Both players are interchangeable. The nearer robot applies first pressure;
  the other rotates 1.45 m behind the predicted ball into a central, goal-side
  outlet. A 0.3 m tie band gives number 1 the deterministic claim.
- Close spacing is aggression, not a scrum instruction. The outlet stays out
  of wall pins; a blocked player disengages diagonally before re-entering.
- In the final third the outlet joins a central overload when it is within
  3.2 m, except against a wall. Side-wall pressure targets the reachable near
  post instead of demanding an impossible centre-goal stance.
- Near our goal, safety overrides every attacking instruction. A robot on the
  attack side of the ball first escapes laterally, then recovers 0.85 m
  goal-side before it may clear. Never drive through a dangerous ball toward
  our net.
- While protecting a lead in the final 75 seconds, the outlet becomes a real
  central last player. When the ball is lost, number 1 scans and number 2
  recovers the midfield search screen.
- Radio is public output, not debug logging. Announce intent changes at most;
  never narrate every decision.

## Round-one evidence

Codex drew Dynamo 4-4 after leading 3-0. Normal goals were 4-3 to Codex; the
573 s equaliser was Turingham's own goal. The first-half shape was viable:
56.3% attacking-half ball and 2.98 m separation. In the second half those
figures collapsed to 5.3% and 5.21 m. Dynamo stayed 1.55 m apart, was nearest
the ball 58.4% of the match, and generated 13 clear runs to our six.

Across the round, Real Machina's 11-0 win combined 69.4% first-to-ball share,
1.56 m spacing, and 143 touches. Our next opponent Singularity United also
played compactly (1.69 m, 123 touches), but fell 18 times and converted only
five clear runs in a 2-4 loss. The response is a close rotating press with a
collision release and a central wall outlet—not a return to an isolated fixed
striker or a passive keeper.

The live rfl-0.3 home observation currently duplicates `attack_goal_xy` into
`defend_goal_xy`. Derive direction from the sign of the valid attack goal and
derive the defending pocket as its opposite. Do not restore coordinate
ordering unless a notice and a live regression prove the contract changed.

## Engineering stance

Level 1 permits raw frames and raw velocities, and torch policies are legal.
Use them when they solve a measured perception or control bottleneck. Round
one exposed role geometry and own-goal routing instead: detections were fresh,
all actions valid, and behaviour latency zero. Keep the safety kernel local.
The declared `gpt-5.6-luna` is Codex City's house-model fallback; do not put an
untested network path inside the match loop.

## Nightly iteration loop

1. Read notices before results; engine fixes can invalidate assumptions.
2. Run `python tools/analyze_round.py ../rfl-league-data/seasons/s2`, then
   inspect goals, public telemetry/radio, and our private decisions if mounted.
3. Scout the next opponent only through the public league archive.
4. State one falsifiable hypothesis in `NOTES.md`; compare against a fixed
   baseline and reject attractive ideas that worsen the target metric.
5. Scrutineer, run a purposeful practice, and inspect decisions—not only score.
6. Keep a change only if it improves the intended measure without creating an
   obvious own-goal, wall-pin, deadline, or empty-goal risk.

## Current targets and risks

- Primary: win goal difference; no own goals.
- Shape: pair distance roughly 1.4-2.3 m under pressure, both players involved,
  and first-to-ball share above 55%.
- Conversion: turn final-third entries into clear runs without adding falls.
- The 0.3 m role threshold is intentionally quick. Practice rejected a 0.75 m
  sticky assignment because attacking-half possession fell to 14.8%.
- A short sample practice is control evidence, not opponent evidence. Only a
  competitive match can validate the Singularity plan.
