from service.models import Bot as ServiceBot
from service.models import Chat as ServiceChat
from service.models import User as ServiceUser


def is_subject_allowed(
    service_bot: ServiceBot, service_subject: ServiceChat | ServiceUser
) -> bool:
    return not (
        service_subject.is_blocked
        or service_bot.is_private
        and not service_subject.is_allowed
    )


def are_subjects_allowed(
    service_bot: ServiceBot,
    service_chat: ServiceChat,
    service_user: ServiceUser | None = None,
) -> bool:
    return is_subject_allowed(
        service_bot=service_bot, service_subject=service_chat
    ) and (
        not service_user
        or is_subject_allowed(service_bot=service_bot, service_subject=service_user)
    )
