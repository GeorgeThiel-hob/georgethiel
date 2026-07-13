### Guard pack (23-guards)

WARN-first-before-BLOCK is the pattern for introducing any NEW gate: ship the
check as a non-blocking WARN, promote to BLOCK only after measurement. Of
this module's 4 guards, three are WARN-/log-grade (claim-binding guard +
circularity guard WARN, confidence-label scan log-only); the citation guard
is the mature exception — it ships BLOCK-grade (default `block`, stops a turn
after ≥2 ungrounded-claim flags) because it has already earned it.

Full guard descriptions + import-closure map: `docs/harness/23-guards.md`.
