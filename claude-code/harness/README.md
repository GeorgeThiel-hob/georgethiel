# Claude Code Workflow Harness

This is the full workflow harness behind the skills in
[`../skills/`](../skills/): the hooks, skills, `CLAUDE.md` rules, and profiles
that turn a bare repository into one that runs a disciplined build pipeline
(tiered tickets, spec → plan → implement → audit → ship gates, model routing,
and evidence-backed review gates).

It's a **snapshot** — a self-contained kit you install into a target repo. It
does not auto-sync with the project it was cut from; its version and cut
provenance are recorded in [`VERSION.md`](VERSION.md). Nothing here trades,
ships, or mutates anything outside the repo you install it into — installation
is copy, merge, rename, and hash, run by one disclosed shell command.

## Quickstart

The installer is **interview-first** — it does not run bare. Both `--spec` and
`--dest` are required, and the spec is produced by an interview, not written by
hand:

1. **Download or clone this `harness/` directory** into a working location.
2. **Run the interview.** Have a Claude Code session read
   [`interview/INTERVIEW.md`](interview/INTERVIEW.md) and, following
   [`START-HERE.md`](START-HERE.md), resolve your answers into an
   `install-spec.json`.
3. **Install:**
   ```bash
   python3 installer.py --spec install-spec.json --dest <target-repo>
   ```
4. **Restart Claude Code** in the target repo. The harness is hooks + skills +
   `CLAUDE.md` rules that Claude Code only loads at session start — it is **not
   live until you restart** (see `INSTALL-GUIDE.md`, final step).
5. **Uninstall** (clean removal, manifest-guarded):
   ```bash
   python3 uninstall.py --dest <target-repo>
   ```

## A note on folder names

The deep docs in this directory — [`START-HERE.md`](START-HERE.md) and
[`INSTALL-GUIDE.md`](INSTALL-GUIDE.md) — refer to the kit as `handoff-kit/`
(e.g. `python3 handoff-kit/installer.py …`), because that's the directory name
the kit is cut into. In this repo the exact same tree lives at
`claude-code/harness/`. So when those docs say `handoff-kit/`, read it as
`claude-code/harness/` — or just run the commands from inside this directory,
where the paths are relative and match as-is.

## Where to read next

- **[`START-HERE.md`](START-HERE.md)** — the full normative install flow (read
  this completely before installing).
- **[`INSTALL-GUIDE.md`](INSTALL-GUIDE.md)** — the short "what to run and when"
  companion for the person acting on the steps.
- **[`VERSION.md`](VERSION.md)** — kit version and cut provenance.

This `README.md` is an addition on top of the kit's pinned file set. It is
intentionally not listed in `FILE-MANIFEST.json`; the integrity self-check
iterates from the manifest to disk (not the reverse), so an extra file like this
one does not fail it.
