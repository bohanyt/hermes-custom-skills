---
title: WhatsApp Connection Setup
session_id: bg_050241_abfc47
date: 2026-05-15
platform: cli
model: openrouter/owl-alpha
messages: 2
tags: [whatsapp, setup, gateway]
---

# WhatsApp Connection Setup

**Date:** 2026-05-15 | **Platform:** CLI | **Messages:** 2

## What Happened

User asked how to chat with Hermes via WhatsApp. User had already set up WhatsApp connection.

## Setup Steps

1. **Scan QR code** that appears in terminal/gateway
2. Open WhatsApp on phone → Settings → Linked Devices → Link a Device
3. Scan the QR code

## How It Works

- User sends message via WhatsApp → Gateway receives → Forwards to Hermes (OWL) → Hermes processes → Replies back via WhatsApp
- Same as chatting here, but through WhatsApp
- All tools accessible (terminal, file, browser, etc.)
- Memory and context preserved across sessions

## Related

- [[multi-session-management]] — Multi-platform session management

## Detail Files

- `sessions/detail/bg_050241_abfc47.md` — 2 messages, WhatsApp setup
