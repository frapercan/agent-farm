# Host crontab of record

Captured 2026-07-27, before the machine was reformatted. Five entries are
active; only two had an installer script in this repository
(`install-restore-drill-cron.sh`, `install-nightly-pgdump-cron.sh`), so the
other three existed only in the running crontab and nowhere else. This file
is the record; `install-all-crons.sh` beside it reinstalls them.

The `conductor-monitor` entry is operator-authorized and on the project's
never-delete list. Its recorder now lives at `observability/recorder.py`;
the crontab line still points at the scratch copy under `storage/`, which is
deliberate and must not be repointed without the operator's say-so.

```cron
30 4 * * 0 cd /home/frapercan/Thesis2/agent-farm && bash scripts/restore-drill.sh >> /home/frapercan/Thesis2/agent-farm/state/logs/restore_drill.log 2>&1 # FARM-1.7-restore-drill
*/5 * * * * PATH=/usr/local/bin:/usr/bin:/bin:/home/frapercan/.local/bin /usr/bin/flock -n -o /tmp/protea-coldboot.lock bash /home/frapercan/Thesis2/agent-farm/scripts/cold-boot.sh --quiet >> /home/frapercan/Thesis2/storage/infra_state/watchdog.log 2>&1 # protea-watchdog
0 3 * * * [ "$(df --output=avail -BG /mnt/protea-archive | tail -1 | tr -dc 0-9)" -ge 60 ] && pg_dump --format=custom --no-owner --file=/home/frapercan/Thesis2/backups/protea-$(date +\%Y-\%m-\%d).dump postgresql://protea:protea@localhost:5432/protea 2>>/home/frapercan/Thesis2/backups/pgdump.log || echo "$(date -Iseconds) skipped: low space" >>/home/frapercan/Thesis2/backups/pgdump.log
15 3 * * * ls -1t /home/frapercan/Thesis2/backups/protea-????-??-??.dump 2>/dev/null | tail -n +4 | xargs -r rm -f
*/5 * * * * /usr/bin/python3 /home/frapercan/Thesis2/storage/conductor-monitor/recorder.py --once >> /home/frapercan/Thesis2/storage/conductor-monitor/cron.log 2>&1 # conductor-monitor
```
