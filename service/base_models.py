from dataclasses import dataclass


@dataclass
class CommandMedia:
    id: int
    position: int
    name: str | None
    size: int | None
    url: str | None
    from_url: str | None
