from datetime import datetime, timedelta
from dataclasses import dataclass

from typing import Callable, Iterable, Any


def in_n_seconds(n: float) -> datetime:
    """Returns datetime object of current time + n seconds."""
    return datetime.now() + timedelta(seconds=n)


NO_ARG = "no-arg"


@dataclass
class CallEvent:
    to_call: Callable | Iterable[Callable]
    at_time: datetime | None = None
    args: Any | Iterable[Any] | None = None

    def __post_init__(self) -> None:
        if self.args is not None:
            if not isinstance(self.args, Iterable):
                self.args = [self.args]


class EventLoop:
    """Contains and manages events from an category."""

    loops = []

    @staticmethod
    def execute_all_loops():
        """Execute all awaiting events in every loop."""
        for loop in EventLoop.loops:
            loop.execute_awaiting()

    def __init__(self) -> None:
        self.events: list[CallEvent] = []
        EventLoop.loops.append(self)

    def add_event(self, event: CallEvent) -> None:
        """Adds new event to loop's stack."""
        self.events.append(event)

    def fetch_awaiting(self) -> list[CallEvent]:
        """Fetches event's from this loop's stack that should be executed."""
        awaiting = []
        for event in self.events:
            if event.at_time is None or event.at_time <= datetime.now():
                awaiting.append(event)
                self.events.remove(event)
        return awaiting

    def execute_awaiting(self) -> None:
        """Execute all awaiting events."""
        for event in self.fetch_awaiting():
            call_stack = event.to_call
            if not isinstance(call_stack, Iterable):
                call_stack = [call_stack]
            for i, to_call in enumerate(call_stack):
                if event.args is None:
                    to_call()
                    continue

                try:
                    arg = event.args[i]
                    if arg != NO_ARG:
                        to_call(arg)
                    else:
                        to_call()
                except IndexError:
                    to_call()

    def clear(self) -> None:
        """Clear all saved, not executed events from stack."""
        self.events = []


main_loop = EventLoop()
anim_loop = EventLoop()
move_loop = EventLoop()
