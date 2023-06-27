import json

import openai
from .chatgpt_function import ChatGptFunction
from .chatgpt_types import Message, Roles
from .function_parameters import Parameters, Property
import typing
from dataclasses import dataclass


@dataclass
class ChatGPTMethodReponse:
    is_function_called: bool
    function_response: None | typing.Any
    chatgpt_response_message: Message


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
        self,
        functions: list[ChatGptFunction],
        messages: list[Message] | None = None,
        temperature: float = 0.5,
        max_tokens: int = 1024,
        is_add_function_output: bool = False,
    ) -> ChatGPTMethodReponse:
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
            function_call="auto",  # auto is default, but we'll be explicit,
            temperature=temperature,
            max_tokens=max_tokens,
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
            if is_add_function_output:
                self.messages.append(
                    Message(
                        role=Roles.FUNCTION,
                        name=function_name,
                        content=json.dumps(function_response),
                    )
                )
            return ChatGPTMethodReponse(
                is_function_called=True,
                function_response=function_response,
                chatgpt_response_message=response_message,
            )
        else:
            # print("Функция не вызвана")
            # print(response["choices"][0]["message"])
            # return response["choices"][0]["message"]
            return ChatGPTMethodReponse(
                is_function_called=False,
                function_response=None,
                chatgpt_response_message=response_message,
            )
