---
description: Display plan progress and next pickable slices
---

Run `bash ~/Thesis2/agent-farm/scripts/plan-progress.sh $ARGS` where $ARGS is optional (e.g., `--phase F-FEAT` to filter by phase, `--next` to pick the highest-priority pickable slice). Joins the plan catalog under `plans/<loop>/PLAN.md` with executor task history from sqlite. Report which slices are pickable, in flight, blocked, or done.
