from dataclasses import dataclass


@dataclass(frozen=True)
class Media:
    name: str | None
    size: int | None
    url: str | None
    from_url: str | None


@dataclass(frozen=True)
class MessageMedia(Media):
    id: int
    position: int
