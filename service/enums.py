from enum import StrEnum


class ConnectionObjectType(StrEnum):
    TRIGGER = 'trigger'
    MESSAGE = 'message'
    MESSAGE_KEYBOARD_BUTTON = 'message_keyboard_button'
    CONDITION = 'condition'
    BACKGROUND_TASK = 'background_task'
    API_REQUEST = 'api_request'
    DATABASE_OPERATION = 'database_operation'
    INVOICE = 'invoice'
    TEMPORARY_VARIABLE = 'temporary_variable'
    TIMER = 'timer'
    RANDOMIZER = 'randomizer'


class ConnectionSourceObjectType(StrEnum):
    TRIGGER = ConnectionObjectType.TRIGGER
    MESSAGE = ConnectionObjectType.MESSAGE
    MESSAGE_KEYBOARD_BUTTON = ConnectionObjectType.MESSAGE_KEYBOARD_BUTTON
    CONDITION = ConnectionObjectType.CONDITION
    BACKGROUND_TASK = ConnectionObjectType.BACKGROUND_TASK
    API_REQUEST = ConnectionObjectType.API_REQUEST
    DATABASE_OPERATION = ConnectionObjectType.DATABASE_OPERATION
    INVOICE = ConnectionObjectType.INVOICE
    TEMPORARY_VARIABLE = ConnectionObjectType.TEMPORARY_VARIABLE
    TIMER = ConnectionObjectType.TIMER
    RANDOMIZER = ConnectionObjectType.RANDOMIZER


class ConnectionTargetObjectType(StrEnum):
    TRIGGER = ConnectionObjectType.TRIGGER
    MESSAGE = ConnectionObjectType.MESSAGE
    CONDITION = ConnectionObjectType.CONDITION
    API_REQUEST = ConnectionObjectType.API_REQUEST
    DATABASE_OPERATION = ConnectionObjectType.DATABASE_OPERATION
    INVOICE = ConnectionObjectType.INVOICE
    TEMPORARY_VARIABLE = ConnectionObjectType.TEMPORARY_VARIABLE
    TIMER = ConnectionObjectType.TIMER
    RANDOMIZER = ConnectionObjectType.RANDOMIZER


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


class BackgroundTaskStatus(StrEnum):
    PENDING = 'pending'
    RUNNING = 'running'


class ChatType(StrEnum):
    PRIVATE = 'private'
    GROUP = 'group'
    SUPERGROUP = 'supergroup'
    CHANNEL = 'channel'
