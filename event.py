from ryu.controller import ofp_event, event

class EventMessage(event.EventBase):
    def __init__(self, message):
        super(EventMessage, self).__init__()
        self.message = message