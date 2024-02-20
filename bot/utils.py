from bs4 import BeautifulSoup, Tag, NavigableString
from typing import Any
import re


ProcessedNestedData = dict[str, str | int]

nested_data_types: tuple = (str, int)
nested_data_iterable_types: tuple = (dict, list, tuple)


async def _process_nested_data(root_key: str, data: dict[str, Any] | list | tuple) -> ProcessedNestedData:
	result: ProcessedNestedData = {}

	for key, value in data.items() if isinstance(data, dict) else enumerate(data):
		full_key = f'{root_key}.{key}'

		if isinstance(value, nested_data_types):
			result[full_key] = value
		elif isinstance(value, nested_data_iterable_types):
			result.update(await _process_nested_data(full_key, value))

	return result

async def replace_text_variables(text: str, variables: dict[str, Any]) -> str:
	for key, value in variables.items():
		if isinstance(value, nested_data_types):
			text = re.sub(r'\{\{\s*' + re.escape(key) + r'\s*\}\}', str(value), text, flags=re.IGNORECASE)
		elif isinstance(value, nested_data_iterable_types):
			text = await replace_text_variables(text, await _process_nested_data(key, value))

	return text

async def _process_element(root_element: Tag) -> str:
	result = ''

	for element in root_element.childGenerator():
		if isinstance(element, Tag):
			if element.name == 'a':
				result += f'<a href="{element["href"]}">{await _process_element(element)}</a>'
			elif element.name in ('b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del', 'tg-spoiler', 'code'):
				result += f'<{element.name}>{await _process_element(element)}</{element.name}>'
			else:
				result += await _process_element(element)
		elif isinstance(element, NavigableString):
			result += element

	return result

async def process_text_with_html_tags(text: str) -> str:
	soup = BeautifulSoup(text, 'lxml')
	result = ''

	for element in soup.find_all(('p', 'pre', 'blockquote')):
		if isinstance(element, Tag):
			if element.name == 'p':
				result += f'{await _process_element(element)}\n'
			elif element.name == 'blockquote':
				result += f'<{element.name}>{await _process_element(element)}</{element.name}>\n'
			elif element.name == 'pre':
				result += f'<{element.name}>{element.get_text()}</{element.name}>\n'

	return result