class TelegramError(Exception):
    pass


class InvalidTokenError(TelegramError):
    pass


class ForbiddenError(TelegramError):
    pass


class ChatMigratedError(TelegramError):
    pass


class BadRequestError(TelegramError):
    pass


class ConflictError(TelegramError):
    pass


class NetworkError(TelegramError):
    pass
