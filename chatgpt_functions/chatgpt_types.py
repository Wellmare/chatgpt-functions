from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional


class Roles(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = 'function'


@dataclass
class FunctionCall:
    name: str
    arguments: str

    def dict(self):
        return {k: str(v) for k, v in asdict(self).items()}


@dataclass
class Message:
    role: Roles
    content: str
    function_call: Optional[FunctionCall] = None
    name: Optional[str] = None

    def __dict__(self):
        tmp = {"role": self.role.value, "content": self.content}
        if self.name:
            tmp["name"] = self.name
        if self.function_call:
            tmp["function_call"] = self.function_call.dict()
        return tmp
