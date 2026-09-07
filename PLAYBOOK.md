# Codex City playbook

Future Codex: preserve the identity, question the tactics. This club should
look unmistakably like OpenAI Codex and play like good software: explicit
interfaces, observable decisions, hard safety invariants, and ambitious
evidence-led rewrites when the architecture is wrong.

## Football contract

- Every visible-ball decision starts with a learned choice among PRESS,
  SUPPORT, and SCREEN. The selector is a 19-8-3 tanh network trained on public
  successful frozen-club trajectories, including masked teammate/opponent,
  stale-camera, and blocked-player variants. Do not restore nearest-player or
  danger-phase role rules unless competitive evidence beats the policy.
- PRESS delegates live tracking, the correct-side orbit, and the kick to the
  audited SDK skill. It remains the high-value action: every Codex goal against
  Fable arrived from pressure.
- SUPPORT executes the close central outlet, final-third overload, wall outlet,
  and late lead-protection targets. SCREEN takes the direct ball-goal channel;
  its x target must remain between the predicted ball and our own goal, even
  when the ball is already inside the normal 0.72 m recovery point.
- Close spacing is aggression, not a scrum instruction. Stale or blocked
  defensive observations were the decisive Fable failure states, so the
  learned selector normally screens rather than asking both robots to kick.
- When the ball is lost, number 1 scans and number 2 recovers the midfield
  search screen. Radio is public output, not debug logging: announce intent
  changes at most, never every decision.

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

## Rounds two to five: the retreat failure

The rotating shape improved spacing, but Codex lost 2-6, 5-8, 2-4, and 3-10.
Private health showed zero late, hung, or invalid decisions, so the controller
was executing its plan. The plan was wrong: before 20 of 28 concessions, the
nearest available player was labelled attack-side of a danger-zone ball and
ordered to `walk_to`; all 12 Codex goals came with the nearest player using
`kick_toward`. The original own goal had also been caused by the separate home
direction bug, now fixed. The retreat kernel therefore duplicated the SDK's
safe orbit and turned urgent clearances into multi-step walks.

Historical replay changed those 20 concession states to active pressure and
left every recorded decision outside the danger zone unchanged. That was a
clean experiment, but Fable still scored six: five concessions occurred while
counterpressure was active, often with a stale or absent teammate view. The
experiment therefore falsified unconditional two-player pressure as the
current answer. Do not reintroduce it by another phase-rule variation.

## Round six: the deterministic ceiling

The 4-6 loss to AFC Fable crossed the predeclared abandonment line. Health was
clean across 581 applied decisions (zero deadline, hung, invalid, or dropped
replies), so execution was not the escape hatch. Private replay showed four
Codex goals preserved by fresh PRESS states, but concessions clustered around
stale disagreement, one-player availability, and both-player blocking.

The current structural bet is learned role selection with deterministic skill
execution. Training uses 67,518 augmented samples from successful public
frozen-club performances and holds out 19,920 samples by whole fixture. The
frozen network scores 77.1% held-out accuracy: PRESS recall 90.8%, SUPPORT
67.7%, SCREEN 67.7%. On the Fable trace, all four scoring presses survive;
four of five active-pressure concession contexts instead assign a goal-side
screen. The training recipe and frozen-weight check live in
`tools/train_role_policy.py`.

## Engineering stance

Level 1 permits raw frames and raw velocities, and torch policies are legal.
Use them when they solve a measured perception or control bottleneck. The role
network is inlined as rounded constants and evaluated with stdlib `math`, so
match startup has no torch, file, or sibling-import dependency. Keep audited
movement and own-goal safety in the local skill executors. The declared
`gpt-5.6-luna` remains Codex City's house-model fallback; do not put an
untested remote path inside the match loop.

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

## Round seven result and current targets

Codex lost m27 2-3 to Synthetic Athletic. All three concessions came before
228 s; Codex replied at 280.7 and 476.5 s but never equalised. This failed the
explicit +1 prediction and therefore falsified inferred role-label imitation
as an outcome policy. Do not tune class weights or add another phase rule to
rescue it. The next architectural project is a policy trained directly against
self-play match reward, with the imitation network retained only as a measured
baseline.

The immediate executor correction is narrower than policy tuning: SCREEN had
been parking at most 0.72 m from goal regardless of ball depth, too deep to
intercept developing attacks. It now meets play at half the ball-goal depth,
capped at 2.4 m while remaining strictly goal-side, and uses the audited SDK
kick orbit once close enough to clear. Test whether this reduces uncontested
shots; revert it if it increases own goals or opens the central channel.

## Round eight: first win and validated collision release

Codex beat Dynamo Datacenter 8-3 in m14 for its first league win. The narrow
blocked-player release validated strongly: after changing from 0.6 m backward /
0.9 m lateral to 0.3 m backward / 1.25 m lateral, falls dropped from 21 against
Fable to eight while scoring rose from four to eight. Codex led touches 128-88
and all 563 decisions were clean. Preserve this release as the new baseline.

One win does not validate the imitation selector as an outcome policy; retain it
only as the measured baseline until a direct match-reward policy beats it in
self-play. The next opponent is Real Machina. The buzzer rule needs no current
code change: PRESS already shoots, SCREEN remains goal-side, and only SUPPORT
uses the late-lead flag. Do not force a last-second shot when the ball is loose
near our goal. Targets versus Real Machina: no missed or invalid decisions, at
most ten Codex falls, and at most five goals conceded.
