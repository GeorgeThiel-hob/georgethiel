# Install Guide — what to run, and when

This is the member-facing "what do I actually do" companion to `START-HERE.md`.
`START-HERE.md` is the normative flow the installing Claude Code session follows step
by step — read it for the full rules. This file is shorter: it sequences the whole
install from your side of the keyboard, and gives the post-restart part (the one part
`START-HERE.md` can't do for you) concrete, checkable steps.

---

## 0. Before you start — where to open the session

You have two options for *where* to point Claude Code at this kit:

- **Dry run first (safe preview).** Open the session in a scratch copy of your repo,
  not the real one. You can watch the whole install happen and read the report, but
  the STANDARD and FULL smoke tests below **cannot execute** there — a dry run's
  scratch folder is never a live working directory, so installed hooks and skills
  never go live inside it (`START-HERE.md` §10). Only LIGHT's fixture test truly runs
  in a dry run.
- **Install directly at your repo's root (the live path).** This is required if you
  want to actually finish the install — restart, `/hooks`, and the smoke test in
  section 3 below only work when the session was opened **at the real destination
  repo's root**, not a subdirectory and not `handoff-kit/` itself.

Either way: open the session **at the repo root** (the directory that contains, or
will contain, `.claude/`, not inside `handoff-kit/`).

---

## 1. Kickoff

Tell the session to read `START-HERE.md` in this kit and begin the install. It will:

1. Read `START-HERE.md` fully and check prerequisites (Claude Code itself; the
   Superpowers plugin for STANDARD/FULL; a shell, `python3`, and `git` for the installer
   step). It reports anything missing before doing anything else.
2. Open `interview/INTERVIEW.md` and ask you **up to nine questions, one at a time**
   (Q4 may be auto-skipped when the project type already pins FULL rigor) — what
   you're building, your Claude plan, GitHub-vs-local, risk/PII/desktop-app/stack
   questions, and optional add-ons. It reads each answer back to you for confirmation
   before moving on. Answer honestly; these answers are what select your rigor
   profile (LIGHT/STANDARD/FULL) and routing profile (PRO/MAX5/MAX20) — there's no
   "correct" answer to game, just an accurate one.

That's the only part you actively participate in. From there the session computes your
module set (steps 4–5) and writes `install-spec.json`, then runs **one static command** —
`python3 handoff-kit/installer.py --spec install-spec.json --dest .` — with no `--now`
flag and no shell command substitution (the installer self-stamps its own UTC
timestamp) — which mechanically does everything the install used to do by hand: copying
files, assembling
`CLAUDE.md`, `.gitignore`, and `.claude/settings.json` (merging every selected module's
`settings-fragment.json` so its hooks are actually registered), applying ADAPT
substitutions, `git init` if needed, and writing `HARNESS-VERSION.md` + an **install
report** (modules installed, ADAPT edits made, defaults used, any skill-collision
warnings), plus `installer-verify.json` (per-file hashes, a `{{TOKEN}}` residue scan,
settings-hooks existence, skill-collision warnings) so the next step confirms rather than
re-derives. The session then does a seeded spot-check (step 7) against both files — a
handful of genuine probes, not a full re-derivation — confirming the installer's own
claims. Read the report. It ends with one instruction: restart.

---

## 2. Restart — step 8 starts here, and it's on you

The install report was written by the *old* session. A `.claude/skills/` directory
that appears mid-session is only discovered by Claude Code at session **start** — so
until you restart, none of what was just installed is actually live.

1. **End the session** that ran the install (exit / close it — don't just open a new
   tab on top of it).
2. **Open a brand-new Claude Code session at the same repo root.** Same directory as
   step 0 — this is not optional; hooks and skills load from `.claude/` at the
   directory Claude Code was started in.

Everything from here is manual verification — a fresh Claude Code session has no
memory of the install session, so you (the human) are the one confirming it landed.

---

## 3. Verify — `/hooks`, then the smoke test

### 3a. `/hooks` — what you're actually checking

Run `/hooks`. You're looking for the kit's own entries to be **registered**, not just
present-looking-plausible. What you should see depends on your resolved rigor tier:

| Your rigor tier | What to look for in `/hooks` |
|---|---|
| **LIGHT** | Nothing kit-related. LIGHT installs no hooks module at all — this is correct, not a failure. |
| **STANDARD** | A **PreToolUse** entry running `pretooluse_dispatcher.py` (matcher `.*`). |
| **FULL** | The same PreToolUse `pretooluse_dispatcher.py` entry, **plus** a **SubagentStop** entry (`subagentstop_log.py`) and a **Stop** entry (`stop_citation_guard.py`). |
| **Any tier where you answered "yes" to the PII question** | An additional **PreToolUse** entry scoped to `Write\|Edit\|MultiEdit` running `pii_pattern_guard.py`. |

`/hooks` showing an entry is **presence**, not proof — it only tells you Claude Code
parsed `settings.json` correctly. The smoke test below is what proves the hook
actually *does* something.

### 3b. Smoke test — run the one matching your rigor tier

**LIGHT — build-and-check a toy skill.**
1. Write a minimal skill under `.claude/skills/toy-skill/SKILL.md` (a few lines of
   instructions is enough).
2. Write one fixture: a small sample input and its expected output.
3. Invoke the skill against that input.
4. **PASS** = the skill's actual output matches the fixture's expected output. There
   is no hook to check at LIGHT — this tier has none installed by design.

**STANDARD — a micro-change through the whole pipeline.**
1. **Create a working branch first.** The standing-brief gate's allow-list is exactly
   `main`, `master`, and the empty branch of a just-`git init`'d repo — it fires on
   **any other** branch name, not only ones prefixed `feature/`. If you run the smoke
   test on `main` you will see no block and wrongly conclude the hook is dead, so
   create a non-main working branch (e.g. `git checkout -b feature/smoke-test`) first.
2. Make the smallest possible edit (a T1-shaped change — a comment, a doc typo fix,
   under 5 lines).
3. Dispatch a subagent (a `Task`/`Agent` call) to carry it through, **without** first
   writing a standing brief.
4. **PASS** = the dispatch gets **blocked** — `pretooluse_dispatcher.py` routes to
   `require_standing_brief` (module `20-tier-system`) and returns a message naming the
   expected brief path (`docs/superpowers/briefs/<branch-slug>.md`). That block *is*
   the hook firing; a list entry in `/hooks` never proves this on its own.
5. Now write the brief at the path the block message named, re-dispatch, and confirm
   it proceeds. Then finish the chain: change → tests (`{{TEST_CMD}}`) → commit via
   the installed `GIT` skill variant. On the github routing variant, this ends with a
   push to your configured remote.

**FULL — a T1-shaped change through the shape of the full pipeline.**
1. On a `feature/*` branch (create one as in STANDARD step 1 — the gate does not fire on
   `main`), confirm the `require_standing_brief` block fires on a brief-less dispatch
   (module `20-tier-system` is installed at FULL too, same hook).
2. Then run a spec stub → implement → one `REVIEW` round → ship via the installed
   `GIT` skill variant.
3. **PASS** = each stage actually engages — the `REVIEW` skill loads and runs its
   first step, and `GIT`'s pre-flight gate (module `22-second-opinion-seat`) runs its
   phase-evidence check. (For a T1-shaped change with no spec/plan evidence recorded,
   that check auto-passes rather than blocking — correct behavior; the point is the gate
   *runs*, not that it blocks.) This is **not** a full production run: the deeper loops
   (MAP's effect-mapping loop, the sentinel gate) are validated by presence-and-invocation
   here, not full convergence. Say so explicitly when you record the result — don't overclaim.

### 3c. Record the result

Append the smoke-test outcome (PASS/FAIL, what you saw, any block messages) to the
install report the prior session wrote. If either `/hooks` or the smoke test doesn't
match what's described above, don't self-diagnose past that point — treat it as a
gap and report it, the same honesty standard `START-HERE.md` asks of the installing
session.

---

## 4. Uninstalling / re-installing

A few things worth knowing once the kit has done its job:

- **Keep the `handoff-kit/` directory around if you might run `uninstall.py` later.**
  If `mypy .` or `ruff` complain about the staged kit templates under `handoff-kit/`,
  the fix is to **exclude** `handoff-kit/` from your type/lint config, not to delete
  the directory — deleting it now forecloses a clean `uninstall.py` run later.
- **Preview before you act.** `python3 handoff-kit/uninstall.py --dest <dir> --dry-run`
  prints exactly what will be removed, stripped, or skipped, and touches nothing on
  disk. Back up any kit-owned file you've since customized before running the real
  uninstall.
- **Re-run or upgrade is two commands, not one.** If you authored your own hook that
  reuses the kit's `.claude/hooks/run_python.sh` launcher, a later `installer.py` run
  will refuse — the prior-install guard matches on any settings entry whose command
  embeds `run_python.sh`, including yours. Re-run with `--force` in that case. Outside
  that case, the normal path to re-run or upgrade the kit is `uninstall.py` first,
  then `installer.py` again — not reaching for `--force` as a shortcut.

---

## See also

- `START-HERE.md` — the normative 8-step flow this guide sequences; read it for the
  actual rules (module resolution, ADAPT substitutions, CLAUDE.md/`.gitignore`
  assembly, update mode).
- `START-HERE.md` §7 ("Smoke tests") and §6/§8/§9 (model-availability, enforcement,
  and risk honesty statements) — the full text behind the summaries above.
