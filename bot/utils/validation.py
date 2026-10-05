import service


def is_service_subject_allowed(
    bot: service.Bot, subject: service.Chat | service.User
) -> bool:
    return not (subject.is_blocked or bot.is_private and not subject.is_allowed)


def are_service_subjects_allowed(
    bot: service.Bot, chat: service.Chat, user: service.User | None = None
) -> bool:
    return is_service_subject_allowed(bot=bot, subject=chat) and (
        not user or is_service_subject_allowed(bot=bot, subject=user)
    )
