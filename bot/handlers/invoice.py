from telegram.models import Chat, LabeledPrice, Update

from service.models import Connection, Invoice

from ..context import HandlerContext
from ..utils.variables import replace_text_variables
from .base import BaseHandler

import asyncio


class InvoiceHandler(BaseHandler[Invoice]):
    async def handle(
        self, update: Update, invoice: Invoice, context: HandlerContext
    ) -> list[Connection] | None:
        chat: Chat | None = update.effective_chat

        if not chat:
            return None

        title, description = await asyncio.gather(
            replace_text_variables(invoice.title, context.variables),
            replace_text_variables(invoice.description, context.variables),
        )
        photo_url: str | None = None

        if invoice.image:
            photo_url = invoice.image.url or invoice.image.from_url

        await self.bot.telegram.send_invoice(
            chat.id,
            title=title,
            photo_url=photo_url,
            description=description,
            prices=[
                LabeledPrice(price.label, price.amount) for price in invoice.prices
            ],
            protect_content=True,
        )

        return invoice.source_connections
