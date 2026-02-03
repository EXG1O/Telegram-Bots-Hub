from .deserializers import deserialize_text

from typing import TYPE_CHECKING, Any, Final, Literal, overload
import asyncio
import re

if TYPE_CHECKING:
    from ..variables import Variables
else:
    Variables = Any


VARIABLE_PATTERN: Final[re.Pattern[str]] = re.compile(r'\{\{([^{}]+)\}\}')


async def _replace_text_variables(text: str, variables: Variables) -> str:
    matches: list[re.Match[str]] = list(VARIABLE_PATTERN.finditer(text))

    if not matches:
        return text

    keys: list[str] = [match.group(1).strip() for match in matches]
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
    final_text: str = text

    for _ in range(3):
        next_text: str = await _replace_text_variables(final_text, variables)

        if next_text == final_text:
            break

        final_text = next_text

    if deserialize:
        return deserialize_text(final_text)

    return final_text


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
