from ..variables import Variables
from . import deserialize_text

from typing import Any, Final, Literal, overload
import asyncio
import re

VARIABLE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'\{\{\s*(\w+(?:(?:\.|\s+)\w+)*)\s*\}\}', re.IGNORECASE
)


@overload
async def replace_text_variables(text: str, variables: Variables) -> str: ...
@overload
async def replace_text_variables(
    text: str, variables: Variables, deserialize: Literal[True]
) -> str | int | float | bool: ...
@overload
async def replace_text_variables(
    text: str, variables: Variables, deserialize: Literal[False]
) -> str: ...
@overload
async def replace_text_variables(
    text: str, variables: Variables, deserialize: bool
) -> str | int | float | bool: ...
async def replace_text_variables(
    text: str, variables: Variables, deserialize: bool = False
) -> str | int | float | bool:
    matches: list[re.Match[str]] = list(VARIABLE_PATTERN.finditer(text))

    if not matches:
        return text

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

    result_text: str = ''.join(result)

    if deserialize:
        return deserialize_text(result_text)

    return result_text


async def replace_data_variables(
    data: Any, variables: Variables, deserialize: bool = False
) -> Any:
    if isinstance(data, str):
        return await replace_text_variables(data, variables, deserialize)
    elif isinstance(data, tuple | list | set | frozenset):
        return type(data)(
            await asyncio.gather(
                *[replace_data_variables(item, variables, deserialize) for item in data]
            )
        )
    elif isinstance(data, dict):
        keys, values = await asyncio.gather(
            asyncio.gather(
                *[replace_data_variables(key, variables) for key in data.keys()]
            ),
            asyncio.gather(
                *[
                    replace_data_variables(value, variables, deserialize)
                    for value in data.values()
                ]
            ),
        )
        return dict(zip(keys, values, strict=False))
    return data
