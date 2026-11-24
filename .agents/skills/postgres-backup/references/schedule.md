# Scheduled backups

Use the requested host, cadence, timezone, and destination. If needed, ask only for missing details that change when or where the backup runs. Use Python 3.11+, absolute paths to the project, Python, Docker and the backup script. Test the exact command under the task identity, with Docker running and access to the Compose project and destination. Keep the Python and script paths available between runs. If the project deployment path changes, update the job.

## Linux cron

Read the selected user's `crontab -l` and preserve unrelated entries. Add or update one line identified by a comment with the project name and path. Use the host timezone, or verify support for `CRON_TZ` in the installed cron before using it. Example for a daily job at 02:00 in the host timezone, with `.backup` created with private permissions beforehand.

```cron
0 2 * * * '/usr/bin/python3' '/srv/postgis/.agents/skills/postgres-backup/scripts/backup.py' --project-dir '/srv/postgis' --docker '/usr/bin/docker' >> '/srv/postgis/.backup/cron.log' 2>&1 # postgis-backup /srv/postgis
```

For an external mount include `--external-dir '<mounted-path>'` and verify the mounted filesystem under that identity. When a mount can disappear, check the expected mount identity in the job before uploading, or keep a separate local backup job. Keep any rootless Docker socket or named context settings needed by the task. Check `crontab -l`, the job log, and the first generated bundle.

## Windows Task Scheduler

Use `New-ScheduledTaskAction` with the actual Python executable, `-WorkingDirectory` set to the project directory, and `-Argument` containing `-X utf8 "<backup.py>" --project-dir "<project-root>" --docker "<docker.exe>"`. Add `--external-dir "<UNC-path>"` when the job identity has access to a network share. Set a `New-ScheduledTaskTrigger` for the agreed time. Register a project-specific task name and configure `New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew`. Reuse the existing task only after confirming it is this project's backup job.

Use the Docker Desktop account with an interactive logon if Docker is available only in that session. For unattended operation, verify from the selected task identity that the Docker backend is available when the user is logged out. A UNC destination needs a logon that can access the network share. S4U tasks lack network access. Protect `.backup` and the external destination with filesystem ACLs. Run the task once with `Start-ScheduledTask` when authorized, check `Get-ScheduledTaskInfo` for `LastTaskResult`, and verify the resulting bundle. Record the task name, effective schedule, timezone, output path, and how to inspect failures.

[Microsoft ScheduledTasks](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/) · [Windows task logon types](https://learn.microsoft.com/en-us/windows/win32/taskschd/principal-logontype) · [Cron table syntax](https://man7.org/linux/man-pages/man5/crontab.5.html)
