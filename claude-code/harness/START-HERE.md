# START HERE — Handoff Kit install guide

You are a fresh Claude Code session and someone has dropped this `handoff-kit/`
folder into a repository. Your job is to install the workflow harness it carries —
the hooks, skills, CLAUDE.md rules, and profiles that turn a bare repo into one
that runs the disciplined build pipeline this kit encodes.

Read this file **completely** before doing anything else. It is the entry point:
every other file in the kit is reached from here. You will run an interview, resolve
the answers into a small set of profiles, run the installer against the resolved spec,
and hand back an install report. Nothing here trades, ships, or mutates anything
outside this repository — installation is copy, merge, rename, and hash, run by one
disclosed shell command (the installer invocation, detailed below).

The kit is a **snapshot**. Its version and cut provenance are recorded in `VERSION.md`.
It does not auto-sync with the project it was cut from; a newer harness means a newer
kit cut, installed through the update procedure described later in this file.

> **Companion doc:** `INSTALL-GUIDE.md` (same directory) is a short, sequential
> "what to run and when" reference for the member — read this file for the full
> normative flow; hand them `INSTALL-GUIDE.md` for the parts they act on directly,
> especially the post-restart step (7 → 8).

---

## 1. Prerequisites

Confirm these before you touch any file. If any is missing, **stop and report it to
the member** — do not improvise around a gap.

- **Claude Code** — required at every rigor tier. The harness is hooks + skills +
  CLAUDE.md rules that only Claude Code loads. Without it there is nothing to install
  into.
- **The Superpowers plugin** — required for the STANDARD and FULL rigor tiers, which
  lean on its brainstorming / planning / review skills. It is **not** required for
  LIGHT: the LIGHT tier runs on bare Claude Code with no plugin dependency. If the
  interview resolves to STANDARD or FULL and the plugin is absent, report the gap and
  let the member decide (install the plugin, or drop to LIGHT).
- **A shell, Python 3, and `git`** — steps 1–5 are tool-driven (Read / Write / Glob);
  step 6 runs exactly **one** shell command, the `installer.py` invocation; step 7 adds
  only the small bounded set of spot-check probes (see the Bounded-shell self-check
  section). `installer.py` itself shells out to `git init`
  internally when the destination has no repo yet — its one disclosed subprocess call —
  and computes hashes in pure Python (`hashlib.sha256`), never the `shasum` binary.
  Confirm `python3` and `git` are both available.
