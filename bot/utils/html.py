from html.parser import HTMLParser
from typing import TYPE_CHECKING, Final
import html

ALLOWED_TAGS: Final[list[str]] = [
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
    'a',
    'code',
    'pre',
    'blockquote',
]
SELF_CLOSING_TAGS: Final[list[str]] = ['br']


class HTMLTextFormatter(HTMLParser):
    if TYPE_CHECKING:
        result: str
        stack: list[tuple[str, int, int]]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SELF_CLOSING_TAGS:
            return

        old_result_length: int = len(self.result)

        if tag == 'a':
            href: str | None = dict(attrs).get('href')

            if not href:
                return

            self.result += f'<a href="{href}">'
        elif tag in ALLOWED_TAGS:
            self.result += f'<{tag}>'

        self.stack.append((tag, old_result_length, len(self.result)))

    def handle_endtag(self, tag: str) -> None:
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

            if tag in ALLOWED_TAGS:
                self.result += f'</{tag}>'

            if tag in ['p', 'blockquote', 'pre']:
                self.result += '\n'

    def handle_data(self, data: str) -> None:
        self.result += html.escape(data)

    def close(self) -> None:
        while self.stack:
            tag, start_index, end_index = self.stack.pop()
            self.result = self.result[:start_index] + self.result[end_index:]
        self.result = self.result.removesuffix('\n')
        super().close()

    def reset(self) -> None:
        self.stack = []
        self.result = ''
        super().reset()

    async def __call__(self, data: str) -> str:
        self.feed(data.replace('&nbsp;', ' '))
        self.close()

        result: str = self.result

        self.reset()

        return result


process_html_text = HTMLTextFormatter()
