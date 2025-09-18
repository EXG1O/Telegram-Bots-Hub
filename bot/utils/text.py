from ..variables import Variables

from typing import Any, Final
import asyncio
import re

VARIABLE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'\{\{\s*(\w+(?:(?:\.|\s+)\w+)*)\s*\}\}', re.IGNORECASE
)


async def replace_text_variables(text: str, variables: Variables) -> str:
    matches: list[re.Match[str]] = list(VARIABLE_PATTERN.finditer(text))
    keys: list[str] = [match.group(1) for match in matches]
    values: list[Any | None] = await asyncio.gather(
        *[variables.get(key) for key in keys]
    )

    result: list[str] = []
    last_end_index: int = 0

    for match, value in zip(matches, values, strict=False):
        start_index, end_index = match.span()
        result.extend(
            [
                text[last_end_index:start_index],
                str(value) if value is not None else match.group(0),
            ]
        )
        last_end_index = end_index
    result.append(text[last_end_index:])

    return ''.join(result)
