#!/usr/bin/env python3
"""DEBATE — multi-agent debate orchestrator.

Spawns N Claude instances that debate a topic across multiple rounds, then synthesizes a
final answer from the full transcript.

Persona pool is loaded from the shared `personas.json` (one directory up from this
skill's own directory — shared with the COUNCIL skill). ADAPT: edit personas.json to
add/replace personas for your own domain; no code change is needed in this file.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Windows App Execution Aliases (e.g. claude) are GUI-session stubs that resolve
# via shutil.which but fail to execute in non-interactive subprocesses (exit 127).
# _find_claude() probes candidates in order; the first that actually runs wins.


def _claude_candidates() -> list[str]:
    """Build candidate list, including version-agnostic Windows glob expansion."""
    candidates = ["claude"]
    # Dynamically discover versioned install dirs under AppData/Roaming/Claude/claude-code/
    roaming = Path.home() / "AppData" / "Roaming" / "Claude" / "claude-code"
    if roaming.exists():
        for versioned in sorted(roaming.iterdir(), reverse=True):
            exe = versioned / "claude.exe"
            if exe.exists():
                candidates.append(str(exe))
    return candidates


def _find_claude() -> str:
    """Return the first claude binary that can actually be executed."""
    candidates = _claude_candidates()
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return candidate
        except (FileNotFoundError, OSError):
            continue
    raise RuntimeError(
        "No working claude CLI found. Checked: " + ", ".join(candidates)
    )


_CLAUDE_BIN: str | None = None


def _claude_bin() -> str:
    global _CLAUDE_BIN
    if _CLAUDE_BIN is None:
        _CLAUDE_BIN = _find_claude()
    return _CLAUDE_BIN


def _load_persona_pool() -> dict[str, tuple[str, str]]:
    """Load the shared persona pool from personas.json (one directory up from this
    skill's own directory — .claude/skills/personas.json, shared with the COUNCIL skill).
    Returns {key: (display_name, focus_description)}."""
    personas_path = Path(__file__).resolve().parent.parent / "personas.json"
    with personas_path.open() as fh:
        data = json.load(fh)
    return {p["key"]: (p["name"], p["focus"]) for p in data["personas"]}


_PERSONA_POOL: dict[str, tuple[str, str]] = _load_persona_pool()

# Persona profiles: ordered list of pool keys, front-loaded with the most relevant
# perspectives. --agents N uses the first N from the profile order. Keys reference
# personas.json — see that file's ADAPT note to add/replace personas for your domain.
PERSONA_PROFILES: dict[str, list[str]] = {
    # Strategic/positioning decisions, sizing, expected value, live parameters — lead
    # with edge-seeking vs risk tension
    "strategy": [
        "domain_strategist",
        "risk_manager",
        "quantitative_analyst",
        "systems_architect",
        "ai_prompt_engineer",
    ],
    # Code design, architecture, module structure, testing — lead with builders
    "code": [
        "systems_architect",
        "ai_prompt_engineer",
        "domain_strategist",
        "quantitative_analyst",
        "risk_manager",
    ],
    # Data quality, calibration, statistical analysis, validation methodology — lead with rigor
    "data": [
        "data_calibration_analyst",
        "risk_manager",
        "domain_strategist",
        "systems_architect",
        "ai_prompt_engineer",
    ],
    # Risk tolerance, allocation limits, correlated exposure — lead with risk lens
    "risk": [
        "risk_manager",
        "quantitative_analyst",
        "domain_strategist",
        "systems_architect",
        "ai_prompt_engineer",
    ],
    # Agent/skill/Claude Code design — lead with AI tooling layer
    "tooling": [
        "ai_prompt_engineer",
        "systems_architect",
        "quantitative_analyst",
        "domain_strategist",
        "risk_manager",
    ],
    # Balanced — default order, all topics
    "mixed": [
        "domain_strategist",
        "risk_manager",
        "quantitative_analyst",
        "systems_architect",
        "ai_prompt_engineer",
    ],
    # Rollout/deployment execution under resource-constrained or contended conditions —
    # execution-first personas for outcome-capture-tactics debates
    "execution": [
        "execution_strategist",
        "latency_systems_engineer",
        "reliability_engineer",
        "domain_strategist",
        "risk_manager",
    ],
}

PERSONAS = [_PERSONA_POOL[k] for k in PERSONA_PROFILES["mixed"]]


def personas_for_profile(profile: str, n_agents: int) -> list[tuple[str, str]]:
    """Return ordered persona list for a given profile, extended with Senior variants if n > 5."""
    order = PERSONA_PROFILES.get(profile, PERSONA_PROFILES["mixed"])
    base = [_PERSONA_POOL[k] for k in order]
    personas = base[:n_agents]
    if n_agents > len(base):
        for i in range(n_agents - len(base)):
            src = base[i % len(base)]
            personas.append((f"Senior {src[0]}", src[1]))
    return personas


def call_claude(prompt: str, model: str = "sonnet", timeout: int = 240, retries: int = 2) -> str:
    """Call Claude CLI as a subprocess and return the response.

    Retries up to `retries` times on transient errors (non-zero exit with
    rate-limit or internal-error signals in stderr).

    For long prompts (> 20K chars), uses stdin piping via `claude --print`
    to avoid Windows CreateProcess command-line length limit (WinError 206).
    """
    # Windows CreateProcess limit is ~32K chars total; stay safely below it.
    USE_STDIN_THRESHOLD = 20_000
    use_stdin = len(prompt) > USE_STDIN_THRESHOLD

    last_error = ""
    for attempt in range(retries + 1):
        try:
            if use_stdin:
                result = subprocess.run(
                    [_claude_bin(), "--print", "--model", model],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            else:
                result = subprocess.run(
                    [_claude_bin(), "-p", prompt, "--model", model],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
        except subprocess.TimeoutExpired:
            return f"[Error: timeout after {timeout}s]"
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                return output
            # Empty stdout with exit 0 — treat as transient
            last_error = "empty response"
        else:
            stderr = result.stderr.strip()
            last_error = stderr or "non-zero exit"
            # Only retry on likely-transient signals
            transient = any(kw in stderr.lower() for kw in ("rate limit", "internal error", "overloaded", "529"))
            if not transient:
                return f"[Error: {last_error}]"
        if attempt < retries:
            time.sleep(5 * (attempt + 1))  # 5s, 10s back-off
    return f"[Error: {last_error}]"


def run_round(
    round_num: int,
    total_rounds: int,
    topic: str,
    transcript: list[dict],
    personas: list[tuple[str, str]],
) -> list[dict]:
    """Run one debate round — all agents respond in parallel."""
    transcript_text = ""
    for entry in transcript:
        transcript_text += f"\n[{entry['persona']}] (Round {entry['round']})\n{entry['response']}\n"

    responses = []

    def agent_turn(persona_name: str, persona_style: str) -> dict:
        if round_num == 1:
            prompt = (
                f"You are '{persona_name}' in a multi-agent debate.\n"
                f"Your style: {persona_style}\n\n"
                f"## Topic\n{topic}\n\n"
                f"## Instructions\n"
                f"This is Round {round_num}/{total_rounds}. Give your opening take on the topic.\n"
                f"Be concise (3-5 paragraphs max). Commit to your perspective — don't hedge.\n"
                f"Start your response directly — do not repeat your persona name."
            )
        else:
            prompt = (
                f"You are '{persona_name}' in a multi-agent debate.\n"
                f"Your style: {persona_style}\n\n"
                f"## Topic\n{topic}\n\n"
                f"## Debate so far\n{transcript_text}\n\n"
                f"## Instructions\n"
                f"This is Round {round_num}/{total_rounds}. You've read everyone's prior responses.\n"
                f"React to what others said. Agree, disagree, build on ideas, or challenge them.\n"
                f"Be concise (2-4 paragraphs max). Push the conversation forward.\n"
                f"Start your response directly — do not repeat your persona name."
            )
        response = call_claude(prompt)
        if response.startswith("[Error:"):
            print(f"  [WARN] {persona_name} failed: {response}", file=sys.stderr)
        return {"persona": persona_name, "round": round_num, "response": response}

    with ThreadPoolExecutor(max_workers=len(personas)) as executor:
        futures = {
            executor.submit(agent_turn, name, style): name
            for name, style in personas
        }
        for future in as_completed(futures):
            responses.append(future.result())

    # Sort by persona order
    persona_order = {name: i for i, (name, _) in enumerate(personas)}
    responses.sort(key=lambda r: persona_order.get(r["persona"], 99))
    return responses


def synthesize(
    topic: str,
    transcript: list[dict],
    total_rounds: int,
    delta_annotations: list[str] | None = None,
) -> str:
    """Synthesizer agent reads full transcript and produces merged answer."""
    transcript_text = ""
    for entry in transcript:
        transcript_text += f"\n[{entry['persona']}] (Round {entry['round']})\n{entry['response']}\n"

    delta_text = ""
    if delta_annotations:
        delta_text = "\n## Round-Delta Annotations\n"
        for i, delta in enumerate(delta_annotations, 1):
            delta_text += f"\n### Round {i}\n{delta}\n"

    prompt = (
        f"You are the Synthesizer. You've observed a {total_rounds}-round debate between "
        f"multiple AI agents on the following topic:\n\n"
        f"## Topic\n{topic}\n\n"
        f"## Full Transcript\n{transcript_text}\n"
        f"{delta_text}\n"
        f"## Instructions\n"
        f"Produce a synthesis in this exact format:\n\n"
        f"## Consensus\nWhat the group agreed on.\n\n"
        f"## Key Debates\nWhere they disagreed and how it resolved (or didn't).\n\n"
        f"## Recommendation\nThe merged answer — what someone should actually do.\n\n"
        f"## Dissents\nAny unresolved disagreements worth noting.\n\n"
        f"Be concise and actionable. The user wants a clear answer, not a transcript summary."
    )
    result = call_claude(prompt, model="opus")
    if result.startswith("[Error:"):
        return f"## Synthesis Failed\n\nSynthesizer call returned an error: {result}\n\nCheck stderr for details."
    return result


# Path to this module's own standalone schema validator (module 31-debate-tools) —
# .claude/hooks/lib/schema_validator.py, resolved relative to this file so the module
# never depends on this project's own package layout (invoked as a plain script, not a
# package module).
_SCHEMA_VALIDATOR_PATH = (
    Path(__file__).resolve().parent.parent.parent / "hooks" / "lib" / "schema_validator.py"
)


def _validate_delta(delta_json: str) -> bool:
    """Validate round-delta JSON against the model_chat_delta schema.

    Returns False for empty arrays — those indicate annotation failure, not success.
    """
    try:
        parsed = json.loads(delta_json)
    except json.JSONDecodeError:
        return False
    # Empty array means annotation failed (call_claude errored); treat as invalid.
    if not parsed:
        return False
    result = subprocess.run(
        [sys.executable, str(_SCHEMA_VALIDATOR_PATH), "--schema", "model_chat_delta", "--input", delta_json],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _extract_json_array(text: str) -> str:
    """Extract a JSON array from text that may have surrounding prose.

    Returns the extracted JSON string, or '[]' if nothing parseable is found.
    """
    # Fast path: already valid JSON
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass
    # Find the outermost [...] block (greedy, handles nested objects)
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
    return '[]'


def _annotate_with_model(round_num: int, responses: list[dict], model: str = "haiku") -> str:
    """Run the round-delta annotation with a specified model."""
    round_text = ""
    for resp in responses:
        round_text += f"\n[{resp['persona']}]\n{resp['response']}\n"

    prompt = (
        f"You are a round-delta annotator. Analyze these {len(responses)} agent responses "
        f"from Round {round_num} and produce a JSON array — one entry per agent.\n\n"
        f"## Responses\n{round_text}\n\n"
        f"## Required JSON schema per entry\n"
        f'{{"round": int, "agent_id": str, "position_delta": str|null, '
        f'"key_new_argument": str|null, "concession": str|null, '
        f'"unresolved_objections": [str], "framing_shift": bool}}\n\n'
        f"Output ONLY a raw JSON array with no markdown fences, no explanation, no extra text."
    )
    raw = call_claude(prompt, model=model)
    return _extract_json_array(raw)


def main():
    parser = argparse.ArgumentParser(description="Debate — multi-agent debate")
    parser.add_argument("topic", nargs="?", help="The topic or question to debate")
    parser.add_argument("--topic-file", help="Path to a file containing the debate topic (alternative to inline topic)")
    parser.add_argument("--agents", type=int, default=5, help="Number of agents (default: 5)")
    parser.add_argument("--rounds", type=int, default=3, help="Number of rounds (default: 3)")
    parser.add_argument("--interactive", action="store_true", help="Pause between rounds for user input")
    parser.add_argument(
        "--profile",
        choices=list(PERSONA_PROFILES.keys()),
        default="mixed",
        help="Persona profile — reorders agents to front-load the most relevant perspectives. "
             "strategy: edge+risk+quant; code: infra+ai; data: quant+risk; risk: risk+quant; "
             "tooling: ai+infra; mixed: balanced default; execution: resource-constrained rollout capture tactics",
    )
    args = parser.parse_args()

    if args.topic_file:
        topic_path = Path(args.topic_file)
        if not topic_path.exists():
            print(f"[Error] --topic-file not found: {args.topic_file}", file=sys.stderr)
            sys.exit(1)
        args.topic = topic_path.read_text().strip()
    elif not args.topic:
        parser.error("Either a positional topic argument or --topic-file is required")

    personas = personas_for_profile(args.profile, args.agents)

    print(f"Debate — {args.agents} agents, {args.rounds} rounds, profile={args.profile}")
    print(f"Personas: {', '.join(p[0] for p in personas)}")
    print(f"Topic: {args.topic[:120]}{'...' if len(args.topic) > 120 else ''}")
    print("=" * 60)

    transcript: list[dict] = []
    delta_annotations: list[str] = []
    steer_context = ""

    for round_num in range(1, args.rounds + 1):
        print(f"\n=== Round {round_num}/{args.rounds} ===\n")

        if steer_context:
            # Inject user steering as a special transcript entry
            transcript.append({
                "persona": "Moderator",
                "round": round_num - 1,
                "response": f"[User guidance]: {steer_context}",
            })
            steer_context = ""

        responses = run_round(round_num, args.rounds, args.topic, transcript, personas)

        failed = [r for r in responses if r["response"].startswith("[Error:")]
        if len(failed) == len(responses):
            print(f"\n[FATAL] All {len(responses)} agents failed in round {round_num}. Aborting.", file=sys.stderr)
            print("Check that `claude` CLI is accessible and model aliases are valid.")
            sys.exit(1)

        for resp in responses:
            print(f"[{resp['persona']}]")
            print(resp["response"])
            print()
            transcript.append(resp)

        # Haiku round-delta annotation with 3-step escalation
        delta = _annotate_with_model(round_num, responses, model="haiku")
        delta_valid = _validate_delta(delta)
        if not delta_valid:
            print("[Round-Delta] Haiku validation failed — re-prompting Haiku...")
            delta = _annotate_with_model(round_num, responses, model="haiku")
            delta_valid = _validate_delta(delta)
        if not delta_valid:
            print("[Round-Delta] Haiku retry failed — escalating to Sonnet...")
            delta = _annotate_with_model(round_num, responses, model="sonnet")
            delta_valid = _validate_delta(delta)
        if not delta_valid:
            print("[Round-Delta] Sonnet validation failed — skipping delta for this round.")
            delta = "[]"
        delta_annotations.append(delta)
        print(f"[Round-Delta] {delta}\n")

        if args.interactive and round_num < args.rounds:
            print("-" * 40)
            user_input = input("Continue (c), steer (s), or stop (x)? ").strip().lower()
            if user_input == "x":
                print("\nStopping early — moving to synthesis...")
                break
            elif user_input == "s":
                steer_context = input("Steering guidance: ").strip()

    print(f"\n{'=' * 60}")
    print("=== Synthesis ===\n")
    synthesis = synthesize(args.topic, transcript, args.rounds, delta_annotations)
    print(synthesis)


if __name__ == "__main__":
    main()
