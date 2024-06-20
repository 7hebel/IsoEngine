from datetime import datetime, timedelta


class Cooldown:
    """Manages abilities cooldown."""
    
    def __init__(self, cooldown_seconds: float) -> None:
        self.secs = cooldown_seconds
        self.__until = datetime.now()

    def __get_new_cooldown_end(self) -> datetime:
        return datetime.now() + timedelta(seconds=self.secs)

    def start_cooldown(self) -> None:
        self.__until = self.__get_new_cooldown_end()

    def is_on_cooldown(self) -> bool:
        return self.__until > datetime.now()

    def reset(self) -> None:
        self.__until = datetime.now()


jump_cooldown = Cooldown(1)
