#!/usr/bin/env python3
"""Run one Cursor CLI assignment with structured logs and no shell interpolation."""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--mode", choices=("agent", "ask", "plan"), default="agent")
    parser.add_argument("--allow-writes", action="store_true")
    parser.add_argument("--resume", metavar="SESSION_ID")
    parser.add_argument("--add-dir", type=Path, action="append", default=[])
    args = parser.parse_args()

    if args.allow_writes and args.mode != "agent":
        parser.error("--allow-writes requires --mode agent")
    workspace = args.workspace.expanduser().resolve(strict=True)
    prompt_file = args.prompt_file.expanduser().resolve(strict=True)
    if not workspace.is_dir() or not prompt_file.is_file():
        parser.error("workspace must be a directory and prompt-file must be a file")
    extra_dirs = [p.expanduser().resolve(strict=True) for p in args.add_dir]
    if any(not p.is_dir() for p in extra_dirs):
        parser.error("every --add-dir must be a directory")
    agent = shutil.which("agent")
    if not agent:
        parser.error("Cursor CLI 'agent' is not on PATH")

    run_dir = Path(tempfile.mkdtemp(prefix="codex-cursor-"))
    cmd = [agent, "--workspace", str(workspace), "--model", args.model,
           "--print", "--output-format", "stream-json"]
    if args.mode != "agent":
        cmd.extend(("--mode", args.mode))
    cmd.append("--trust")
    if args.allow_writes:
        cmd.append("--force")
    if args.resume:
        cmd.extend(("--resume", args.resume))
    for directory in extra_dirs:
        cmd.extend(("--add-dir", str(directory)))
    cmd.append(prompt_file.read_text(encoding="utf-8"))

    stream_path = run_dir / "stream.jsonl"
    stderr_path = run_dir / "stderr.log"
    print(json.dumps({"run_dir": str(run_dir), "model": args.model,
                      "mode": args.mode, "workspace": str(workspace)}), flush=True)
    with stream_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        return_code = subprocess.run(cmd, stdout=stdout, stderr=stderr, check=False).returncode

    terminal = None
    session_id = None
    with stream_path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                session_id = event.get("session_id") or session_id
                if event.get("type") == "result":
                    terminal = event
    success = return_code == 0 and terminal is not None and terminal.get("subtype") == "success"
    result = {"run_dir": str(run_dir), "exit_code": return_code,
              "terminal_success": success, "session_id": session_id,
              "model": args.model, "mode": args.mode}
    (run_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result), flush=True)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
