from bs4 import BeautifulSoup, NavigableString, Tag

from collections.abc import Sequence
from typing import Any
import re

ProcessedNestedData = dict[str, str | int]

nested_data_types = (str, int)
nested_data_iterable_types = (dict, Sequence)


async def _replace_text_variables_in_nested_data(
	root_key: str, data: dict[str, Any] | Sequence[Any]
) -> ProcessedNestedData:
	result: ProcessedNestedData = {}

	for key, value in data.items() if isinstance(data, dict) else enumerate(data):
		full_key = f'{root_key}.{key}'

		if isinstance(value, nested_data_types):
			result[full_key] = value
		elif isinstance(value, nested_data_iterable_types):
			result.update(await _replace_text_variables_in_nested_data(full_key, value))

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
				result, await _replace_text_variables_in_nested_data(key, value)
			)

	return result


async def _process_html_element(root_element: Tag) -> str:
	result: str = ''

	for element in root_element.childGenerator():
		if isinstance(element, Tag):
			if element.name == 'a':
				result += f'<a href="{element["href"]}">{await _process_html_element(element)}</a>'
			elif element.name in [
				'b',
				'strong',
				'i',
				'em',
				'u',
				'ins',
				's',
				'strike',
				'del',
				'tg-spoiler',
				'code',
			]:
				result += f'<{element.name}>{await _process_html_element(element)}</{element.name}>'
			else:
				result += await _process_html_element(element)
		elif isinstance(element, NavigableString):
			result += element

	return result


async def process_text_with_html(text: str) -> str:
	soup = BeautifulSoup(text, 'lxml')
	result: str = ''

	for element in soup.find_all(['p', 'pre', 'blockquote']):
		if not isinstance(element, Tag):
			continue

		if element.name == 'p':
			result += f'{await _process_html_element(element)}\n'
		elif element.name == 'blockquote':
			result += f'<{element.name}>{await _process_html_element(element)}</{element.name}>\n'
		elif element.name == 'pre':
			result += f'<{element.name}>{element.get_text()}</{element.name}>\n'

	return result
