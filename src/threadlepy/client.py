from __future__ import annotations

import os
import signal
import subprocess
import shutil
import json
import time
import re
import select
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

@dataclass(frozen=True)
class ThreadleStruct:
    name: str

ThreadleName = Union[str, ThreadleStruct]

proc: Optional[subprocess.Popen[str]] = None

def stop():
    global proc
    if proc and proc.poll() is None:
        print("threadle stopped")
        print(f"threadle {os.getpgid(proc.pid)} killed")
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    proc = None

def start(path: str | None = None) -> subprocess.Popen[str]:
    global proc
    exe = path or shutil.which("threadle")

    if not exe:
        raise FileNotFoundError("Threadle path not found.")
    exe =  os.path.abspath(exe)

    if proc and proc.poll() is None:
        raise RuntimeError("Threadle already started.")
    
    proc = subprocess.Popen(
        [exe, "--json", "--silent"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        start_new_session=True,
        )
    print(f"threadle started pid={proc.pid} pgid={os.getpgid(proc.pid)}")
    return proc

def collect_args(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}

def json_cmd(command: str, args: Optional[Dict[str, Any]] = None, assign: Optional[str] = None) -> str:
    dto = {
        "Assign": assign,                 # None -> JSON null
        "Command": str(command),
        "Args": args or {},               # 关键：保证是 {}
    }
    return json.dumps(dto, ensure_ascii=False)

def send_command(cmd_json: str, timeout: float = 30.0) -> Dict[str, Any]:
    global proc
    if proc is None or proc.poll() is not None:
        raise RuntimeError("Threadle process is not running.")
    assert proc.stdin is not None
    assert proc.stdout is not None

    proc.stdin.write(cmd_json.rstrip("\n") + "\n")
    proc.stdin.flush()

    out_lines: list[str] = []
    end = time.time() + timeout

    while time.time() < end:
        r, _, _ = select.select([proc.stdout], [], [], 0.01)
        if not r:
            continue

        line = proc.stdout.readline()
        if line == "":
            raise RuntimeError("EOF from Threadle.")

        out_lines.append(line)

        s = re.sub(r"^\s*>\s*", "", line).strip()

        if s.startswith("{") and s.endswith("}"):
            try:
                resp = json.loads(s)
                if isinstance(resp, dict):
                    return resp
            except json.JSONDecodeError:
                pass

    raise TimeoutError("Timed out waiting for JSON response.")

def unwrap(resp: Dict[str, Any], *, print_message: bool = True) -> Any:
    if resp.get("Success") is not True:
        code = resp.get("Code") or "Error"
        msg = resp.get("Message") or "Threadle error"
        raise RuntimeError(f"[{code}] {msg}")

    if print_message:
        msg = resp.get("Message")
        if isinstance(msg, str) and msg.strip():
            print(msg)

    return resp.get("Payload")

def _norm(v: Any) -> Any:
    if isinstance(v, ThreadleStruct):
        return v.name
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (list, tuple)):
        return ";".join(str(x) for x in v)
    return v

def call(cmd: str, locals_dict: dict, *, assign: Optional[str] = None, timeout: float = 30.0) -> Any:
    args = collect_args(**locals_dict)
    args.pop("cmd", None)
    args.pop("assign", None)

    if assign is not None:
        for k, v in list(args.items()):
            if v == assign:
                args.pop(k, None)
                break

    args = {k: _norm(v) for k, v in args.items()}
    cmd_json = json_cmd(cmd, args=args, assign=assign)
    resp = send_command(cmd_json, timeout=timeout)
    return unwrap(resp)
