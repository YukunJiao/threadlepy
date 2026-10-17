from __future__ import annotations

import collections
import json
import logging
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import warnings
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional, Union

logger = logging.getLogger("threadlepy")

# Threadle CLI version (major.minor) that the wrappers in this package were written for.
# tools/check_api.py checks that it matches tools/threadle-api.json.
SUPPORTED_THREADLE_VERSION = "1.3"

@dataclass(frozen=True)
class ThreadleStruct:
    name: str

ThreadleName = Union[str, ThreadleStruct]

proc: Optional[subprocess.Popen[str]] = None
print_cmd: bool = False
print_message: bool = True
default_timeout: float = 1800.0

# Lines read from the backend by background threads (see _start_readers). Reading in
# threads instead of select() works on Windows too, and draining stderr continuously
# keeps the backend from blocking on a full stderr pipe.
_stdout_lines: "queue.Queue[Optional[str]]" = queue.Queue()
_stderr_tail: "collections.deque[str]" = collections.deque(maxlen=200)
_readers: list[threading.Thread] = []

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

def _start_readers(p: subprocess.Popen[str]) -> None:
    global _stdout_lines
    _stdout_lines = queue.Queue()
    _stderr_tail.clear()

    def read_stdout(stream, q):
        for line in stream:
            q.put(line)
        q.put(None)  # EOF

    def read_stderr(stream):
        for line in stream:
            _stderr_tail.append(line.rstrip("\n"))

    _readers[:] = [
        threading.Thread(target=read_stdout, args=(p.stdout, _stdout_lines), daemon=True),
        threading.Thread(target=read_stderr, args=(p.stderr,), daemon=True),
    ]
    for t in _readers:
        t.start()

def _stderr_detail() -> str:
    text = "\n".join(_stderr_tail).strip()
    return f"\nThreadle stderr:\n{text}" if text else ""

def stop():
    """Stop the running Threadle subprocess, if one is active."""
    global proc
    p, proc = proc, None
    if p is None or p.poll() is not None:
        return
    try:  # ask the backend to exit on its own first
        assert p.stdin is not None
        p.stdin.write("exit\n")
        p.stdin.flush()
        p.stdin.close()
        p.wait(timeout=5)
    except Exception:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
    for t in _readers:  # the readers finish once the process has closed its pipes
        t.join(timeout=2)
    for stream in (p.stdout, p.stderr):
        if stream is not None:
            stream.close()
    logger.info("Threadle process %s stopped", p.pid)

def start(path: str | None = None) -> subprocess.Popen[str]:
    """Start the Threadle CLI JSON subprocess and return the process handle."""
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
    # Run the backend in its own process group so that Ctrl+C in the Python
    # session (e.g. interrupting a notebook cell) does not kill it.
    if sys.platform == "win32":
        group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    else:
        group = {"start_new_session": True}

    proc = subprocess.Popen(
        [exe, "--json", "--silent"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
        env=env,
        **group,
        )
    _start_readers(proc)
    logger.info("Threadle process %s started: %s", proc.pid, exe)
    _check_backend_version()
    return proc

def _check_backend_version() -> None:
    """Warn when the backend's version differs from the one the wrappers were written for."""
    try:
        about = unwrap(send_command(json_cmd("about"), timeout=30), print_message=False)
        version = str(about.get("CliVersion", ""))
    except Exception as e:  # never block startup on this check
        logger.debug("Could not read the Threadle version: %s", e)
        return
    if ".".join(version.split(".")[:2]) != SUPPORTED_THREADLE_VERSION:
        warnings.warn(
            f"Threadle {version} is running, but this version of threadlepy was written for "
            f"Threadle {SUPPORTED_THREADLE_VERSION}.x. Some commands may fail or behave differently.",
            stacklevel=3,
        )

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
    """Return keyword arguments whose values are not ``None``."""
    return {k: v for k, v in kwargs.items() if v is not None}

def json_cmd(command: str, args: Optional[Dict[str, Any]] = None, assign: Optional[str] = None) -> str:
    """Build a JSON command payload for the Threadle CLI."""
    dto = {
        "Assign": assign,
        "Command": str(command),
        "Args": args or {},
    }
    return json.dumps(dto, ensure_ascii=False)

def send_command(cmd_json: str, timeout: Optional[float] = None) -> Dict[str, Any]:
    """Send a JSON command to Threadle and wait for a JSON response."""
    if proc is None or proc.poll() is not None:
        raise RuntimeError("Threadle process is not running.")
    assert proc.stdin is not None

    if print_cmd:
        print(cmd_json)

    proc.stdin.write(cmd_json.rstrip("\n") + "\n")
    proc.stdin.flush()

    timeout = default_timeout if timeout is None else timeout
    end = time.monotonic() + timeout

    while True:
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(
                f"Timed out waiting for Threadle JSON response after {timeout} seconds. "
                "Use threadlepy.client.configure(timeout=...) to increase it."
            )
        try:
            line = _stdout_lines.get(timeout=min(remaining, 0.5))
        except queue.Empty:
            if proc is None or proc.poll() is not None:
                raise RuntimeError(f"Threadle process exited before returning JSON.{_stderr_detail()}")
            continue
        if line is None:
            raise RuntimeError(f"Threadle process exited before returning JSON.{_stderr_detail()}")

        # In JSON mode the backend answers each command with exactly one JSON line.
        s = re.sub(r"^\s*>\s*", "", line).strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                resp = json.loads(s)
                if isinstance(resp, dict):
                    return resp
            except json.JSONDecodeError:
                pass

def unwrap(resp: Dict[str, Any], *, print_message: bool = True) -> Any:
    """Validate a Threadle response and return its payload."""
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

def _caller_params(depth: int = 2) -> Optional[tuple[str, ...]]:
    """Names of the parameters of the function `depth` frames up, or None at module level."""
    code = sys._getframe(depth).f_code
    if code.co_name == "<module>":
        return None
    n = code.co_argcount + code.co_kwonlyargcount
    return code.co_varnames[:n]

def call(
    cmd: str,
    locals_dict: dict,
    *,
    assign: Optional[str] = None,
    assign_from: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
    return_response: bool = False,
    drop: tuple[str, ...] = (),
) -> Any:
    """Call a typed Threadle command wrapper using the caller's arguments.

    Wrappers pass ``locals()``; only the wrapper's own parameters are sent, under
    their own names, so helper variables in the wrapper body never reach the backend.
    Parameters set to ``None`` are left out, so the backend applies its default.

    - ``assign_from``: name of the parameter holding the backend variable to assign
      the result to (e.g. ``"name"``); that parameter is not sent as an argument.
    - ``drop``: further parameters not to send (client-side only arguments).
    - ``extra``: arguments to send that are not parameters of the wrapper.
    """
    params = _caller_params()
    if params is not None and all(p in locals_dict for p in params):
        locals_dict = {p: locals_dict[p] for p in params}
    args = collect_args(**locals_dict)
    args.pop("cmd", None)
    args.pop("assign", None)

    if assign_from is not None:
        assign = locals_dict[assign_from]
        args.pop(assign_from, None)
    elif assign is not None:
        # Older calling convention: drop the first argument holding the assign name.
        for k, v in list(args.items()):
            if v == assign:
                args.pop(k, None)
                break
    for key in drop:
        args.pop(key, None)
    args.update(collect_args(**(extra or {})))

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
