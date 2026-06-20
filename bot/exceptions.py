class NoTriggerSubscribersError(Exception):
    def __init__(self, trigger_id: int) -> None:
        self.trigger_id = trigger_id
        super().__init__(f'No subscribers found for trigger (service_id={trigger_id}).')
