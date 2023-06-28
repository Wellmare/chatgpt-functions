from .function_parameters import Parameters


class ChatGptFunction:
    def __init__(self, function: callable, parameters: Parameters, function_description: str):
        self.function: callable = function
        self.function_description: str = function_description
        self.parameters: dict = parameters.prepare()
        self.function_name: str = function.__name__

    def append_available_functions(self, AVAILABLE_FUNCTIONS: dict) -> None:
        AVAILABLE_FUNCTIONS[self.function_name] = self.function

    def __dict__(self):
        return {
            "name": self.function_name,
            "description": self.function_description,
            "parameters": self.parameters,
        }
