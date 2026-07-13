### Second-opinion-seat gate (22-second-opinion-seat)

Every required phase-gate (spec, audit, plan — which ones are required is set
by your routing profile, see below) needs one second-opinion-seat call,
recorded via `check_gate_evidence.py --write-evidence <phase>` before the
call. Your routing profile's number is a COUNT of required phase-gates
(e.g. MAX5's `{T2: 2}` = spec AND audit), never a per-phase threshold — the
ship check always verifies each required phase at `--threshold 1`.

The second-opinion seat is the advisor tool if this environment has one,
else a fresh-context subagent on the strongest affordable model — never a
bare model-name reference. A `-RISK` tier suffix (module `20-tier-system`)
adds one more phase to the required set (capped at all 3 phases); the ship
skill computes that bump, not this module.

Full seat-dispatch instructions: `docs/harness/22-second-opinion-seat.md`.
