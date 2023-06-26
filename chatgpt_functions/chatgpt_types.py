from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Roles(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = 'function' 

@dataclass
class Message:
    role: Roles
    content: str
    name: Optional[str] = None

    def __dict__(self):
        tmp = {"role": self.role.value, "content": self.content}
        if self.name:
            tmp["name"] = self.name
        return tmp