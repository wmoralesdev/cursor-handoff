---
name: cursor-handoff
description: Plan and hand off a coding task to one or more Cursor CLI agents with selectable models, then inspect their results. Use only when explicitly invoked as $cursor-handoff.
license: MIT
---

# Cursor handoff

Use this skill only when the user explicitly invokes `$cursor-handoff`. It is an agent-neutral workflow for planning, launching Cursor CLI agents, and checking their work. Invocation does not by itself authorize commits, pushes, deployments, or other external actions; follow the user's actual task scope.

## Choose the requested behavior

- Default for an implementation request: The coordinating assistant plans, Cursor implements, and the coordinating assistant verifies and reports.
- If the user asks for planning only, produce the plan and stop before launching Cursor.
- For an existing plan, validate it against the current checkout and hand it off without repeating the planning work.
- For review, critique, or comparison, run Cursor in read-only `ask` or `plan` mode and report findings without applying edits.
- Support multiple Cursor agents or models when requested. Give each agent a distinct assignment and model. In one checkout, run agents that write files sequentially; independent read-only agents may run together. Agents assigned to separate repositories may run independently. Use Cursor worktrees only when the user asks for them.

## Prepare the handoff

1. Inspect the target repository's instructions, branch, HEAD, and working-tree status. Preserve existing changes. Identify the requested outcome, boundaries, dependencies, and meaningful validation.
2. Write a concise handoff Markdown file in a writable task workspace or temporary directory. Include the objective, target repository, current context, implementation or review assignment, acceptance criteria, checks, and any explicit restrictions. For multiple agents, make a separate handoff file per assignment. Refer to repository files by path rather than copying large source excerpts.
3. Check `command -v agent`, `agent --version`, `agent status`, and `agent models` or `agent --list-models`. Authentication and model availability are account-specific. If a sandboxed check cannot reach the Cursor API, retry the same check directly on the host with appropriate execution permission before treating it as an authentication blocker. The user's supplied model list helps identify candidates but may become stale. If the host CLI is unauthenticated or cannot list models at launch time, report the blocker and retain the prepared plan; do not guess that a model is available or launch a substitute.

## Select models

- Honor an exact model requested by the user. Confirm its CLI identifier in the current `agent models` output. If absent, report that and ask for a choice instead of silently replacing it.
- Without a specified model, use `cursor-grok-4.6-xhigh-fast` (Grok 4.6 Extra High Fast). If unavailable in the live model list, report that and ask for a choice instead of silently replacing it.
- Recheck the live list on each new handoff. Use the exact CLI variant identifier, including the `cursor-` prefix and `-xhigh-fast` suffix for the default model; do not infer identifiers from model display names.
- Allow the user to choose a different model per agent or phase. Record the actual model for each run.

## Launch and verify

- Prefer headless runs. Resolve `scripts/run_cursor.py` relative to this skill directory and run it with `--workspace`, `--model`, `--prompt-file`, and `--mode`. The script invokes `agent` without a shell, passes `--trust` to acknowledge the selected workspace in headless mode, and captures stdout as `stream.jsonl`, stderr, exit code, and terminal result. `--trust` only clears Cursor's workspace trust prompt; it is separate from permission to edit files or run commands. Use `--allow-writes` only for an authorized implementation; it passes Cursor's `--force`, which allows direct changes in headless mode. Respect the coordinating assistant's filesystem and network permissions when launching the subprocess.
- Do not use `--worktree` by default. Do not add unrelated workspace directories. If multiple agents must edit the same checkout, wait for one to finish and review its diff before starting the next.
- While a long run is active, monitor its log and keep the user informed. A started process is not a completed handoff. On completion, check both the process exit code and the terminal `result` event. Treat a missing result, errors, or stalled run as incomplete.
- Compare the resulting working tree with the baseline. Review the diff and relevant tests or checks yourself. Treat Cursor's summary as a claim to verify. Report the plan, model(s), run status, changes, checks, and remaining issues. Avoid making a commit, PR, push, or deployment unless the user requested it.

## CLI references

- `agent --help`, `agent models --help`, `agent status`, `agent models`
- [Cursor CLI parameters](https://cursor.com/docs/cli/reference/parameters)
- [Headless CLI](https://cursor.com/docs/cli/headless)
- [Output format](https://cursor.com/docs/cli/reference/output-format)
