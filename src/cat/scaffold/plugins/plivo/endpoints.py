import os

from fastapi import Request
from fastapi.responses import Response

from cat import endpoint, log

from .signature import validate_v3_signature


ANSWER_XML = (
    "<Response><Speak>Hello from the Cheshire Cat, powered by Plivo.</Speak></Response>"
)


def _truthy(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


async def _params(request: Request) -> dict:
    """Plivo puts callback params in the query string on GET and the form on POST."""
    if request.method == "GET":
        return dict(request.query_params)
    return dict(await request.form())


async def _verify(request: Request, signed_url_env: str) -> bool:
    """Verify the Plivo V3 signature on an inbound webhook.

    ``signed_url_env`` names the env var holding the public URL Plivo was
    pointed at (that URL is what Plivo signs, so it must match exactly).

    Verification is on by default. Without a ``PLIVO_AUTH_TOKEN`` the signature
    cannot be checked, so the request is rejected unless the operator has
    explicitly set ``PLIVO_ALLOW_UNVERIFIED_WEBHOOKS`` (for local development).
    """
    auth_token = os.getenv("PLIVO_AUTH_TOKEN", "")
    if not auth_token:
        if _truthy(os.getenv("PLIVO_ALLOW_UNVERIFIED_WEBHOOKS", "")):
            log.warning(
                "Plivo webhook accepted without signature check: PLIVO_AUTH_TOKEN "
                "is unset and PLIVO_ALLOW_UNVERIFIED_WEBHOOKS is on. Do not use "
                "this in production."
            )
            return True
        log.warning(
            "Rejecting Plivo webhook: PLIVO_AUTH_TOKEN is not set, so the "
            "signature cannot be verified."
        )
        return False

    signed_url = os.getenv(signed_url_env, "")
    signature = request.headers.get("X-Plivo-Signature-V3", "")
    nonce = request.headers.get("X-Plivo-Signature-V3-Nonce", "")
    if not (signed_url and signature and nonce):
        log.warning(
            f"Rejecting Plivo webhook: missing {signed_url_env}, signature, or nonce."
        )
        return False

    params = await _params(request)
    if not validate_v3_signature(request.method, signed_url, nonce, signature, auth_token, params):
        log.warning(f"Rejecting Plivo webhook: V3 signature mismatch for {signed_url_env}.")
        return False
    return True


async def _answer(request: Request) -> Response:
    if not await _verify(request, "PLIVO_ANSWER_URL"):
        return Response(content="forbidden", status_code=403)
    return Response(content=ANSWER_XML, media_type="application/xml")


async def _inbound_sms(request: Request) -> Response:
    if not await _verify(request, "PLIVO_INBOUND_SMS_URL"):
        return Response(content="forbidden", status_code=403)
    # The incoming message lives in the params: From, To, Text, MessageUUID.
    # Hook the Cat's own logic in here to act on it. We acknowledge with a 200 so
    # Plivo marks the delivery as handled.
    return Response(status_code=200)


# Both webhooks are registered for GET and POST so the answer/message method can
# be chosen on the Plivo side without the plugin being locked to one verb.
@endpoint.get("/plivo/answer", tags=["Plivo"])
async def plivo_answer_get(request: Request) -> Response:
    """Inbound call answer webhook (GET). Plivo fetches this and speaks the returned XML."""
    return await _answer(request)


@endpoint.post("/plivo/answer", tags=["Plivo"])
async def plivo_answer_post(request: Request) -> Response:
    """Inbound call answer webhook (POST). Plivo fetches this and speaks the returned XML."""
    return await _answer(request)


@endpoint.get("/plivo/sms", tags=["Plivo"])
async def plivo_sms_get(request: Request) -> Response:
    """Inbound SMS webhook (GET). Plivo sends an incoming text here (From, To, Text)."""
    return await _inbound_sms(request)


@endpoint.post("/plivo/sms", tags=["Plivo"])
async def plivo_sms_post(request: Request) -> Response:
    """Inbound SMS webhook (POST). Plivo sends an incoming text here (From, To, Text)."""
    return await _inbound_sms(request)
