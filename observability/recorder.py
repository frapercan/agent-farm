#!/usr/bin/env python3
"""Conductor monitor recorder (READ-ONLY observer).

Authorized read-only monitor of the live conductor (the other `claude`
session in tmux window agent-farm:conductor). Tails its JSONL transcript
and records a compact registry of ACTIONS (tool calls, user turns) and
ERRORS into this folder ONLY. Never modifies the repo, the conductor's
work, or the shared memory store. See README.md.
"""
from __future__ import annotations
import json, os, re, time, subprocess

HOME = os.path.expanduser("~")
PROJ_DIR = f"{HOME}/.claude/projects/-home-frapercan-Thesis2"
SELF_SESSION = "c1b61fd4-c35a-4ce5-a85e-ae42322a9f30"  # my own session, never monitor it
MON = f"{HOME}/Thesis2/storage/conductor-monitor"
STATE = f"{MON}/.state.json"
ACTIONS = f"{MON}/actions.log"
ERRORS = f"{MON}/errors.log"
ALERTS = f"{MON}/alerts.log"
PANE = f"{MON}/pane-latest.txt"
HEARTBEAT = f"{MON}/.heartbeat"
TMUX_TARGET = "agent-farm:conductor"
POLL_SECS = 12
CRON_TAG = "# conductor-monitor"
IDLE_FAST = 300    # < 5 min idle -> 1 min cadence
IDLE_SLOW = 1200   # < 20 min idle -> 3 min; beyond -> 10 min

# Tightened: only strong, unambiguous error signals (avoid matching the word
# "error"/"failed" inside prompt text echoed in tool results).
ERR_RX = re.compile(
    r"traceback \(most recent|fatal: |command not found|"
    r"no such file or directory|permission denied|exit code [1-9]|"
    r"segmentation fault|\bkilled\b|out of memory|\boom-kill|"
    r"merge conflict|^[a-z.]*error:|exception:",
    re.I | re.M,
)

# Hard-constraint violations (from ~/Thesis2/CLAUDE.md) the conductor must
# never do. Signals for ME to decide whether to message it.
ALERT_RX = re.compile(
    r"git stash|--no-verify|--no-gpg-sign|co-authored-by|pgvector|"
    # direct push to main/master only: main must be within 30 chars of `push`
    # (so branch pushes and `gh pr create --base main` do NOT match)
    r"push\b[^\n]{0,30}\b(?:origin\s+)?(?:main|master)\b|"
    r"push\b[^\n]{0,30}:(?:main|master)\b|"
    r"manage\.sh\s+(?:restart|stop|down)|repositories/PROTEA",
    re.I,
)


def load_state() -> dict:
    try:
        with open(STATE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(s: dict) -> None:
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f)
    os.replace(tmp, STATE)


def pick_target() -> str | None:
    """Largest jsonl modified in the last 15 min, excluding my own session."""
    best, best_size = None, 0
    now = time.time()
    try:
        for name in os.listdir(PROJ_DIR):
            if not name.endswith(".jsonl") or SELF_SESSION in name:
                continue
            p = os.path.join(PROJ_DIR, name)
            try:
                st = os.stat(p)
            except OSError:
                continue
            if now - st.st_mtime > 900:
                continue
            if st.st_size > best_size:
                best, best_size = p, st.st_size
    except OSError:
        return None
    return best


def brief(name: str, inp) -> str:
    if not isinstance(inp, dict):
        return str(inp)[:160]
    for k in ("command", "file_path", "path", "pattern", "query", "url",
              "prompt", "description"):
        if k in inp and inp[k]:
            return f"{k}={str(inp[k])[:200]}"
    return ",".join(list(inp.keys()))[:160]


def stringify(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for it in content:
            if isinstance(it, dict):
                out.append(str(it.get("text") or it.get("content") or ""))
            else:
                out.append(str(it))
        return " ".join(out)
    return str(content)


def append(path: str, line: str) -> None:
    with open(path, "a") as f:
        f.write(line.rstrip("\n") + "\n")


def resources_constrained() -> bool:
    """True if heavy compute is occupying limiting resources (GPU/CPU/RAM).

    Operator overnight policy (2026-06-22): poll TIGHT (1 min) while the
    system is parked, and BACK OFF only when we are occupying limiting
    resources, so the monitor does not compete with the real work.
    """
    try:
        if os.getloadavg()[0] > 0.7 * (os.cpu_count() or 4):
            return True
    except Exception:
        pass
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=8,
        )
        if out.returncode == 0:
            for line in out.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                # VRAM is the reliable heavy-job signal (a loaded PLM = GBs);
                # raw util spikes transiently and is too noisy to gate on.
                if len(parts) >= 2 and int(float(parts[1])) > 2500:
                    return True
    except Exception:
        pass
    try:
        with open("/proc/meminfo") as f:
            mi = {l.split(":")[0]: int(l.split()[1]) for l in f if ":" in l}
        if mi.get("MemAvailable", 0) / 1024 / 1024 < 8:
            return True
    except Exception:
        pass
    return False


