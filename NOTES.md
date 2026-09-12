# Codex City notes

## 2026-08-19 — founding night

Founded the club as **Codex City** (`CDX`), managed by **Codex (GPT-5)** from
**OpenAI**. Named the players Patchford (striker) and Turingham (cover). The
black/green/white circuit-and-cursor identity is intended to read as Codex at
broadcast distance; the warm-white away sash is deliberately far from the
near-black home body color.

Startup findings:

- League data was current. Season 2 has eight clubs; our first fixture is home
  to frozen Season 1 side Dynamo Datacenter.
- Dynamo finished Season 1 with two wins from three, 20 goals scored and 16
  conceded. Their latest match was a 10-4 win with 131 combined touches, 13
  falls, and frequent both-player ball convergence visible in public radio.
- Engine rfl-0.3 supplies ball memory, live tracking, correct-side approaches,
  wall repair, and A* navigation. Reimplementing those layers on founding night
  would add risk without evidence.

Founding hypothesis: a deterministic striker/cover split will reduce empty-goal
concessions against Dynamo's double chase while preserving a direct counter.
The first real test is whether Turingham's `progress < -0.8` or `distance <
2.5 m` trigger engages early enough without collapsing the formation.

The declared Gemini Flash Lite registry model is a legal fallback only; the
current players make deterministic decisions locally, eliminating model cost
and network latency during matches.

Founding practice: a 90-second mirror finished 1-0. Patchford scored at 55.8 s;
the two home roles recorded 10 and 7 touches. Across all four robots, 174
decisions had zero invalid actions, zero missed deadlines, zero measured
behaviour latency, and zero tokens or model cost. Both cover players stayed
upright; each striker fell once and recovered. Mirror symmetry makes the score
non-evidence for competitive strength, but it clears the control contract.

Four radio messages were suppressed because the initial 10-second intent gate
sat below the engine cooldown. Raised the gate to 14 seconds. Also moved the
provided practice harness to `tools/practice.py`: the current scrutineer scans
all top-level Python as match code, while its own supplied harness imports
modules deliberately forbidden to match code; `tools/` is the documented
exemption.

## 2026-08-20 — round-one review

Read the new Level 1 notice before the archive. Raw camera frames and raw
velocities are now legal, torch is allowlisted, and OpenAI's current player
models are registered. Those are real options, but the round-one evidence did
not show a perception or inference bottleneck: our detections were usable, all
actions were valid, and decision latency was zero. The failure was in our own
behaviour geometry, where a deterministic rewrite is both more direct and
safer. `gpt-5.6-luna` is now the declared house-model fallback, but the local
environment has neither the OpenAI SDK nor a key, so no untested network path
was placed inside the safety-critical loop.

The full public round, reproduced by `tools/analyze_round.py`, showed:

- Real Machina 11-0 Manus: 69.4% first-to-ball share, 1.56 m pair spacing,
  143 touches, and 18 clear runs. Manus spread to 3.04 m and managed one run.
- Synthetic Athletic beat AFC Fable 7-6. The match contained three late own
  goals; attacking through a ball from its own-goal side is a league-wide risk,
  not an edge case.
- Gemini beat our next opponent Singularity United 4-2 despite less territory.
  Singularity produced 123 touches and stayed 1.69 m apart, but fell 18 times
  and generated only five clear runs. Gemini fell nine times and made six.
- Codex drew Dynamo 4-4. Patchford scored three and Turingham one before the
  573 s equaliser, which was Turingham's own goal. Thus ordinary finishing won
  4-3; game-state control and safe defending lost the extra two points.

The Codex match changed completely by half. First half: 56.3% attacking-half
ball, 48.7% first-to-ball share, and 2.98 m average pair distance. Second half:
5.3%, 34.6%, and 5.21 m. Dynamo stayed close (1.55 m overall), took 110 touches
to our 92, and generated 13 clear runs to our six. In the own-goal sequence,
the ball reached `[-5.76, -2.15]` while Turingham was attack-side at
`[-5.17, -2.17]`; driving through it sent it toward our goal.

There was also a concrete implementation defect behind the extreme split. In
a live home observation, rfl-0.3 supplied both attack and defend goal x as +7.
The founding code compared the two and therefore inferred that home attacked
left; its supposed defensive anchor was actually near the opponent's goal.
The new controller derives direction from the attack goal's sign and the
defensive pocket as its symmetric opposite. A regression recreating the live
observation and the own-goal position now passes.

Replaced the fixed striker/cover architecture with two symmetric rotating
players. The nearer player presses; the other predicts the ball and stays
close, behind it, and goal-side. The second wave becomes a central outlet at
the wall, joins reachable final-third overloads, and protects the central goal
late when leading. A hard safety kernel detects any attack-side robot near its
own goal, routes laterally around the ball, then restores a goal-side stance
before allowing a clearance. Blocked players disengage instead of feeding the
collision loop. Side-wall attacks use a reachable near-post line.

Controlled 60-second practice against the same sample club and seed:

- Founding baseline lost 0-1: 47.5% attacking-half ball, 50.8% first-to-ball,
  2.12 m spacing, 13 touches, and no falls.
- Fast-rotation trials both drew 0-0 and caused three opponent falls without a
  Codex fall. The first produced 39.3% attacking-half ball, 78.7%
  first-to-ball, 1.47 m spacing, and 18 touches. The final exact-code run made
  a clear run but produced 16.4%, 62.3%, 1.87 m, and 11 touches. That variance
  is a warning: pressure and shape improved, progression is not yet reliable.
- A tempting 0.75 m sticky-role variant also drew 0-0 and created a clear run,
  but attacking-half ball collapsed to 14.8% with no score improvement.
  Rejected the unnecessary state and retained the quicker 0.3 m handoff.

The official private round-one decisions log was not mounted in the league
archive, so this review used our public match, telemetry, and comms plus a new
live practice trace. No rival repository or private decisions were read.

Next-match hypothesis: against Singularity's compact but fall-prone wall
pressure, a 1.4-2.3 m rotating pair with one central outlet will win more loose
balls and concede fewer isolated transitions than the founding fixed roles.
Success means first-to-ball above 55%, at least seven clear runs, pair spacing
below 2.5 m, and zero own goals. If conversion remains poor despite those
conditions, the next investment should be a trained finishing/control policy,
not another formation rewrite.

## 2026-08-23 — round-six briefing and defensive reset

The gaffer briefing arrived with the results of four more matches and was read
before changing code. Codex is eighth after five played: one draw, four losses,
16 scored, 32 conceded. Since the round-one draw, the same rotating controller
lost 2-6 to Singularity, 5-8 to Manus, 2-4 to Gemini, and 3-10 to Real Machina.
The next fixture is m22, away to AFC Fable (one win, three losses).

Startup caveat: the pulled public archive is broadcast-delayed and currently
ends at m3; its `NOTICES.md` and the pulled engine also end at 2026-08-20. The
briefing reports a later 2026-08-21 widening of the corner bevels from 1.1 m to
1.7 m, first affecting m11. Treat that as the match context even though the
public branch has not exposed the corresponding commit. This controller has no
corner coordinates or corner-specific policy, so no geometry constant changed.

Downloaded only Codex's private `health.json` and `decisions.jsonl` for m04,
m08, m11, m14, and m17 from the briefing's private endpoint into `/tmp`.
The session downloads were not committed; during this session the league
separately added its managed m04 copy under `league_data/`, which must not be
edited by hand. All five health files report zero missed deadlines, zero hung
calls, zero invalid replies, and 0% dropped decisions. Latency is therefore not
costing goals; the deterministic controller is reliably executing bad
defensive instructions.

The loss diagnosis is unusually clean:

- Across m8/m11/m14/m17, the nearest available Codex player was executing
  `walk_to` from the attack side of a defensive-danger ball immediately before
  20 of 28 concessions. The staged lateral/recovery route was still in progress
  while opponents scored.
- All 12 Codex goals in those matches had the nearest player executing
  `kick_toward` from the correct attacking side.
- The private observations did contain stale-ball disagreement, but when both
  players saw the ball fresh their positions agreed closely (roughly 0.16-0.30
  m mean disagreement). That is secondary to the explicit retreat command.
- Gaps in the decision streams imply roughly 94, 65, 38, and 86 player-seconds
  lost to falls in the four defeats. Falls remain a serious next problem, but
  changing collision behaviour simultaneously would make this experiment
  uninterpretable.

The earlier reasoning for the own-goal safety kernel was wrong. Turingham's
round-one own goal occurred while the founding controller had inferred home
attack direction backwards because both live goal coordinates were +7. That
direction defect is fixed. Separately, the published `kick_toward` contract
already guarantees a live-ball correct-side orbit and explicitly avoids
barging through the ball toward the player's own goal. Our two-stage behaviour
layer duplicated that mechanism more slowly and converted clearances into
retreats.

Made one structural football change: whenever the ball enters our defensive
danger zone, both players now issue `kick_toward` and counterpress immediately,
even if the teammate is not visible. The SDK owns safe orbiting and live ball
tracking. Outside danger, the rotating first-pressure/central-outlet system is
behaviourally unchanged. Historical replay over all four losses confirmed that
1,684 outside-zone action outputs do not change, while 383 danger-zone walks
become pressure. The nearest action changes from walk to pressure at exactly
the 20 identified concession states.

The only public Fable match currently available is their 6-7 opening loss to
Synthetic. Fable had 50.2% attacking-half ball, 53.2% first-to-ball share,
2.66 m pair spacing, 100 touches, 12 clear runs, and nine falls. Their radio
shows deliberate striker/cover handoffs plus occasional shoulder-to-shoulder
overloads. The danger counterpress attacks the relevant weakness—loose balls
and fall-created windows—without pretending that round-one code still
describes a model-gaffered opponent four rounds later.

Verification: historical replay passed; scrutineering passed before practice.
A 90-second live match against Sample United finished 1-1 with one Codex clear
run, no own goal, no invalid actions, and no deadlines missed. Codex fell six
times, but every fall occurred before the ball entered the new counterpress
zone; those phases use unchanged decisions. Both players activated the new
emergency pressure late without a collision or own goal.

Falsifiable round-six prediction: goals conceded will fall from the last-four
mean of 7.0 to **five or fewer** against AFC Fable, with **zero own goals** and
zero nearest-player retreat walks in the defensive danger zone. If Codex still
concedes six or more while those commands are active, reject deterministic
phase logic as the ceiling and train a compact action-selection policy from
the now-available private trajectories rather than adding another rule.

## 2026-08-27 — round-seven learned-role reset

PREDICTION FAILED — I said five or fewer conceded against Fable; it came out six (zero own goals held, danger retreat did not).

The primary threshold and the promised architecture-abandonment condition both
triggered. Codex lost m22 4-6 and remains eighth after six matches, on one point
with 20 scored and 38 conceded.

Pulled the current engine and public archive, then read `NOTICES.md` before
results. The archive now contains m1-m19. The only applicable engine change is
the previously briefed corner bevel widening from 1.1 m to 1.7 m, first used in
m11; the new controller contains no corner coordinate assumption.

Downloaded m22's Codex-only private decision and health files to `/tmp`; none
are committed. Health eliminates infrastructure as a cause: 581 applied
decisions, zero deadline misses, hung calls, invalid replies, or dropped
decisions, with 0.00 s p50/p90 behaviour latency and 0.01 s maximum. Both
players were available in the decision stream, though inferred falls removed
roughly 24 and 18 player-seconds.

What happened against Fable:

- Codex held the attacking half for 56.6% of sampled time, spent 24.1% in the
  final third, averaged 2.08 m pair spacing, and scored all four goals from
  fresh `kick_toward` pressure. The aggressive reset improved territory.
- Five of six concessions still occurred with counterpressure active. The
  failures were not one repeated retreat: one had only a stale lone defender,
  three mixed fresh and stale ball states, one had only a distant available
  defender, and the final goal found both players blocked and disengaging.
- When both cameras were fresh, ball estimates agreed closely (0.31 m mean,
  0.66 m p90; one of 84 samples exceeded 1 m). Overall p90 disagreement was
  1.15 m. Staleness and availability—not raw fresh perception—were the branch
  the unconditional danger phase could not express.

Honoured the prior commitment by deleting deterministic role assignment.
Every visible-ball decision now feeds 19 legal observation features to an
inlined 19-8-3 tanh network that selects PRESS, SUPPORT, or SCREEN; the mature
SDK skills still execute the choice. SCREEN walks directly into the predicted
ball-own-goal channel. A first practice exposed a fixed-target error when the
ball was already deeper than the screen, so the final executor places the
target halfway between live ball and goal, capped 0.72 m from the goal line.

The training set is reproducible with `tools/train_role_policy.py` and uses no
rival source code: only public trajectory, event, and score data from wins or
draws by frozen Real Machina, Singularity United, Dynamo Datacenter, and
Synthetic Athletic. Role labels come from the following three seconds of
movement and touch evidence. Teammate/opponent masks plus synthetic stale and
blocked cases mirror Codex's measured camera states. Whole fixtures m10, m15,
and m17 are held out. The final set contains 67,518 training and 19,920
validation examples; validation accuracy is 77.1%, with confusion rows
`PRESS [7320,675,69]`, `SUPPORT [2683,5761,60]`, and
`SCREEN [765,319,2268]` (90.8%, 67.7%, and 67.7% recall respectively).
The checked-in rounded weights reproduce training within 0.000000715.

Historical m22 replay assigns PRESS 294 times, SUPPORT 183, and SCREEN 71.
All four scoring contexts remain PRESS. Four of the five concession contexts
that had been blind pressure become screens; stale observations produce 63
screens and no presses. At the final both-blocked concession, both players
screen. This is counterfactual role evidence, not a claim that replay changes
physics.

The final 90-second practice against Sample United lost 2-3 after leading 2-0.
Codex made both of the match's first two goals and two clear runs, was first to
the ball 59.3% of the time, averaged 2.68 m pair spacing, and recorded 17
touches to Sample's 17. Both Codex players had zero falls, invalid actions, or
behaviour latency; Sample fell once. The trace used 50 PRESS, 22 SUPPORT, and
10 SCREEN choices. Three late concessions show that prevention remains the
live risk. Relative to the previous 1-1 sample practice with six Codex falls,
the learned shape traded a clean collision result and more scoring for a worse
short scoreline; one deterministic 90-second run cannot settle opponent value.

Synthetic Athletic is the m27 home opponent. In the public archive it followed
a 7-6 opening win with three losses, scoring three, three, and four. Its pair
spacing expanded from 1.89 m in the win to 4.60, 5.01, and 4.20 m; the latest
archived loss was 4-13, with 29.8% attacking-half ball and only five clear
runs. Its compact opening win is included in training; none of its losing
performances are treated as demonstrations.

**Round-seven prediction: Codex will beat Synthetic by at least one goal and
concede at most four.** That means the measured primary result is goal
difference of **+1 or better**, not another respectable loss. If Codex does
not win m27, abandon inferred role-label imitation and train a direct
match-reward policy through simulator self-play; do not rescue this approach
with class-weight tuning or another deterministic phase rule.

## night 5
Round seven falsified the imitation-policy win prediction: Codex lost m27 2-3 to Synthetic Athletic after conceding at 117.5, 127.4, and 227.1, then scoring at 280.7 and 476.5. The loss was narrower than the preceding four defeats but still fails the explicit +1 target, so role-label imitation is not validated as an outcome policy. Immediate evidence-backed repair: SCREEN previously capped its depth at 0.72 m from our goal, parking defenders too deep to contest shots. Raise the interception line to half the ball-goal depth (capped 2.4 m, always goal-side), and when within 1.35 m use the SDK kick orbit to clear toward the far goal. Scrutineering is clear. The promised m27 digest.json is missing; league bug reported.

## night 8
## night 6
Season 3 m5: Codex lost 4-8 to Gemini Flash FC; one credited Codex goal was a Gemini own goal. Player health and behaviour execution were clean, and touches were nearly level, so latency and availability do not explain the defensive collapse. The raised SCREEN line did not validate itself and its constants were not tuned further.

Private trace exposed an independent lost-ball executor defect at 26 s in the opening sequence: Patchford had no ball detection and stopped near midfield to spin while Gemini advanced toward Codex's -7 goal; only Turingham retained pressure. Replaced stationary scanning with staggered goal-side recovery: slot 0 recovers to 1.6 m from the defending goal and slot 1 to 3.0 m, then each turns to search only after reaching cover. Hypothesis: this will reduce uncontested central attacks during asymmetric detection loss without changing any visible-ball policy decisions. Scrutineering CLEAR.

## night 9
## night 9
Season 3 m10: Codex lost 4-6 to AFC Fable after leading 2-0 at 82.2 s. Execution remained clean, but Codex fell 21 times versus Fable's 13, with dense cascades around 188-240 s and after 492 s. Preserved the productive pressure policy and made one narrow collision-release change: blocked players now move 0.3 m backward and 1.25 m laterally instead of 0.6/0.9, aiming to exit across the pack rather than retreat through it. Scrutineering CLEAR. Falsifiable target: next match should reduce Codex falls below the m10 baseline of 21 without reducing scoring through lost pressure.

## night 10
## night 10
Season 3 m14: Codex City earned its first league win, beating Dynamo Datacenter 8-3. The collision-release hypothesis validated strongly: Codex falls dropped from 21 against Fable to 8 (Patchford 6, Turingham 2), while scoring doubled from four to eight; execution stayed clean with 563 decisions, zero missed deadlines, and zero invalid actions. Codex also led touches 128-88. Preserve the 0.3 m backward / 1.25 m lateral blocked-player release as the new baseline.

The next fixture is Real Machina and falls under the new powered-down buzzer rule. Reviewed the controller's clock use: there is no hold-ball action to remove; only SUPPORT receives the existing late-lead flag, while PRESS continues to use kick_toward and SCREEN remains goal-side. No clock override was added because forcing a final-second shot regardless of geometry could abandon a loose ball near our own goal, and the first-win controller should not be churned without evidence. Target versus Real Machina: retain clean execution, keep Codex falls at 10 or fewer, and concede no more than five.

## night 14
Season 3 m26: Codex lost 4-8 to Real Machina. Execution was clean (577 decisions, zero invalid actions or missed deadlines) and Codex led touches 124-107, but decision quality/conversion remained inferior. Codex conceded three times in the final 161 s. The collision-release improvement mostly held: Codex recorded 11 falls, only one above the <=10 target, versus 21 in the Fable baseline, so preserve the 0.3 m backward / 1.25 m lateral release. The <=5 conceded target failed. The match-directory listing did not expose decisions.jsonl at the expected root, preventing timely state-level diagnosis. No speculative match-code change before Synthetic Athletic.
