#!/usr/bin/env bash
# queue-watcher-tick.sh (EXAMPLE, not productionised).
#
# One tick of the example queue-watcher service. A productionised
# version would query the RabbitMQ management API and exit non-zero
# when a watched queue has a non-empty backlog and zero consumers,
# writing FAIL_KIND to the fail-env file so the supervisor can decide
# whether to escalate.
#
# Contract expected by _supervisor-template.sh:
#   - exit 0  => tick succeeded; supervisor sleeps until the next poll.
#   - exit !0 => tick failed; supervisor writes nothing itself, so the
#                tick MUST write FAIL_KIND (+ optional FAIL_EXIT) to
#                $QUEUE_WATCHER_FAIL_ENV before exiting. FAIL_KIND of
#                "prereq_fail" tells the supervisor not to escalate
#                (daemon-level issue; operator is the recovery path).
#
# This stub always succeeds so the example never spawns a janitor.

set -uo pipefail

FAIL_ENV="${QUEUE_WATCHER_FAIL_ENV:-/tmp/queue-watcher-last-fail.env}"

# A real implementation would do something like:
#
#   if ! depth=$(rabbitmq_queue_depth protea.jobs); then
#     printf 'FAIL_KIND=prereq_fail\nFAIL_EXIT=1\n' > "$FAIL_ENV"
#     exit 1
#   fi
#   if (( depth > 0 )) && (( $(rabbitmq_consumer_count protea.jobs) == 0 )); then
#     printf 'FAIL_KIND=stalled_queue\nFAIL_EXIT=2\n' > "$FAIL_ENV"
#     exit 1
#   fi
#
# Placeholder: clear any stale fail-env and succeed.
rm -f "$FAIL_ENV" 2>/dev/null || true
exit 0
