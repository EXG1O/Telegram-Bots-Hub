from telegram import Update

from service.enums import ConditionPartNextPartOperator, ConditionPartOperator
from service.models import Condition, Connection

from ..utils import replace_text_variables
from ..variables import Variables
from .base import BaseHandler

import asyncio


class ConditionHandler(BaseHandler[Condition]):
    async def handle(
        self, update: Update, condition: Condition, variables: Variables
    ) -> list[Connection] | None:
        result: bool | None = None

        for part in condition.parts:
            current_result: bool = False

            raw_first_value, raw_second_value = await asyncio.gather(
                replace_text_variables(part.first_value, variables),
                replace_text_variables(part.second_value, variables),
            )
            first_value: str | int | float | bool = deserialize_text(raw_first_value)
            second_value: str | int | float | bool = deserialize_text(raw_second_value)

            if part.operator == ConditionPartOperator.EQUAL:
                current_result = first_value == second_value
            elif part.operator == ConditionPartOperator.NOT_EQUAL:
                current_result = first_value != second_value
            elif not isinstance(first_value, str) and not isinstance(second_value, str):
                if part.operator == ConditionPartOperator.GREATER:
                    current_result = first_value > second_value
                elif part.operator == ConditionPartOperator.GREATER_OR_EQUAL:
                    current_result = first_value >= second_value
                elif part.operator == ConditionPartOperator.LESS:
                    current_result = first_value < second_value
                elif part.operator == ConditionPartOperator.LESS_OR_EQUAL:
                    current_result = first_value <= second_value

            if result is None:
                result = current_result
            elif part.next_part_operator == ConditionPartNextPartOperator.AND:
                result = result and current_result
            elif part.next_part_operator == ConditionPartNextPartOperator.OR:
                result = result or current_result

        return condition.source_connections if bool(result) else None
