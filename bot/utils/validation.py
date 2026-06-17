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
