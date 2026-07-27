# conductor-monitor

AUTHORIZED read-only monitor (sanctioned by Francisco). Writes ONLY here.
Everything outside this folder (the agent-farm repo, the conductor's tmux
pane, its JSONL transcript, the sqlite state) is read-only observation,
never modified. NOT a leftover of the conductor's own scoping; do not
delete (whitelist in any cleanup).

## What runs

`recorder.py` tails the live conductor's JSONL transcript (the other
`claude` session in tmux `agent-farm:conductor`), auto-selecting the
largest recent `.jsonl` under `~/.claude/projects/-home-frapercan-Thesis2/`
excluding this monitor's own session. Driven by OS cron (`--once` per run);
the cron interval self-adapts (1/3/10 min) to conductor activity. A
self-sleeping daemon is impossible (the harness kills bash-tool background
processes, exit 144).

## Files

- `actions.log`  TOOL calls, USER turns, META (source/cron changes)
- `errors.log`   tool_result errors + strong error signals
- `alerts.log`   hard-constraint-violation hits (git stash, push to main, etc.)
- `pane-latest.txt`  newest tmux pane snapshot
- `OBSERVATIONS.md`  curated findings + environment improvements
- `.state.json` / `.heartbeat`  recorder bookkeeping

## Cron (cadence)

```
crontab -l | grep conductor-monitor      # inspect
crontab -l | grep -v '# conductor-monitor' | crontab -   # remove
```

## Messaging the conductor (fragile; use with care)

`tmux send-keys -t agent-farm:conductor "<msg>" Enter`. CAUTION: if the TUI
is in the background-agents widget mode ("Enter to view / x to stop"),
keystrokes are interpreted as widget commands, NOT input text (a stray `x`
can STOP an agent). Verify the input box has focus and is empty/idle first;
do not inject while it is "Flowing/thinking".
