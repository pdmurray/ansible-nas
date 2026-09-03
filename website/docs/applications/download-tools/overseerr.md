---
title: "Overseerr"
---

 Homepage: [https://docs.seerr.dev](https://docs.seerr.dev)

 Docker Container: [ghcr.io/seerr-team/seerr](https://github.com/seerr-team/seerr/pkgs/container/seerr)

 Overseerr is a free and open source software application for managing requests for your media library. It integrates with your existing services, such as Sonarr, Radarr, and Plex!

 Overseerr has been rebranded as **Seerr**, and this role now deploys the `ghcr.io/seerr-team/seerr` image. The variable names, container name and data directory are unchanged, so existing installs upgrade in place: Seerr migrates an existing Overseerr config directory automatically on first start. See the [migration guide](https://docs.seerr.dev/migration-guide/), and back up `{{ docker_home }}/overseerr/config` before the first run.

## Usage

 Using overseerr: Set `overseerr_enabled: true` in your `inventories/<your_inventory>/group_vars/nas.yml` file.

 The overseerr web interface can be found at [http://ansible_nas_host_or_ip:5055](http://ansible_nas_host_or_ip:5055).
