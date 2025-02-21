---
title: "Tailscale"
---

Homepage: [tailscale.com](https://tailscale.com)

Tailscale is a zero-config VPN that creates a secure network between your devices. Built on top of WireGuard®, Tailscale makes it easy to securely access your Ansible-NAS from anywhere without opening ports or requiring complex firewall rules.

## Usage

Set `tailscale_enabled: true` in your `inventories/<your_inventory>/nas.yml` file.

You'll need to get an auth key from your Tailscale admin console (<https://login.tailscale.com/admin/authkeys>) and add it to your configuration:

```yaml
tailscale_auth_key: "ts_auth_key"
```

## Specific Configuration

### Exit Node

If you want to use your Ansible-NAS as a Tailscale exit node (allowing other devices to route their internet traffic through it), set:

```yaml
tailscale_exit_node: true
```


### Subnet Routes

If you want to route traffic from your Ansible-NAS to other subnets, you can add them to the `tailscale_subnet_routes` list. For example:

```yaml
tailscale_accept_routes: true
tailscale_subnet_routes:
  - 10.0.0.0/8
```


### Additional Arguments

Any additional Tailscale arguments can be passed using:

```yaml
tailscale_extra_args: "--hostname ansible-nas --advertise-tags=tag:nas"
```

## Troubleshooting

- Ensure your auth key has the necessary permissions in the Tailscale admin console
- Check the service status with `systemctl status tailscaled`
- View logs with `journalctl -u tailscaled`
