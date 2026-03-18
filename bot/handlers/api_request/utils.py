from aiohttp import hdrs
from multidict import CIMultiDict, istr
import msgspec

from core.msgspec import json_decoder

from typing import Any, Final

FORBIDDEN_HEADERS: Final[list[istr]] = [
    hdrs.CONNECTION,
    hdrs.CONTENT_LENGTH,
    hdrs.CONTENT_TYPE,
    hdrs.HOST,
    hdrs.PROXY_AUTHORIZATION,
    istr('Proxy-Connection'),
    hdrs.TE,
    hdrs.TRANSFER_ENCODING,
    hdrs.UPGRADE,
    hdrs.USER_AGENT,
]


def get_safe_headers(base_headers: dict[str, str] | None = None) -> CIMultiDict[str]:
    headers = CIMultiDict(base_headers)

    for forbidden_header in FORBIDDEN_HEADERS:
        if forbidden_header in headers:
            del headers[forbidden_header]

    return headers


def parse_response_body(body: bytes) -> Any:
    try:
        return json_decoder.decode(body)
    except msgspec.DecodeError:
        return body.decode()
