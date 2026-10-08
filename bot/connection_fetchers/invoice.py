from telegram import Message, SuccessfulPayment, Update

from service import Connection, Invoice

from ..context import Context
from .base import BaseConnectionFetcher


class InvoiceConnectionFetcher(BaseConnectionFetcher):
    async def fetch(self, update: Update, context: Context) -> list[Connection] | None:
        message: Message | None = update.message

        if not message:
            return None

        payment: SuccessfulPayment | None = message.successful_payment

        if not payment:
            return None

        invoice: Invoice = await self._bot.service.get_invoice(
            id=int(payment.invoice_payload)
        )
        return invoice.source_connections
