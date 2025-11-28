from dataclasses import dataclass


@dataclass(frozen=True)
class CommandMedia:
    id: int
    position: int
    name: str | None
    size: int | None
    url: str | None
    from_url: str | None
