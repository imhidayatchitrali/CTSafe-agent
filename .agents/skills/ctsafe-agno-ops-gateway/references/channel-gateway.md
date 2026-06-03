# Channel Gateway

## Purpose

Provide one normalized interface for Telegram now and possible WhatsApp/web channels later. Agno agents should not depend on Telegram-specific payloads.

## Internal Event Shape

```json
{
  "event_id": "evt_123",
  "channel": "telegram",
  "channel_user_id": "123456",
  "channel_chat_id": "987654",
  "message_type": "text",
  "text": "/stato_dvr",
  "attachments": [],
  "received_at": "2026-05-27T18:00:00Z",
  "raw_ref": "telegram_update_id_123"
}
```

## Adapter Responsibilities

Each adapter should:

- verify webhook authenticity where supported;
- convert raw payloads into internal events;
- extract text, files, voice/transcription refs, buttons, and callback payloads;
- attach channel metadata;
- never call Agno agents directly before auth.

## Channel Expansion

| Channel | Recommended use |
|---|---|
| Telegram | Primary MVP channel for intake, revision, status, approvals. |
| WhatsApp | Future customer-friendly channel; add only after Telegram flow is stable. |
| Web dashboard | Future control panel for approvals, progress, sources, and downloads. |
| Email | Optional notification channel, not primary command surface. |

## Output Events

Use a response envelope:

```json
{
  "channel": "telegram",
  "chat_id": "987654",
  "message": "Il DVR e' al 62%. Mancano dati su attrezzature e mansioni.",
  "attachments": [],
  "buttons": [
    {"label": "Vedi mancanti", "action": "show_missing_data"}
  ]
}
```

Keep channel formatting at the adapter boundary. Agents produce semantic responses, adapters render them.
