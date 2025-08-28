from multidict import CIMultiDict

from typing import Any, Final
import json

FORBIDDEN_HEADERS: Final[list[str]] = [
    'Connection',
    'Content-Length',
    'Content-Type',
    'Host',
    'Proxy-Authorization',
    'Proxy-Connection',
    'TE',
    'Transfer-Encoding',
    'Upgrade',
    'User-Agent',
]


def get_safe_headers(base_headers: dict[str, str] | None = None) -> CIMultiDict[str]:
    headers = CIMultiDict(base_headers)

    for forbidden_header in FORBIDDEN_HEADERS:
        if forbidden_header in headers:
            del headers[forbidden_header]

    return headers


def parse_response_body(body: bytes) -> Any:
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return body.decode()
