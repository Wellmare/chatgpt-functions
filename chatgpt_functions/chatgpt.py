import asyncio
import json
import sys
import typing
from dataclasses import dataclass

import openai
from loguru import logger
from retry import retry

from .chatgpt_function import ChatGptFunction
from .chatgpt_types import Message, Roles
from .function_parameters import Parameters, Property


@dataclass
class ChatGPTMethodReponse:
    is_function_called: bool
    function_response: None | typing.Any
    chatgpt_response_message: Message


class MaxRetriesExceeded(Exception):
    pass


def retry_decorator(tries: int, delay: int):
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            attempt = 1
            while attempt <= tries:
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Exception! Attempt {attempt}/{tries} ({e})")
                    attempt += 1
                    if not attempt <= tries:
                        break
                    await asyncio.sleep(delay)

            self.logger.error(f"Exception! Exceeded number of attempts ({tries})")
            raise MaxRetriesExceeded(f"Exceeded number of attempts ({tries})")

        return wrapper

    return decorator


class ChatGPT:
    AVAILABLE_FUNCTIONS = {}

    def __init__(
        self,
        openai_api_key: str,
        messages: list[Message] = [],
        model: str = "gpt-3.5-turbo-0613",
        is_log: bool = False,
        is_debug: bool = False,
    ):
        openai.api_key = openai_api_key
        self.model = model
        self.messages: list[Message] = []
        self.is_log = is_log
        self.logger = logger
        if not is_debug:
            self.logger.add(sys.stderr, level="INFO")

    def log_info(self, message):
        if self.is_log:
            self.logger.info(message)

    def log_error(self, message):
        if self.is_log:
            self.logger.error(message)

    def log_debug(self, message):
        if self.is_log:
            self.logger.debug(message)

    @retry_decorator(tries=3, delay=2)
    async def get_chatgpt_response_with_functions(
        self,
        functions: list[ChatGptFunction],
        messages: list[Message] | None = None,
        temperature: float = 0.5,
        max_tokens: int = 1024,
        is_add_function_output: bool = False,
    ) -> ChatGPTMethodReponse:
        # try:
        if messages is not None:
            self.messages = messages

        self.log_debug(f"messages: {messages}")

        functions_to_chatgpt = [
            function.append_avaliable_functions(self.AVAILABLE_FUNCTIONS)
            or function.__dict__()
            for function in functions
        ]
        self.log_debug(f"functions_to_chatgpt: {functions_to_chatgpt}")
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo-0613",
            messages=[message.__dict__() for message in self.messages],
            functions=functions_to_chatgpt,
            function_call="auto",  # auto is default, but we'll be explicit,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self.log_debug(f"response: {response}")

        response_message = response["choices"][0]["message"]
        self.log_info(f"response_message: {response_message}")

        if response_message.get("function_call"):
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            # only one function in this example, but you can have multiple
            function_name = response_message["function_call"]["name"]
            function_to_call = self.AVAILABLE_FUNCTIONS[function_name]
            function_args = json.loads(response_message["function_call"]["arguments"])

            self.log_info(f"Call function {function_name} with args {function_args}")

            function_response = function_to_call(function_args)

            self.log_info(f"function_response: {function_response}")

            if is_add_function_output:
                self.log_debug("Add function response to messages")
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
            self.log_info("The function is not called")
            # print(response["choices"][0]["message"])
            # return response["choices"][0]["message"]
            return ChatGPTMethodReponse(
                is_function_called=False,
                function_response=None,
                chatgpt_response_message=response_message,
            )

    # except Exception as e:
    #     self.log_error(f"Error with get_chatgpt_response_with_functions: {e}")
    #     raise e
