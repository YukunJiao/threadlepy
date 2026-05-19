from __future__ import annotations

import os
import signal
import subprocess
import shutil
import json
import time
import re
import select
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional, Union

@dataclass(frozen=True)
class ThreadleStruct:
    name: str

ThreadleName = Union[str, ThreadleStruct]

proc: Optional[subprocess.Popen[str]] = None
print_cmd: bool = False
print_message: bool = True
default_timeout: float = 1800.0

def is_available(path: str | None = "threadle") -> bool:
    """Return whether the Threadle executable can be found."""
    if path is None or not str(path).strip():
        path = "threadle"
    if os.path.sep in str(path) or (os.path.altsep and os.path.altsep in str(path)):
        p = os.path.expanduser(str(path))
        return os.path.isfile(p) and os.access(p, os.X_OK)
    return shutil.which(str(path)) is not None

def configure(
    *,
    print_commands: Optional[bool] = None,
    print_messages: Optional[bool] = None,
    timeout: Optional[float] = None,
) -> None:
    """Configure client-side behavior for subsequent Threadle calls."""
    global print_cmd, print_message, default_timeout
    if print_commands is not None:
        print_cmd = bool(print_commands)
    if print_messages is not None:
        print_message = bool(print_messages)
    if timeout is not None:
        default_timeout = float(timeout)

def stop():
    global proc
    if proc and proc.poll() is None:
        print("threadle stopped")
        print(f"threadle {os.getpgid(proc.pid)} killed")
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    proc = None

def start(path: str | None = None) -> subprocess.Popen[str]:
    global proc
    if path is None or not str(path).strip():
        exe = shutil.which("threadle")
    elif os.path.sep not in str(path) and not (os.path.altsep and os.path.altsep in str(path)):
        exe = shutil.which(str(path))
    else:
        exe = str(path)

    if not exe:
        raise FileNotFoundError(
            "Threadle executable not found. Add `threadle` to PATH or pass "
            "the full executable path to threadlepy.start(...)."
        )
    exe = os.path.abspath(os.path.expanduser(exe))
    if not os.path.isfile(exe):
        raise FileNotFoundError(f"Threadle executable not found at: {exe}")
    if not os.access(exe, os.X_OK):
        raise PermissionError(f"Threadle executable is not executable: {exe}")

    if proc and proc.poll() is None:
        raise RuntimeError("Threadle already started.")

    env = os.environ.copy()
    env.update(
        {
            "DOTNET_EnableDiagnostics": "0",
            "COMPlus_EnableDiagnostics": "0",
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
        }
    )
    
    proc = subprocess.Popen(
        [exe, "--json", "--silent"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        start_new_session=True,
        env=env,
        )
    print(f"threadle started pid={proc.pid} pgid={os.getpgid(proc.pid)}")
    return proc

@contextmanager
def session(path: str | None = None, **config: Any) -> Iterator[subprocess.Popen[str]]:
    """Start Threadle for a `with` block and stop it on exit."""
    if config:
        configure(**config)
    process = start(path)
    try:
        yield process
    finally:
        stop()

def collect_args(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}

def json_cmd(command: str, args: Optional[Dict[str, Any]] = None, assign: Optional[str] = None) -> str:
    dto = {
        "Assign": assign,
        "Command": str(command),
        "Args": args or {},
    }
    return json.dumps(dto, ensure_ascii=False)

def send_command(cmd_json: str, timeout: Optional[float] = None) -> Dict[str, Any]:
    global proc
    if proc is None or proc.poll() is not None:
        raise RuntimeError("Threadle process is not running.")
    assert proc.stdin is not None
    assert proc.stdout is not None

    if print_cmd:
        print(cmd_json)

    proc.stdin.write(cmd_json.rstrip("\n") + "\n")
    proc.stdin.flush()

    out_lines: list[str] = []
    timeout = default_timeout if timeout is None else timeout
    end = time.time() + timeout

    while time.time() < end:
        if proc.poll() is not None:
            stderr = ""
            if proc.stderr is not None:
                try:
                    stderr = proc.stderr.read() or ""
                except Exception:
                    stderr = ""
            detail = f"\nThreadle stderr:\n{stderr.strip()}" if stderr.strip() else ""
            raise RuntimeError(f"Threadle process exited before returning JSON.{detail}")

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

    hint = (
        f"Timed out waiting for Threadle JSON response after {timeout} seconds. "
        "Use threadlepy.client.configure(timeout=...) to increase it."
    )
    raise TimeoutError(hint)

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

def call(
    cmd: str,
    locals_dict: dict,
    *,
    assign: Optional[str] = None,
    timeout: Optional[float] = None,
    return_response: bool = False,
    drop: tuple[str, ...] = (),
) -> Any:
    args = collect_args(**locals_dict)
    args.pop("cmd", None)
    args.pop("assign", None)
    for key in drop:
        args.pop(key, None)

    if assign is not None:
        for k, v in list(args.items()):
            if v == assign:
                args.pop(k, None)
                break

    args = {k: _norm(v) for k, v in args.items()}
    cmd_json = json_cmd(cmd, args=args, assign=assign)
    resp = send_command(cmd_json, timeout=timeout)
    return resp if return_response else unwrap(resp, print_message=print_message)

def raw_cmd(
    cmd: str,
    args: Optional[Dict[str, Any]] = None,
    *,
    assign: Optional[str] = None,
    timeout: Optional[float] = None,
    return_response: bool = False,
) -> Any:
    """Send an arbitrary Threadle command, useful before a typed wrapper exists."""
    norm_args = {k: _norm(v) for k, v in (args or {}).items() if v is not None}
    resp = send_command(json_cmd(cmd, args=norm_args, assign=assign), timeout=timeout)
    return resp if return_response else unwrap(resp, print_message=print_message)
