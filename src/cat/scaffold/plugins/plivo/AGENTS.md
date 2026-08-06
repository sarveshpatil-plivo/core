# Plivo plugin

A Cheshire Cat plugin that adds Plivo telephony capabilities. It ships a
`plugin.json` manifest plus decorated modules the mad hatter auto-discovers
when the plugin is installed.

## Capabilities

- `send_sms` (`@tool`, `tools.py`) — sends an SMS via the Plivo Messages API
  (`POST /v1/Account/{auth_id}/Message/`, success `202`).
- `make_call` (`@tool`, `tools.py`) — places an outbound call via the Plivo
  Voice API (`POST /v1/Account/{auth_id}/Call/`, success `201`). The answer_url
  defaults to `PLIVO_ANSWER_URL` so the caller does not have to pass one, and
  answer_method chooses how Plivo fetches it, either `GET` or `POST` (default
  `POST`).
- `plivo_answer` (`@endpoint`, `endpoints.py`) — the inbound answer webhook,
  returning static Plivo `<Speak>` call-flow XML for Plivo to fetch on answer.
- `plivo_sms` (`@endpoint`, `endpoints.py`) — the inbound SMS webhook, which
  Plivo sends incoming texts to (From, To, Text). It acknowledges with a `200`
  and is the place to hook your own handling of received messages.

Both inbound webhooks are registered for `GET` and `POST`, so the answer method
or message method can be set to either on the Plivo side without the plugin
being tied to one verb. They validate the `X-Plivo-Signature-V3` header so only
genuine Plivo requests are accepted, using the URL form that matches the request
method. The check is a standard library reimplementation of Plivo's V3 signature
(`signature.py`), so the plugin needs no extra dependency.

## Configuration

The tools read credentials from the environment:

- `PLIVO_AUTH_ID` — Plivo Auth ID (HTTP Basic username).
- `PLIVO_AUTH_TOKEN` — Plivo Auth Token (HTTP Basic password). Also used to
  validate inbound webhook signatures.
- `PLIVO_SRC` — the Plivo sender number / caller ID in E.164 format.
- `PLIVO_ANSWER_URL` — public URL of this Cat's `/plivo/answer` endpoint. Used
  as the default answer_url for outbound calls and to validate the signature on
  inbound answer requests.
- `PLIVO_INBOUND_SMS_URL` — public URL of this Cat's `/plivo/sms` endpoint. Used
  to validate the signature on inbound SMS requests.

Inbound signature checking is on by default. Without `PLIVO_AUTH_TOKEN` the
signature cannot be verified, so inbound webhooks are rejected. For local
development you can set `PLIVO_ALLOW_UNVERIFIED_WEBHOOKS` to accept unverified
requests, which logs a warning and should never be used in production.

Get credentials from the [Plivo console](https://cx.plivo.com).

## Wiring the inbound webhooks

- Point a Plivo application's Answer URL at `POST /plivo/answer` on this Cat
  instance so inbound calls receive the `<Speak>` flow.
- Point the Message URL of your Plivo number or application at `POST /plivo/sms`
  so inbound texts reach the Cat.

Configure both in the Plivo console (cx.plivo.com) or via the Plivo
Applications API, and set the matching `PLIVO_ANSWER_URL` and
`PLIVO_INBOUND_SMS_URL` env vars to the same public URLs.

## Notes

- All Plivo REST calls use HTTP Basic auth (`auth_id`:`auth_token`) against
  `https://api.plivo.com`.
- Success for a send is *queued/fired*, not *delivered/answered*. Delivery and
  call outcomes arrive on their respective status webhooks.
