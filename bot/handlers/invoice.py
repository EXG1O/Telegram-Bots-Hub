from telegram import Chat, LabeledPrice, Update

from service import Invoice

from ..context import Context
from ..utils.variables import replace_text_variables
from .base import BaseHandler

import asyncio


class InvoiceHandler(BaseHandler[Invoice]):
    async def handle(self, update: Update, invoice: Invoice, context: Context) -> None:
        chat: Chat | None = update.effective_chat

        if not chat:
            return

        title, description = await asyncio.gather(
            replace_text_variables(invoice.title, context.variables),
            replace_text_variables(invoice.description, context.variables),
        )
        photo_url: str | None = None

        if invoice.image:
            photo_url = invoice.image.url or invoice.image.from_url

        await self._bot.telegram.send_invoice(
            chat.id,
            title=title,
            photo_url=photo_url,
            description=description,
            prices=[
                LabeledPrice(price.label, price.amount) for price in invoice.prices
            ],
            payload=str(invoice.id),
            protect_content=True,
        )