- **Windows notes** (the kit is developed on macOS/Linux; on Windows the
  following are load-bearing):
  - **Git for Windows is required for the hook layer.** Claude Code runs hook
    commands through Git Bash when Git for Windows is installed — without it,
    hook commands fall back to PowerShell, which cannot run the kit's
    `bash .claude/hooks/run_python.sh …` commands, and every hook (including
    the Stop-hook's `CITATION_GUARD_MODE=block …` env-prefix form) stays dead.
    The skills themselves are plain Markdown and work without any of this.
  - **Python launch:** where `python3` is a Microsoft Store alias stub, launch
    the installer with `python` or `py -3` instead (the installed hooks are
    unaffected — `run_python.sh` already falls back `python3` → `python`).
  - **Skill shell-outs:** skills that call `python3 .claude/hooks/…` (gate
    evidence, schema checks) run inside the same Git-Bash environment as the
    hooks; they inherit the same requirement.
  - **The github ship skill needs the GitHub CLI** — an authenticated `gh`.
  - **If you commit `.claude/hooks/` to a repo that Windows machines check
    out**, add `*.sh text eol=lf` to that repo's `.gitattributes` — a CRLF
    checkout corrupts `run_python.sh` and every hook dies. (The kit's own tree
    ships a `.gitattributes` with this rule; your project repo needs its own.)
  - **Known limitation:** the FULL-tier reexec guard shells out to `grep`,
    which native Windows lacks — on Windows that guard is fail-open (no
    enforcement, no crash).

Report anything missing, in one message, before continuing to the install flow.

---

## 2. The install flow — 8 steps

Run these in order. Steps 1–7 happen in this session; step 8 happens in a **new** session
after a restart.

> **Orientation read-set — read ONLY these, nothing else.** Beyond this file, the
> installing session reads exactly: `interview/INTERVIEW.md`, the **ONE** rigor profile
> matching its resolution (`profiles/rigor-LIGHT.md` **or** `-STANDARD.md` **or**
> `-FULL.md` — pick the single one the resolution algorithm selects, never all three),
> the **ONE** routing profile matching Q2 (`profiles/routing-PRO.md` **or** `-MAX5.md`
> **or** `-MAX20.md`), and `profiles/resolution-table.md`. **Do NOT read the module
> `README.md` files or `installer.py`** — the resolution table and profiles are
> authoritative for module lists and parameters; the installer is a black box you
> invoke, not code you review. (One narrow exception: if the member asks to **override**
> — drop or add a module — the one module whose dependency is in question gets its
> `README.md` consulted per "Override bounds" in `interview/INTERVIEW.md`; this does not
> apply to the default, no-override flow. This restriction covers the installer flow
> only — the `## Fallback — manual install` appendix has its own, wider read-set and
> applies only when the member explicitly chooses the manual path.)

1. **Read `START-HERE.md` fully.** (You are here. Finish reading before you act.)

2. **Check prerequisites; report gaps.** Run the checks in section 1 and report any
   missing prerequisite before proceeding.

3. **Run the interview.** Open `interview/INTERVIEW.md` and ask its questions **one at a
   time**. After each answer, read the answer back to the member and get confirmation
   before moving to the next question. Do not batch the questions. At Q9's confirmation,
   the session **writes `install-spec.json`** per `interview/INTERVIEW.md`'s "Writing
   install-spec.json" section — this file is the installer's entire input.

4. **Resolve answers → profiles + flags.** Feed the confirmed answers through the
   resolution algorithm (`interview/INTERVIEW.md`) to select exactly **one rigor profile**
   and **one routing profile**, plus environment flags. This resolution IS what
   `install-spec.json`'s `rigor`/`routing`/`flags` fields record.

5. **Read the two profile manifests (or `profiles/resolution-table.md`) and compute the
   module set.** Read the selected rigor and routing profile manifests under `profiles/`
   — or, faster, the single matching row-block in `profiles/resolution-table.md`, which
   mirrors them. Compute the **union** of the modules they list and apply flag variants.
   **Only if the member proposes a per-module override** (dropping or adding a module),
   consult that specific module's own `README.md` for its declared dependency line and
   validate the override against it (see "Override bounds" below) — this is the one case
   a module `README.md` is read; the default, no-override flow never opens one. This
   union IS `install-spec.json`'s `modules` field.

6. **Run the installer — zero LLM tokens for the mechanical work.**

   ```bash
   python3 handoff-kit/installer.py --spec install-spec.json --dest .
   ```

   This is a **static** command — copy it verbatim, with no `--now` flag and no command
   substitution (e.g. no `$(date -u ...)`). `--now` is optional: `installer.py`
   self-stamps a UTC ISO-8601 timestamp when it is omitted, so there is nothing to
   compute here. (A `$(date ...)` in this command previously caused a sandbox permission
   denial and a retry in a live install trial — the fix is to never construct the
   timestamp in the shell at all.)

   `installer.py` performs the ENTIRE mechanical install deterministically: copies each
   selected module's `files/` payload with the dot-staging / skill-variant / Q3-conditional /
   `.template` renames; deep-merges every selected module's `settings-fragment.json` into
   `.claude/settings.json`; assembles `CLAUDE.md` (detecting fresh vs merged from the
   destination — never trusting a spec input); assembles `.gitignore` the same way; applies
   every ADAPT substitution and refuses if any `{{TOKEN}}` survives; runs `git init` if no
   repo exists; writes `HARNESS-VERSION.md` (profiles, flags, ADAPT values, the post-ADAPT
   sha256 baseline) and `HARNESS-INSTALL-REPORT.md`; runs the skill-collision Glob; emits
   `installer-result.json`. If `installer.py` exits non-zero, its stderr names the exact
   validation failure — fix `install-spec.json` and re-run; do not hand-patch the
   destination.

7. **Self-check — a seeded spot-check against the installer's own evidence, not a
   re-derivation.** `installer.py` now writes `installer-verify.json` alongside
   `installer-result.json` specifically so this step confirms with real filesystem
   probes instead of re-deriving everything by hand. Read both files first, then run the
   narrow set of genuine probes below — **the machine report alone verifies nothing; the
   probes below are what actually prove it, and you must run them yourself.**

   **a. Read the evidence, don't just trust it.** Open `installer-verify.json` and
   `installer-result.json` and confirm:
   - `token_scan.residues` is an empty list;
   - every entry in `settings_hooks` has `"exists": true`;
   - `skill_collisions` is empty. **This replaces any instruction to Glob
     `~/.claude/skills` or any home-directory path** — collision detection is the
     installer's job now (it already ran the same Glob at step 6 and recorded the
     result). Any Glob you run at this step must stay bounded to the install root
     (`.`), never `~`.

   If any of the three is non-empty / false, stop and report it — do not patch around
   it.

   **b. Then run these three GENUINE probes yourself — the report is a claim, these are
   the check:**
   - **Re-hash 2–3 sampled files.** Pick 2–3 paths from `installer-verify.json`'s `files`
     list — the sample MUST include at least one file that went through an ADAPT
     substitution and at least one plain copy — read each file from disk, compute its
     sha256 yourself, and compare against the recorded hash. Do not re-hash the full
     list; the sample is the point.
   - **Run your own `{{TOKEN}}` grep.** Scan the installed tree for a surviving
     `{{TOKEN}}` placeholder yourself, excluding `HARNESS-VERSION.md` and
     `HARNESS-INSTALL-REPORT.md` (their ADAPT-values tables legitimately document
     `{{TOKEN}}` literals in prose — that's documentation, not a residue). This is a
     second, independent look at the same claim `token_scan.residues` already made empty
     — not a re-trust of it.
   - **Trace ONE import chain end-to-end.** Pick one entry from `settings_hooks`, follow
     it from `.claude/settings.json` to the hook script it names, open that script, and
     confirm every `lib.`-style import it makes (`from lib.X import ...`, `from .X
     import ...`, `from . import ...`, `from lib import ...`, `import lib...`) resolves
     to a file that actually exists on disk. Do not re-trace every hook — one full chain
     proves the shared code path works; `settings_hooks[].exists` already covers the
     rest.

   **Do NOT**, at this step: re-derive the full file inventory (that's what `files` in
   `installer-verify.json` is for), re-hash every file (the sample in (b) is the check),
   or re-trace every hook's import chain (one full trace in (b) is the check). The
   evidence file covers breadth; your spot-checks prove the shared code path is sound —
   spending tokens re-deriving what the evidence file already states is exactly the
   waste this step exists to avoid.

   Use Read and Glob for all of this, plus the sha256/grep probes in (b). Do not reach
   for any other shell command here.

8. **New session — verify and smoke-test.** After the restart, the **member** (this is a
   human action; you cannot read it) confirms hook registration by running `/hooks`. Then
   run the smoke test for the resolved rigor level (see the Smoke tests section). A hook
   **actually firing** during the smoke test is the real proof of registration — presence
   in a list is not. Append the smoke-test result to `HARNESS-INSTALL-REPORT.md`.

**If `installer.py` cannot run** (no Python 3 available, or an environment restriction
blocks running a script) — see `## Fallback — manual install` at the end of this file for
the original Read/Write/Glob-only flow. Do not silently fall back; report the blocker to
the member first, then offer the fallback as their explicit choice.

---

## 3. CLAUDE.md and .gitignore assembly

CLAUDE.md (and, per (e) below, `.gitignore`) is assembled at step 6, not blindly
copied. Detect which case you are in first, then follow the matching rule.

**(a) Fresh repo (no existing CLAUDE.md).** The `00-core` module ships
`CLAUDE-skeleton.md` at the module level (`modules/00-core/CLAUDE-skeleton.md`, beside
its `README.md` — not under `files/`, since it is an assembly input this step consumes,
never a payload file copied to the destination as-is). Fill it with: the
`claude-md-block.md` blocks contributed by the selected modules (nothing from an
uninstalled module ever appears) for the HARD-RULES slot; the per-rigor
`00-core/workflow-table-<RIGOR>.md` snippet for the WORKFLOW-TABLE slot; and the
auto-generated `docs/harness/<module>.md` pointer rows (one per installed module that
ships one, skipping the pre-seeded `00-core` row) for the DETAIL-DOCS-POINTER-TABLE
slot — `installer.py`'s `assemble_claude_md` is the normative implementation of this
rule (spec §4 step 3). Keep the
result lean: any block longer than roughly ten lines goes to a detail doc under
`docs/harness/<module>.md` with a one-line pointer left in CLAUDE.md, never inlined.
Record `claude_md_mode: fresh` in `HARNESS-VERSION.md`.

**(b) Existing CLAUDE.md (merged case).** **Never restructure the member's own
content.** Append exactly one delimited section, wrapped in these literal marker lines
(shown fenced here for rendering clarity; the member types them verbatim, and they are
plain HTML-comment markers — not recompute directives, so they need no other handling):

```
<!-- BEGIN handoff-kit harness v<X> -->
... the kit-owned CLAUDE.md section, assembled from selected modules' blocks ...
<!-- END handoff-kit harness -->
```

Record `claude_md_mode: merged`. Everything the member wrote stays exactly where it was;
the harness lives entirely between those two markers.

**(c) Update-mode hash rule for the merged case.** When you later re-hash a merged
CLAUDE.md to check for drift, the hash is **section-scoped**: hash only the bytes
**between** the marker lines, with the marker lines themselves excluded. That way a
member editing their own content outside the region never trips the drift check, while
an edit **inside** the harness region flags as member-modified under the normal update
rule.

**(d) Context-budget guidance (cut-time, not an install gate).** Kit-owned CLAUDE.md
content is kept within a per-tier budget — roughly ≤60 lines for LIGHT, ≤150 for
STANDARD, ≤300 for FULL. This budget is enforced **when the kit is authored** (the
modules' `claude-md-block.md` blocks and their detail docs are written to fit). The
installer never authors or relocates content to hit a budget at install time; it only
copies and assembles what was already cut to fit.

**(e) `.gitignore` assembly.** The owner wants the harness itself, and the Claude-
generated working docs it produces, kept out of the pushed repo. `00-core` ships a
second assembly input beside `CLAUDE-skeleton.md`: `gitignore-block.md`
(`modules/00-core/gitignore-block.md`, module-level, not under `files/` — never
deposited at the destination as a stray file, same discipline as the skeleton). Apply
the identical fresh-vs-merged discipline used for CLAUDE.md above:

- **Fresh (no existing `.gitignore`).** Create one. Write the delimited section (see
  markers below) containing `gitignore-block.md`'s content verbatim — there is no
  member content to protect, but wrapping it in the same markers keeps a later add-on
  update able to find the section the same way regardless of which case the original
  install landed in.
- **Merged (a `.gitignore` already exists).** **Never restructure the member's own
  entries.** Append exactly one delimited section at the end of the file, wrapped in
  these literal marker lines (plain `#`-comment lines, valid `.gitignore` syntax — not
  recompute directives):

  ```
  # BEGIN handoff-kit harness
  ... gitignore-block.md's content, verbatim ...
  # END handoff-kit harness
  ```

The shipped block ignores `.claude/` (the installed hooks/skills/state — the harness
itself stays untracked) plus `docs/superpowers/briefs/` (ephemeral Claude-generated
working notes — standing briefs). **`docs/analyses/` is deliberately NOT ignored** —
see `gitignore-block.md`'s own note: module 30's data-analysis playbook nudge detects
that shape from the COMMITTED git diff, so its dossiers must stay tracked or the nudge
silently never fires. Ignore it only if you also retarget that detection to the working
tree.

**Judgment call, flagged for owner confirmation:** which doc directories count as
"ephemeral" versus "deliverable" is project-specific — the shipped list is a reasonable
default, not a fixed policy. The member can add or remove lines inside the delimited
section on any later pass; deliverable docs (specs, PM/status reports, ticket files)
should stay tracked and are deliberately not on this list.

**(f) Update-mode hash rule for the merged `.gitignore` case.** The same discipline as
(c) applies here: when you later re-hash a merged `.gitignore` to check for drift, the
hash is **section-scoped**: hash only the bytes **between** the `# BEGIN handoff-kit
harness` / `# END handoff-kit harness` marker lines, with the marker lines themselves
excluded. That way a member editing their own entries outside the region never trips
the drift check, while an edit **inside** the harness region flags as member-modified
under the normal update rule.

---

## 4. Update mode and post-install changes

Once the harness is installed, later kit versions and later add-ons flow through one
consistent mechanism. The core idea: know exactly what the member has changed, and
never overwrite a member's edit.

**(a) Two hash sets — do not confuse them.** The kit carries `FILE-MANIFEST.json`, a
**cut-time** hash of every file inside `handoff-kit/`. Its only job is transport
integrity: confirming the kit arrived unmodified. It is **not** the update baseline.
The real update baseline is the **post-ADAPT** per-file hash set recorded in the
adopter's `HARNESS-VERSION.md`, written by `installer.py` at step 6 — computed **after**
that same step's ADAPT substitutions. The cut-time hashes cannot serve as the update
baseline, because an
ADAPT-touched file legitimately differs from its template the moment it is installed;
only a hash taken after ADAPT describes the file as it actually landed.

**(b) Update procedure.** For each file a new kit version would replace: compute the
`shasum` of the currently-installed copy and compare it to the recorded post-ADAPT
baseline for that file.
- **Match** (member has not touched it): replace it with the new kit's file, re-apply
  that file's ADAPT substitutions, and re-record the new post-ADAPT hash as the
  baseline.
- **Mismatch** (member has edited it): **flag it as member-modified and never
  overwrite.** The member decides, per file, whether to keep their version or take the
  new one.

**(c) Merged-CLAUDE.md exception.** When updating a merged CLAUDE.md and the
section-scoped hash matches, **splice** the new kit-owned section in between the
existing BEGIN/END markers — never whole-file replace. If a marker is missing or
duplicated, the harness region is undefined: treat it as member-modified, flag it, and
touch nothing.

**(d) Add-ons and overrides after install.** Adding a module later is the **identical**
mechanical step: copy its `files/`, merge its `settings-fragment.json`, apply its ADAPT
notes, record the post-ADAPT hash baseline for the new files, and append the change to
`HARNESS-VERSION.md`. A rigor upgrade (say STANDARD → FULL) is just installing the delta
modules the same way. Accepting a previously-flagged member-modified file's new-kit
version follows the match path: replace, re-apply ADAPT, re-record.

**(e) Re-interview only on changed answers.** If the member's interview answers have not
changed, reuse the recorded manifest — do not re-run the interview. Re-interview only
when an answer actually changes.

---

## 5. Bounded-shell self-check

Steps 1–5 are deliberately tool-driven — Read, Write, Glob, no shell. Step 6 is the
**one** disclosed shell command the whole flow issues: the `installer.py` invocation.
Verification (step 7) is a bounded set of seeded spot-checks against `installer.py`'s own
output (`installer-verify.json` and `installer-result.json`) — mostly Read and Glob
(check file existence with Glob, read contents and reason about imports/references with
Read), plus a small, explicitly bounded set of hand-run probes: re-hashing 2–3 sampled
files (`hashlib.sha256`/`shasum`, never the full file list) and one `{{TOKEN}}` scan over
the installed tree. Those probes are the disclosed exceptions at this step — there is no
open-ended shell scanning step at self-check, only the named, bounded ones in step 7.

Inside `installer.py`, the two disclosed exceptions are:

- `git init` — the script's sole `subprocess` call, run at step 6 when the destination
  has no repo yet. The session never shells this out directly.
- hashing — the post-ADAPT baseline `installer.py` writes into `HARNESS-VERSION.md`, and
  the update-mode compare (section 4b), are both `hashlib.sha256` calls inside the
  script, **not** the `shasum` binary.

No shell command beyond the one `installer.py` invocation and step 7's bounded
re-hash/`{{TOKEN}}`-scan probes appears anywhere in the install flow — no direct `find`,
`diff`, `cp`, or `git` call from the session, and no unbounded `grep`/`shasum` sweep over
the whole destination. Copying and assembly are Write/Read/Glob or delegated into that
one disclosed script invocation; self-check is Read/Glob plus the two named, sample-sized
probes in step 7.

---

## 6. Model availability — honesty rule

The routing profile you install assumes a set of model seats. Be honest with the member
about what can and cannot be checked:

- **There is no model-list enumeration surface.** `/model` is a human picker, and
  `/status` shows only the current model. No API or command lists which seats this
  account may dispatch. An agent cannot detect availability, and this kit claims no such
  detection.
- **A blocked model does not error.** A dispatch requesting a model the account cannot
  use does **not** fail — it silently falls back to the inherited or default model. The
  CLI surfaces a substitution notice that a human can see; an agent cannot rely on it.
- **Therefore the routing table is authoritative at install.** The routing profile
  (keyed by the interview's model-access question) is the source of truth for what to
  install. If the member's plan or organization restricts a seat's model, tell them to
  **drop the routing profile one tier** rather than trusting silent substitution.
- **Never block the install on an availability doubt.** Availability cannot be verified
  from inside a session, so uncertainty about it is never a reason to halt. Install per
  the routing table and note the substitution caveat in the report.

---

## 7. Smoke tests

After the restart (step 8), run the smoke test for the resolved rigor level. Each level
has its own procedure; run only the one that matches.

**LIGHT.** Build a toy skill and exercise it against a single fixture — a sample input
paired with its expected output — and confirm the skill's output matches. This procedure
is self-contained here and has **no dependency on the fixture-testing module** (that
module installs only when the member opts into it); LIGHT must be able to smoke-test on
bare Claude Code.

**STANDARD.** Run a micro-change — the smallest, T1-style edit — all the way through the
pipeline end to end: change → gate → test → commit. On the github routing variant, the
final step pushes to the configured remote.

**FULL.** Run a T1-shaped change through the **shape** of the full pipeline: a spec stub
→ implement → one audit round → ship via the installed ship skill variant. State plainly
in the report that this is **not** a full production run: the deeper loops (the
effect-mapping loop and the sentinel gate) are validated by **presence and invocation** —
the skill loads and its first step engages — **not** by full convergence. Record that
limit in the install report.

---

## 8. Enforcement honesty statements

Two statements about how strongly the harness actually enforces things. Read them to the
member; do not overstate what the kit does.

**Sentinel enforcement strength.** When an advisor tool is present, the gate-evidence
check (the sentinel module) is **gate-grade**: it is forge-resistant and
transcript-visible, so the evidence of a gate having run cannot be fabricated. When the
same role is filled by a subagent seat instead, the check is a **WARN-grade convention**
that the orchestrator could forge. The kit says this plainly rather than claiming
gate-grade enforcement in a configuration that only supports a convention.

**Anti-hallucination-stack limit.** The harness stacks several defenses — never-assume
plus confidence labels (`00-core`), the citation guard plus the confidence-label scan
(the guards module), fresh-context review at gates (the sentinel module), test-driven
development plus fixture tests (the TDD and skill-delivery modules), and the audit and
effect-mapping loops (the review-loop module). Together these **reduce and catch**
hallucinations. No configuration of this kit makes hallucinations "non-existent," and the
kit does not claim it does.

---

## 9. Risks and honest limits

Install with these limits in view, and pass them to the member:

- **Hooks are fail-open by design.** A hook that errors allows the action rather than
  blocking it. That lowers the risk of a hook wedging your workflow; it does **not**
  eliminate the risk the hook was meant to catch.
- **Data-handling controls reduce exposure, they do not guarantee safety.** The
  data-handling module's deny-list, synthetic fixtures, and WARN hook lower the chance
  sensitive data leaks, but regex-based PII detection is imperfect and cannot guarantee
  a clean result.
- **The anti-hallucination stack has limits** (see the Enforcement honesty statements
  above) — it reduces and catches, it does not eliminate.
- **Plan limits may force session splitting.** Even with the lean CLAUDE.md rules, a Pro
  plan's context and usage limits can force you to split work across sessions.
- **Model availability drifts silently** (see the Model availability section) — seats
  can change under you with no error surfaced to the agent.
- **The skill-delivery module is unproven content**, and is flagged as such inside the
  kit; treat what it installs as a starting point, not a validated result.
- **The kit is a snapshot.** Its `VERSION.md` records the commit it was cut from. It does
  **not** track the source project; a newer harness means a newer kit cut.

---

## 10. Coverage honesty

Be candid about how much of the configuration space has actually been exercised.

**3 of the 9** rigor × routing combinations are exercised by a dry-run plus one live
validation: LIGHT + PRO + local, STANDARD + PRO + github, and FULL + MAX5 + local. The
remaining 6 are validated **by construction** — the rigor and routing manifests are
orthogonal selections over the same shared module library, so a combination that was
never installed end to end is still assembled from modules each of which was exercised in
one of the three validated paths. That is validation by construction, not by an executed
install; the kit states this rather than implying all nine were run.

A dry run has a hard limit worth stating: the scratch dry-run folder is **never** the
build session's own root, so installed hooks and skills cannot go live during a dry run.
That means the STANDARD and FULL smoke tests are **not** executable in a dry run — only
LIGHT's fixture test truly executes there. The live-harness path (restart → `/hooks` →
smoke test) is validated once per kit cut by a human-in-the-loop real install session
opened **at** the scratch repo root.

---

## 11. Kit-authoring note — fencing directive examples

This note is for whoever later edits the kit's own docs, not for the install flow.

The harness ships a recompute-and-compare guard (the guards module) that re-runs
structured recompute directives embedded in markdown handoff files and blocks on a stale
one. Any **illustrative** directive written into a kit doc — a worked example of the
convention, not a live claim — must sit inside a triple-backtick code fence, so the guard
treats it as an example and not as an assertion to verify. For instance, an illustrative
directive is shown like this, fenced:

```
<!-- reexec:count pattern="TODO" path="src/" n="0" -->
```

The same discipline covers this file: every example directive here is fenced, and the
BEGIN/END CLAUDE.md and `.gitignore` markers in section 3 are fenced for rendering
clarity even though they are plain HTML/`#` comments rather than directives. When you
edit a kit doc, re-check that every illustrative directive is inside a fence before you
save.

---

## Fallback — manual install

`installer.py` (§2 step 6) is the primary install path (spec F5). This section is the
original Read/Write/Glob-only manual flow, preserved for the rare case `installer.py`
cannot run in this environment. Every rule below is IDENTICAL in substance to what
`installer.py` now does mechanically — read this section only if you were told to use it.

6. **Copy each selected module's `files/` into place — with the Write tool, no bash.**
   For each module in the resolved set, copy its `files/` payload to the destination,
   with two renames applied at copy time:
   - **Dot-staging rename.** Any path segment staged with a `dot-` prefix is renamed
     back to a literal dot on the way in — `dot-claude/` becomes `.claude/`, a
     `dot-gitignore` payload becomes `.gitignore`, and so on. The kit stages dotted
     destinations this way so the kit's own skills do not go live inside the kit, and
     so dotfile directories survive zip round-trips; you reverse it here.
   - **Flag-variant rename.** For a skill that ships flag variants, copy **exactly the
     one variant chosen at step 5** for each destination, renaming its
     `-lite` / `-full` / `-github` / `-local` suffix to the literal `SKILL.md`. Copy
     one variant per destination, never more than one.
   - **Q3-conditional file, same discipline.** A module can also gate a single plain
     file on the interview answer rather than a skill's rigor/routing variant — module
     `25-ticketing` ships `files/tickets/README-template-local.md`, suffixed the same
     way as a flag variant. Copy it to the destination as `tickets/README-template.md`
     **only** when Q3 resolves to the local-folder ticketing variant; when Q3 resolves
     to the github-issues variant, there is no counterpart file and you copy nothing
     under `tickets/` at all.

   **Assembly inputs are not payload.** Two files exist to be *consumed* by this step,
   not copied verbatim to the destination: `00-core/CLAUDE-skeleton.md` (module-level,
   sitting beside that module's `README.md` — not under its `files/` payload directory)
   and every installed module's own `claude-md-block.md` (same: module-level, not under
   `files/`). Neither is part of any module's `files/` copy — do not deposit
   `CLAUDE-skeleton.md` or a `claude-md-block.md` at the destination as a stray file.
   Instead, **assemble CLAUDE.md** per the CLAUDE.md assembly rules below: detect the
   fresh-vs-merged case **first**, then either skeleton-fill (fresh repo, reading the
   skeleton from `00-core/CLAUDE-skeleton.md`) or delimited-section-append (existing
   CLAUDE.md).

   **Assemble `.gitignore` the same way.** `00-core/gitignore-block.md` is a third
   assembly input (module-level, beside `00-core/README.md`, not under `files/`) — copy
   nothing named `gitignore-block.md` to the destination. Detect fresh-vs-merged first,
   same as CLAUDE.md: if the destination has no `.gitignore`, create one; if it already
   has one, append a delimited section — **never restructure the member's existing
   entries.** See §3(e) below for the exact marker lines and section content.

   **Assemble `.claude/settings.json` the same way.** Every selected module's own
   `settings-fragment.json` (module-level, beside that module's `README.md` — not under
   `files/`) is a further assembly input. Like `CLAUDE-skeleton.md` and
   `gitignore-block.md`, `settings-fragment.json` is an assembly input consumed here —
   **never** copied to the destination as payload; do not deposit a stray
   `settings-fragment.json` anywhere under the destination. Instead, assemble
   `.claude/settings.json` by merging every **selected** module's `settings-fragment.json`
   into it: create the file if it does not already exist, and **deep-merge the `hooks`
   object** so that multiple modules' `PreToolUse` / `Stop` / `SubagentStop` entries all
   coexist — append each module's entries under the matching event-type key rather than
   letting a later module's fragment silently overwrite an earlier module's entries
   (e.g. `10-hooks-base` contributes a `PreToolUse` entry, `23-guards` contributes `Stop`
   and `SubagentStop` entries, and `27-data-handling` contributes a second,
   differently-matchered `PreToolUse` entry — all three must be present in the merged
   result when their modules are selected). Skip this sub-step only if no selected
   module ships a `settings-fragment.json`. This is the step section 4(d) above already
   assumes exists ("Adding a module later is the **identical** mechanical step: copy its
   `files/`, merge its `settings-fragment.json` …") — without it, no selected module's
   hooks are ever registered and the harness installs dead.

7. **Apply each module's ADAPT notes.** Each module's `README.md` lists the values a
   new repo must substitute — project name, stack commands (test / lint / typecheck),
   your risk-sensitive path prefixes (`RISK_PREFIXES`), and similar. Apply every ADAPT
   substitution the installed modules declare.

8. **`git init` if no repo exists.** If the destination is not already a git
   repository, initialize one. This is **shell exception #1** — one of the only two
   shell commands the install flow runs.

9. **Self-check — Read / Glob only.** With no shell beyond the one disclosed exception
   already run (`git init`, at step 8), verify the manual install landed by re-reading
   what you just wrote in steps 6–8. There is no `installer-result.json` on this path —
   every check below is a direct Read/Glob against the destination, not a re-trust of a
   script's own claim:
   - every file each selected module's `files/` payload was supposed to copy — plus the
     assembled `.claude/settings.json`, `CLAUDE.md`, and `.gitignore` from step 6 — actually
     exists at its destination, with the dot-staging and flag-variant renames correctly
     applied;
   - no `{{TOKEN}}` placeholder survives anywhere in the destination — re-read every file
     you wrote or assembled at step 6 and confirm no ADAPT substitution from step 7 was
     left unresolved;
   - the transitive import closure of **every** copied `.py` — the dispatcher **and** the
     standalone Stop / SubagentStop hooks — resolves against the installed module set.
     Check every lib-referencing import form the payload might use: `from lib.X import
     ...`, `from .X import ...`, `from . import ...`, `from lib import ...`, and `import
     lib...` (defensive, not exhaustive — read what the files actually import);
   - `.claude/settings.json` parses as valid JSON and contains a `PreToolUse` /
     `Stop` / `SubagentStop` entry for every selected module that ships a
     `settings-fragment.json`, correctly deep-merged (per step 6's merge rule) rather than
     overwritten, and references no script that was not shipped;
   - **the skill-collision Glob.** For each installed skill, Glob **both**
     `~/.claude/skills/<name>/` and `~/.claude/skills/<name>.md`. A hit on either path for
     a skill you just installed is a collision with a pre-existing global skill of the
     same name — note it; step 11's install report surfaces it to the member as a WARN.

   Use Read and Glob for all of this. Do not reach for a shell command here.

10. **Write `HARNESS-VERSION.md`.** Record: the kit version, the chosen profiles, any
    overrides and add-ons, the ADAPT values you substituted, the install date, the
    `claude_md_mode` (fresh or merged), and the **post-ADAPT per-file hash baseline**.
    The hash rules — which files, computed when, with what tool — are in the Update mode
    section below; apply them from there rather than restating them inline.

11. **Write the install report.** List: the modules installed, the ADAPT edits you
    made, the decisions that fell back to a default, any overrides or add-ons applied,
    and any skill-collision WARNs found at step 9. Then instruct the member to
    **restart the Claude Code session** — a top-level `.claude/skills/` directory
    created mid-session is only discovered after a restart, so the harness is not live
    until the session is restarted.
