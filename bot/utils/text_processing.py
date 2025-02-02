from collections.abc import Sequence
from typing import Any
import re

ProcessedNestedData = dict[str, str | int]

nested_data_types = (str, int)
nested_data_iterable_types = (dict, Sequence)


async def _process_nested_variables(
    root_key: str, data: dict[str, Any] | Sequence[Any]
) -> ProcessedNestedData:
    result: ProcessedNestedData = {}

    for key, value in data.items() if isinstance(data, dict) else enumerate(data):
        full_key = f'{root_key}.{key}'

        if isinstance(value, nested_data_types):
            result[full_key] = value
        elif isinstance(value, nested_data_iterable_types):
            result.update(await _process_nested_variables(full_key, value))

    return result


async def replace_text_variables(text: str, variables: dict[str, Any]) -> str:
    result: str = text

    for key, value in variables.items():
        if isinstance(value, nested_data_types):
            result = re.sub(
                r'\{\{\s*' + re.escape(key) + r'\s*\}\}',
                str(value),
                result,
                flags=re.IGNORECASE,
            )
        elif isinstance(value, nested_data_iterable_types):
            result = await replace_text_variables(
                result, await _process_nested_variables(key, value)
            )

    return result
