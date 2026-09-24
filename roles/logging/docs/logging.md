# Centralized Docker logging

The `logging` role installs a self-contained Grafana, Loki, and Grafana Alloy
stack. Alloy discovers every container on the local Docker daemon and begins
shipping its logs automatically, including containers created by Portainer or
other Compose projects after the role has run.

## Enable the stack

Add the following to your inventory's `group_vars/nas.yml`. Store the password
with Ansible Vault rather than committing it in plaintext.

```yaml
logging_stack_enabled: true
logging_grafana_admin_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...
```

Then run only this role while reviewing the first installation:

```bash
ansible-playbook -i inventories/<inventory>/inventory nas.yml --tags logging
```

Grafana listens on `127.0.0.1:3001` by default. Reach it through an SSH tunnel:

```bash
ssh -L 3001:127.0.0.1:3001 <user>@<nas-host>
```

Then open `http://localhost:3001`. If you publish Grafana through a reverse
proxy, keep authentication enabled, use HTTPS on both proxy legs, set
`logging_grafana_root_url`, and bind `logging_grafana_bind_address` only to the
specific VM address the proxy needs. Loki and Alloy are not published.

## Search and alerting

Open **Dashboards > Ansible-NAS > Docker Logs**. The dashboard includes a
container selector, a free-form LogQL regex filter, and a graph of error-like
messages. The default filter is:

```text
(?i)(error|fatal|panic|exception|critical)
```

Grafana also evaluates an alert for the same pattern. It is visible under
**Alerting > Alert rules**. To receive notifications, add a contact point in
**Alerting > Contact points** and route alerts with `source=docker-logs` to it.
This keeps credentials for email, Slack, Gotify-compatible webhooks, or another
destination out of the repository.

Tune noisy applications with `logging_error_pattern`, or disable the provisioned
rule with `logging_error_alert_enabled: false` while retaining the dashboard.

On first start, Alloy reads retained Docker logs. Loki rejects entries older
than its default one-week ingestion window and some out-of-order historical
entries. These errors should stop once Alloy catches up; the rejected copies
remain in Docker's original logs.

If Alloy repeatedly reports `configured logging driver does not support
reading` for a container, identify its name and driver using the container ID
from the error:

```bash
docker inspect --format '{{.Name}} log-driver={{.HostConfig.LogConfig.Type}}' <container-id>
```

Docker cannot supply logs from a container using the `none` logging driver
through the Docker API. Exclude that container in inventory using its name
without the leading `/`:

```yaml
logging_excluded_containers:
  - example-container
```

The exclusion matches exact container names. Other containers remain
automatically discovered. To collect logs from the excluded application,
configure that application's logging driver to support `docker logs`, or add a
separate log source for its output.

## Retention, security, and backup

- Logs are retained for 28 days (`672h`) by default. Loki deletes by age, not by
  disk usage, so monitor the free space beneath `logging_data_directory`.
- Alloy needs access to `/var/run/docker.sock` for container discovery and log
  reads. Access to the Docker socket is effectively privileged; keep Grafana
  patched and do not expose Alloy.
- The stack persists beneath the configured `logging_data_directory`. Include
  that directory in backups only if historical logs and Grafana state are worth
  the space.
- Disabling the role removes its containers and private Docker network but
  preserves all configuration and data for recovery or re-enablement.
