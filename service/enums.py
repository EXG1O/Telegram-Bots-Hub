from enum import IntEnum, StrEnum


class ConnectionSourceObjectType(StrEnum):
    TRIGGER = 'trigger'
    MESSAGE = 'message'
    MESSAGE_KEYBOARD_BUTTON = 'message_keyboard_button'
    CONDITION = 'condition'
    BACKGROUND_TASK = 'background_task'
    API_REQUEST = 'api_request'
    DATABASE_OPERATION = 'database_operation'
    INVOICE = 'invoice'
    TEMPORARY_VARIABLE = 'temporary_variable'


class ConnectionTargetObjectType(StrEnum):
    TRIGGER = 'trigger'
    MESSAGE = 'message'
    CONDITION = 'condition'
    API_REQUEST = 'api_request'
    DATABASE_OPERATION = 'database_operation'
    INVOICE = 'invoice'
    TEMPORARY_VARIABLE = 'temporary_variable'


class APIRequestMethod(StrEnum):
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    PATCH = 'patch'
    DELETE = 'delete'


class MessageKeyboardType(StrEnum):
    DEFAULT = 'default'
    INLINE = 'inline'
    PAYMENT = 'payment'


class MessageKeyboardButtonStyle(StrEnum):
    DEFAULT = 'default'
    PRIMARY = 'primary'
    SUCCESS = 'success'
    DANGER = 'danger'


class ConditionPartType(StrEnum):
    POSITIVE = '+'
    NEGATIVE = '-'


class ConditionPartOperator(StrEnum):
    EQUAL = '=='
    NOT_EQUAL = '!='
    GREATER = '>'
    GREATER_OR_EQUAL = '>='
    LESS = '<'
    LESS_OR_EQUAL = '<='


class ConditionPartNextPartOperator(StrEnum):
    AND = '&&'
    OR = '||'


class BackgroundTaskInterval(IntEnum):
    DAY_1 = 1
    DAY_3 = 3
    DAY_7 = 7
    DAY_14 = 14
    DAY_28 = 28
