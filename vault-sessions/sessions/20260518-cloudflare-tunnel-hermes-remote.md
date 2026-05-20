---
title: Cloudflare Tunnel — Hermes Web UI Remote Access
sessions: [20260518_061437_f2e056d3]
date: 2026-05-18
platform: discord
model: openrouter/owl-alpha
total_messages: 43 (10 user, 33 assistant)
tags: [cloudflare-tunnel, hermes-dashboard, remote-access, networking, vpn]
---

# Cloudflare Tunnel — Hermes Web UI Remote Access

**Date:** 2026-05-18 06:14 | **Platform:** Discord | **Messages:** 43

## What Happened

User wanted to access Hermes Web UI from any network (not just local). Evaluated options: port forwarding, Cloudflare Tunnel, and Tailscale. Decided on Cloudflare Tunnel. Successfully set up and tested.

## Options Evaluated

| Option | Pros | Cons |
|--------|------|------|
| **Port Forwarding** | Simplest | Needs public IP (not CGNAT), insecure (no auth on dashboard) |
| **Cloudflare Tunnel** | Secure, free, no port forwarding, works behind CGNAT | URL changes each restart (unless using named tunnel + domain) |
| **Tailscale** | Full mesh VPN, device-to-device | Requires installing app on every client device |

## Decision: Cloudflare Tunnel

**Why:** Access from any device without installing anything. Just open a URL in any browser.

**Comparison table discussed:**

| | Cloudflare Tunnel | Tailscale |
|---|---|---|
| **How it works** | Tunnel from machine → Cloudflare edge → internet | VPN mesh between devices |
| **Access via** | Public URL (`xxx.trycloudflare.com`) | Private IP `100.x.x.x` |
| **Install on client?** | **No** — just open URL in any browser | **Yes** — install Tailscale on each device |
| **Auth/Security** | Can add Access Policy (email allowlist) | Requires Tailscale login on each device |
| **Free** | ✅ Forever | ✅ Personal (≤100 devices) |
| **Weakness** | Random URL changes each restart | Client must install app + join network |

## Setup Steps

1. **Install cloudflared:**
   ```powershell
   winget install Cloudflare.cloudflared
   ```

2. **Run tunnel:**
   ```powershell
   cloudflared tunnel --url http://localhost:9119
   ```

3. **Access URL:** `https://schema-roses-accountability-bend.trycloudflare.com`

## Hermes Dashboard Config

- **Dashboard command:**
  ```powershell
  hermes dashboard --host 0.0.0.0 --port 9119 --insecure --tui --skip-build --no-open
  ```
- **Dashboard URL (local):** `http://172.20.10.10:9119`
- **Network:** `172.20.10.x` (local only without tunnel)

## Important Notes

- **URL is random and changes each restart** — for permanent URL, need Cloudflare account + named tunnel
- **Dashboard runs as background process** — terminal doesn't need to stay open on screen
- **Tunnel was confirmed working** — accessible from phone browser
- **Next steps identified** (not yet done):
  1. ✅ Cloudflare Tunnel — working
  2. Permanent URL (Cloudflare account needed)
  3. Auto-start tunnel on Windows boot
  4. Add Cloudflare Access auth (email allowlist)

## Related

- [[hermes-desktop-setup]] — Hermes Desktop + local AI setup
- [[hermes-web-ui]] — Web UI dashboard discovery (session 20260517_233528_84bcf2)
- [[multi-session-management]] — Session management across networks

## Detail Files

- `sessions/detail/20260518_061437_f2e056d3.md` — 43 messages
