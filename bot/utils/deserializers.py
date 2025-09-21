from contextlib import suppress


def deserialize_text(text: str) -> str | int | float | bool:
    if text.lower() in ['true', 'false']:
        return text.lower() == 'true'

    with suppress(ValueError):
        return int(text)

    with suppress(ValueError):
        return float(text)

    return text
