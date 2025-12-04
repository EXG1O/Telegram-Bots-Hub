from enum import Enum


class ConnectionSourceObjectType(Enum):
    TRIGGER = 'trigger'
    MESSAGE = 'message'
    MESSAGE_KEYBOARD_BUTTON = 'message_keyboard_button'
    CONDITION = 'condition'
    BACKGROUND_TASK = 'background_task'
    API_REQUEST = 'api_request'
    DATABASE_OPERATION = 'database_operation'


class ConnectionTargetObjectType(Enum):
    TRIGGER = 'trigger'
    MESSAGE = 'message'
    CONDITION = 'condition'
    API_REQUEST = 'api_request'
    DATABASE_OPERATION = 'database_operation'


class APIRequestMethod(Enum):
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    PATCH = 'patch'
    DELETE = 'delete'


class MessageKeyboardType(Enum):
    DEFAULT = 'default'
    INLINE = 'inline'
    PAYMENT = 'payment'


class ConditionPartType(Enum):
    POSITIVE = '+'
    NEGATIVE = '-'


class ConditionPartOperator(Enum):
    EQUAL = '=='
    NOT_EQUAL = '!='
    GREATER = '>'
    GREATER_OR_EQUAL = '>='
    LESS = '<'
    LESS_OR_EQUAL = '<='


class ConditionPartNextPartOperator(Enum):
    AND = '&&'
    OR = '||'


class BackgroundTaskInterval(Enum):
    DAY_1 = 1
    DAY_3 = 3
    DAY_7 = 7
    DAY_14 = 14
    DAY_28 = 28
