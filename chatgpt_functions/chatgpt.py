import json

import openai
from .chatgpt_function import ChatGptFunction
from .chatgpt_types import Message, Roles
from .function_parameters import Parameters, Property


class ChatGPT:
    AVAILABLE_FUNCTIONS = {}

    def __init__(
        self,
        openai_api_key: str,
        messages: list[Message] = [],
        model: str = "gpt-3.5-turbo-0613",
    ):
        openai.api_key = openai_api_key
        self.model = model
        self.messages: list[Message] = []

    async def get_chatgpt_response_with_functions(
        self, functions: list[ChatGptFunction], messages: list[Message] | None = None
    ) -> None | str:
        if messages is not None:
            self.messages = messages
        functions_to_chatgpt = [
            function.append_avaliable_functions(self.AVAILABLE_FUNCTIONS)
            or function.__dict__()
            for function in functions
        ]

        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo-0613",
            messages=[message.__dict__() for message in self.messages],
            functions=functions_to_chatgpt,
            function_call="auto",  # auto is default, but we'll be explicit
        )
        response_message = response["choices"][0]["message"]
        print(response_message)

        if response_message.get("function_call"):
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            # only one function in this example, but you can have multiple
            function_name = response_message["function_call"]["name"]
            function_to_call = self.AVAILABLE_FUNCTIONS[function_name]
            function_args = json.loads(response_message["function_call"]["arguments"])
            function_response = function_to_call(function_args)
        else:
            print("Функция не вызвана")
            print(response["choices"][0]["message"])
            return response["choices"][0]["message"]
