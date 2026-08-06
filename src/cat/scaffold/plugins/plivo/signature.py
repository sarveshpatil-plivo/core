"""Plivo V3 webhook signature validation, using only the standard library.

This mirrors the algorithm in plivo-python's ``plivo.utils.signature_v3`` so
inbound webhooks can be verified without pulling the Plivo SDK into the Cat's
dependencies. The signature is an HMAC-SHA256 over the request URL and a nonce,
base64 encoded, sent in the ``X-Plivo-Signature-V3`` header. GET and POST
callbacks are signed over slightly different URL forms, so both are supported.
"""

import base64
import hashlib
import hmac
from urllib.parse import parse_qs, urlparse, urlunparse


def _fmt(value):
    if isinstance(value, bytes):
        return "".join(chr(b) for b in bytearray(value))
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return [_fmt(v) for v in value]
    return value


def _map_from_query(query: str) -> dict:
    return {_fmt(k): _fmt(v) for k, v in parse_qs(query, keep_blank_values=True).items()}


def _sorted_query_string(params: dict) -> str:
    parts = []
    for key in sorted(params.keys()):
        value = params[key]
        if isinstance(value, list):
            parts.append("&".join(f"{_fmt(key)}={v}" for v in sorted(_fmt(value))))
        else:
            parts.append(f"{_fmt(key)}={_fmt(value)}")
    return "&".join(parts)


def _sorted_params_string(params: dict) -> str:
    parts = []
    for key in sorted(params.keys()):
        value = params[key]
        if isinstance(value, list):
            parts.append("".join(f"{_fmt(key)}{v}" for v in sorted(_fmt(value))))
        elif isinstance(value, dict):
            parts.append(f"{_fmt(key)}{_sorted_params_string(value)}")
        else:
            parts.append(f"{_fmt(key)}{_fmt(value)}")
    return "".join(parts)


def _construct_get_url(uri: str, params: dict, empty_post_params: bool = True) -> str:
    parsed = urlparse(uri)
    base_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    merged = dict(params)
    merged.update(_map_from_query(parsed.query))
    query_params = _sorted_query_string(merged)
    if len(query_params) > 0 or not empty_post_params:
        base_url += "?" + query_params
    if len(query_params) > 0 and not empty_post_params:
        base_url += "."
    return base_url


def _construct_post_url(uri: str, params: dict) -> str:
    base_url = _construct_get_url(uri, {}, len(params) == 0)
    return base_url + _sorted_params_string(params)


def _signature(auth_token: str, base_url: str, nonce: str) -> str:
    digest = hmac.new(
        auth_token.encode("utf-8"),
        f"{base_url}.{nonce}".encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.encodebytes(digest).strip().decode("utf-8")


def validate_v3_signature(
    method: str, uri: str, nonce: str, signature: str, auth_token: str, params: dict = None
) -> bool:
    """Return True when a webhook's V3 signature is valid for the given method.

    ``signature`` is the raw ``X-Plivo-Signature-V3`` header, which may carry a
    comma separated list of signatures; a match against any one is accepted.
    """
    params = dict(params or {})
    if method.upper() == "GET":
        base_url = _construct_get_url(uri, params)
    else:
        base_url = _construct_post_url(uri, params)
    return _signature(auth_token, base_url, nonce) in (signature or "").split(",")
