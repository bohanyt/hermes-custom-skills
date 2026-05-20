---
title: Cloudflare Tunnel — Hermes Web UI Remote Access
date: 2026-05-18
sessions: [
  session_20260518_061437_f2e056d3,
  session_20260518_063119_3b4574,
  session_20260518_103753_992adc
]
platform: discord/cli
model: openrouter/owl-alpha
total_messages: ~151 (combined)
tags: [cloudflare-tunnel, hermes-dashboard, remote-access, networking]
---

# Cloudflare Tunnel — Hermes Web UI Remote Access

**Date:** 2026-05-18 | **Platform:** Discord/CLI | **Combined messages:** ~151

## What Happened

Discussion and setup of Cloudflare Tunnel for remote access to Hermes Web UI dashboard. User wanted to access Hermes from outside the local network.

## Key Topics

### Cloudflare Tunnel Setup
- Created Cloudflare account and tunnel
- Configured tunnel to expose Hermes Web UI
- Successfully tested remote access

### Hermes Web UI Dashboard
- Built-in Web UI discovered (React + Fastapi)
- Dashboard accessible via browser
- Remote access via Cloudflare Tunnel

### Network Configuration
- Tunnel runs as background service
- No port forwarding needed
- Secure access via Cloudflare proxy

## Related

- [[hermes-web-ui]] — Hermes Web UI dashboard
- [[cloudflare-tunnel]] — Cloudflare Tunnel concept
- [[20260517-hermes-web-ui-dashboard]] — Previous Web UI session
