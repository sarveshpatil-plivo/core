import os

import httpx

from cat import tool


PLIVO_API_BASE = "https://api.plivo.com/v1/Account"


@tool
async def send_sms(dst: str, text: str) -> str:
    """Send an SMS through Plivo. Input is the destination number in E.164 format and the message text."""

    auth_id = os.getenv("PLIVO_AUTH_ID")
    auth_token = os.getenv("PLIVO_AUTH_TOKEN")
    src = os.getenv("PLIVO_SRC")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PLIVO_API_BASE}/{auth_id}/Message/",
            auth=(auth_id, auth_token),
            json={"src": src, "dst": dst, "text": text},
        )

    if response.status_code == 202:
        return f"SMS queued for {dst}."
    return f"Failed to send SMS to {dst}: {response.status_code} {response.text}"


@tool
async def make_call(to: str, answer_url: str) -> str:
    """Place an outbound Plivo call. Input is the destination number in E.164 format and the answer_url Plivo fetches for call-flow XML."""

    auth_id = os.getenv("PLIVO_AUTH_ID")
    auth_token = os.getenv("PLIVO_AUTH_TOKEN")
    src = os.getenv("PLIVO_SRC")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PLIVO_API_BASE}/{auth_id}/Call/",
            auth=(auth_id, auth_token),
            json={"from": src, "to": to, "answer_url": answer_url},
        )

    if response.status_code == 201:
        return f"Call fired to {to}."
    return f"Failed to call {to}: {response.status_code} {response.text}"
