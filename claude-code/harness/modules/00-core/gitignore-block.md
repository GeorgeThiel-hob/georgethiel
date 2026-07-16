# The harness itself: installed hooks, skills, and state — kept untracked by design.
.claude/

# Ephemeral Claude-generated working notes — adjust freely; a starting default, not a
# fixed policy. Keep deliverable docs (specs, PM/status reports, ticket files) tracked.
docs/superpowers/briefs/
# NOTE: docs/analyses/ is deliberately NOT ignored. Module 30's data-analysis playbook
# nudge detects that shape from the COMMITTED git diff, so its dossiers must stay
# tracked or the nudge silently never fires. Ignore it only if you also retarget that
# detection to the working tree.

# Python bytecode caches — never track.
__pycache__/
