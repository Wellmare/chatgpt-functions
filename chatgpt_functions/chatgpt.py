import asyncio
import json
import sys
import typing
from dataclasses import dataclass
from typing import Optional

import openai
from loguru import logger

from .chatgpt_function import ChatGptFunction
from .chatgpt_types import Message, Roles, FunctionCall
from .function_parameters import Parameters, Property


@dataclass
class UsageTokens:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatGPTFunctionsMethodResponse:
    is_function_called: bool
    function_response: typing.Any
    chatgpt_response_message: Message
    usage_tokens: UsageTokens
    function_args: Optional[dict] = None


@dataclass
class ChatGPTMethodResponse:
    chatgpt_response_message: Message
    usage_tokens: UsageTokens


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
    messages: list[Message] = []

    def __init__(
            self,
            openai_api_key: str,
            messages: list[Message] | None = None,
            model: str = "gpt-3.5-turbo",
            is_log: bool = False,
            is_debug: bool = False,
    ):
        openai.api_key = openai_api_key
        self.model = model
        if messages:
            self.messages = messages
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
    async def get_chatgpt_response(self, messages_to_set: list[Message] | None = None, temperature: float = 0.5,
                                   max_tokens: int = 1024, ) -> ChatGPTMethodResponse:
        if messages_to_set is not None:
            self.messages = messages_to_set

        self.log_debug(f"messages: {self.messages}")
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[message.__dict__() for message in self.messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self.log_debug(f"response: {response}")

        response_message = response["choices"][0]["message"]

        chatgpt_message = Message(role=Roles.ASSISTANT, content=response_message['content'], )

        self.log_debug(f"response_message: {response_message}")

        usage_tokens = UsageTokens(prompt_tokens=response['usage']['prompt_tokens'],
                                   completion_tokens=response['usage']['completion_tokens'],
                                   total_tokens=response['usage']['total_tokens'],
                                   )
        return ChatGPTMethodResponse(
            chatgpt_response_message=chatgpt_message,
            usage_tokens=usage_tokens,
        )

    @retry_decorator(tries=3, delay=2)
    async def get_chatgpt_response_with_functions(
            self,
            functions: list[ChatGptFunction],
            messages_to_set: list[Message] | None = None,
            temperature: float = 0.5,
            max_tokens: int = 1024,
            is_add_function_output: bool = False,
    ) -> ChatGPTFunctionsMethodResponse:
        # try:
        if messages_to_set is not None:
            self.messages = messages_to_set

        self.log_debug(f"messages: {self.messages}")

        functions_to_chatgpt = [
            function.append_available_functions(self.AVAILABLE_FUNCTIONS)
            or function.__dict__()
            for function in functions
        ]
        self.log_debug(f"functions_to_chatgpt: {functions_to_chatgpt}")
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[message.__dict__() for message in self.messages],
            functions=functions_to_chatgpt,
            function_call="auto",  # auto is default, but we'll be explicit,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self.log_debug(f"response: {response}")

        response_message = response["choices"][0]["message"]
        self.log_debug(f"response_message: {response_message}")

        usage_tokens = UsageTokens(prompt_tokens=response['usage']['prompt_tokens'],
                                   completion_tokens=response['usage']['completion_tokens'],
                                   total_tokens=response['usage']['total_tokens'],
                                   )

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

            chatgpt_message = Message(role=Roles.ASSISTANT, content=response_message['content'],
                                      function_call=FunctionCall(name=function_name,
                                                                 arguments=response_message["function_call"][
                                                                     "arguments"]))

            if is_add_function_output:
                self.log_debug("Add function response to messages")
                self.messages.append(
                    Message(
                        role=Roles.FUNCTION,
                        name=function_name,
                        content=json.dumps(function_response),
                    )
                )
                self.messages.append(chatgpt_message)
            return ChatGPTFunctionsMethodResponse(
                is_function_called=True,
                function_response=function_response,
                function_args=function_args if bool(function_args) else None,
                chatgpt_response_message=chatgpt_message,
                usage_tokens=usage_tokens
            )
        else:
            self.log_info("The function is not called")
            # print(response["choices"][0]["message"])
            # return response["choices"][0]["message"]
            return ChatGPTFunctionsMethodResponse(
                is_function_called=False,
                function_response=None,
                chatgpt_response_message=Message(role=Roles.ASSISTANT, content=response_message['content']),
                usage_tokens=usage_tokens
            )

    # except Exception as e:
    #     self.log_error(f"Error with get_chatgpt_response_with_functions: {e}")
    #     raise e
