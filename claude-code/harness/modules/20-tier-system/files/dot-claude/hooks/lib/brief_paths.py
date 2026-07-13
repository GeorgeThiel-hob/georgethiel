from pathlib import Path


def resolve_brief_path(slug: str, repo_root: Path) -> Path:
    """Resolve a standing-brief path, normalizing slug form + filename.

    Accepts slug as the full branch-slug ('feature-X') or the post-'feature/'
    core ('X'). The AS-IS name is the primary and the missing-both default;
    the alternate form (stripped for a feature-slug, 'feature-'-prepended for a
    core/non-feature slug) is only SEARCHED. So this is byte-identical to legacy
    `_brief_path` for any slug — a non-feature slug never gets a spurious
    'feature-' prepended into the default (N12). Always absolute under repo_root.
    """
    briefs_dir = repo_root / "docs" / "superpowers" / "briefs"
    if slug.startswith("feature-"):
        candidates = [slug, slug[len("feature-"):]]   # feature-X.md, then X.md
    else:
        candidates = [slug, f"feature-{slug}"]         # X.md (or hotfix-Y.md), then feature-X.md
    for name in candidates:
        path = briefs_dir / f"{name}.md"
        if path.exists():
            return path
    return briefs_dir / f"{candidates[0]}.md"  # default = as-is primary (legacy)
