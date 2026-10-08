from collections.abc import Iterable
from typing import Any


def normalize_params(params: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}

    for key, value in params.items():
        if value is None:
            continue

        if isinstance(value, Iterable) and not isinstance(value, str):
            if not value:
                continue

            result[key] = ','.join(map(str, value))
        else:
            result[key] = str(value)

    return result
