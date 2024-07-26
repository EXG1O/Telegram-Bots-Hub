from .enums import APIRequestMethod

from dataclasses import dataclass


@dataclass
class CommandMedia:
	id: int
	position: int
	name: str | None
	size: int | None
	url: str | None
	from_url: str | None


@dataclass
class APIRequest:
	url: str
	method: APIRequestMethod
	headers: str | None
	body: str | None
