# Plivo plugin

A Cheshire Cat plugin that adds Plivo telephony capabilities. It ships a
`plugin.json` manifest plus decorated modules the mad hatter auto-discovers
when the plugin is installed.

## Capabilities

- `send_sms` (`@tool`, `tools.py`) — sends an SMS via the Plivo Messages API
  (`POST /v1/Account/{auth_id}/Message/`, success `202`).
- `make_call` (`@tool`, `tools.py`) — places an outbound call via the Plivo
  Voice API (`POST /v1/Account/{auth_id}/Call/`, success `201`).
- `plivo_answer` (`@endpoint`, `endpoints.py`) — the inbound answer webhook,
  returning static Plivo `<Speak>` call-flow XML for Plivo to fetch on answer.

## Configuration

The tools read credentials from the environment:

- `PLIVO_AUTH_ID` — Plivo Auth ID (HTTP Basic username).
- `PLIVO_AUTH_TOKEN` — Plivo Auth Token (HTTP Basic password).
- `PLIVO_SRC` — the Plivo sender number / caller ID in E.164 format.

Get credentials from the [Plivo console](https://cx.plivo.com/?utm_source=github&utm_medium=oss&utm_campaign=cheshire-cat).

## Wiring the inbound webhook

Point a Plivo application's Answer URL at `POST /plivo/answer` on this Cat
instance so inbound calls receive the `<Speak>` flow. Configure it in the Plivo
console (cx.plivo.com) or via the Plivo Applications API.

## Notes

- All Plivo REST calls use HTTP Basic auth (`auth_id`:`auth_token`) against
  `https://api.plivo.com`.
- Success for a send is *queued/fired*, not *delivered/answered* — delivery and
  call outcomes arrive on their respective status webhooks.