def desired_interval() -> int:
    # Inverted policy: 1 min while parked, back off when resources are scarce.
    return 5 if resources_constrained() else 1


def set_cron_interval(mins: int) -> None:
    """Rewrite this monitor's own crontab line to the desired cadence."""
    try:
        out = subprocess.run(["crontab", "-l"], capture_output=True,
                             text=True, timeout=10).stdout
    except Exception:
        return
    sched = "*" if mins <= 1 else f"*/{mins}"
    newline = (f"{sched} * * * * /usr/bin/python3 {MON}/recorder.py --once "
               f">> {MON}/cron.log 2>&1 {CRON_TAG}")
    lines = [l for l in out.splitlines() if CRON_TAG not in l and l.strip()]
    lines.append(newline)
    try:
        subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n",
                       text=True, timeout=10)
    except Exception:
        pass


def process_obj(obj: dict) -> None:
    ts = obj.get("timestamp", "")
    typ = obj.get("type", "")
    msg = obj.get("message") or {}
    content = msg.get("content")
    if typ == "user" and isinstance(content, str):
        append(ACTIONS, f"{ts}\tUSER\t{content[:240]}")
        return
    if not isinstance(content, list):
        return
    for item in content:
        if not isinstance(item, dict):
            continue
        t = item.get("type")
        if t == "tool_use":
            name = item.get("name", "?")
            inp = item.get("input", {})
            append(ACTIONS, f"{ts}\tTOOL\t{name}\t{brief(name, inp)}")
            blob = json.dumps(inp) if isinstance(inp, dict) else str(inp)
            m = ALERT_RX.search(blob)
            if m:
                append(ALERTS, f"{ts}\tALERT\t{name}\thit={m.group(0)!r}\t{blob[:300]}")
        elif t == "tool_result":
            txt = stringify(item.get("content"))
            if item.get("is_error") or ERR_RX.search(txt[:2000]):
                tag = "ERROR" if item.get("is_error") else "WARN"
                append(ERRORS, f"{ts}\t{tag}\t{txt[:600].replace(chr(10), ' / ')}")


def snapshot_pane() -> None:
    try:
        out = subprocess.run(
            ["tmux", "capture-pane", "-p", "-t", TMUX_TARGET, "-S", "-200"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0:
            with open(PANE, "w") as f:
                f.write(out.stdout)
    except Exception:
        pass


def tick(st: dict, do_pane: bool = True) -> dict:
    target = pick_target() or st.get("path")
    if target and target != st.get("path"):
        try:
            st = {"path": target, "offset": os.path.getsize(target),
                  "cron_min": st.get("cron_min")}
        except OSError:
            st = {"path": target, "offset": 0, "cron_min": st.get("cron_min")}
        append(ACTIONS, f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\tMETA\tsource -> {os.path.basename(target)}")
        save_state(st)
    if target and os.path.exists(target):
        try:
            size = os.path.getsize(target)
            off = st.get("offset", size)
            if off > size:
                off = 0
            if size > off:
                with open(target, "r", errors="replace") as f:
                    f.seek(off)
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            process_obj(json.loads(line))
                        except Exception:
                            pass
                    st["offset"] = f.tell()
                save_state(st)
        except Exception:
            pass
    # Adaptive cadence: back the cron off when the conductor is quiet.
    idle = 9999.0
    tp = st.get("path")
    if tp and os.path.exists(tp):
        try:
            idle = time.time() - os.path.getmtime(tp)
        except OSError:
            pass
    di = desired_interval()
    if di != st.get("cron_min"):
        set_cron_interval(di)
        st["cron_min"] = di
        save_state(st)
        append(ACTIONS, f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\tMETA\tcron -> every {di} min (resources_constrained={di>1})")
    if do_pane:
        snapshot_pane()
    with open(HEARTBEAT, "w") as f:
        f.write(time.strftime("%Y-%m-%dT%H:%M:%S")
                + f" tracking={os.path.basename(st.get('path','-'))}"
                + f" idle={int(idle)}s cron={st.get('cron_min','?')}min\n")
    return st


def main() -> None:
    import sys
    once = "--once" in sys.argv
    st = load_state()
    if once:
        tick(st)
        return
    n = 0
    while True:
        st = tick(st, do_pane=(n % 5 == 0))
        n += 1
        time.sleep(POLL_SECS)


if __name__ == "__main__":
    main()
