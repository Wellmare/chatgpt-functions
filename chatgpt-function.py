import json

import openai
import asyncio
from dataclasses import dataclass


from config import API_KEY
from mytypes import Message, Roles

openai.api_key = API_KEY

AVAILABLE_FUNCTIONS = {}


@dataclass(init=False)
class Property:
    kwargs = []

    def __init__(self, property_name: str, prop_type: str, description: str, **kwargs):
        self.property_name = property_name
        self.prop_type = prop_type
        self.description = description
        self.kwargs = kwargs

    property_name: str
    prop_type: str
    description: str


def prepare_parameters(properties: list[Property], required: list | bool = True):
    properties_dict = {}
    required_list = required
    for prop in properties:
        properties_dict[prop.property_name] = {
            "type": prop.prop_type,
            "description": prop.description,
        }
        for key, value in prop.kwargs.items():
            properties_dict[prop.property_name][key] = value
    if required == True:
        required_list = [prop.property_name for prop in properties]

    return {
        "type": "object",
        "properties": properties_dict,
        "required": required_list,
    }


class ChatGptFunction:
    def __init__(self, function: callable, parameters: dict, function_description: str):
        self.function = function
        self.function_description = function_description
        self.parameters = parameters
        self.function_name = function.__name__

        AVAILABLE_FUNCTIONS[self.function_name] = function

    def __dict__(self):
        return {
            "name": self.function_name,
            "description": self.function_description,
            "parameters": self.parameters,
        }


async def get_chatgpt_response_with_functions(
    functions: list[ChatGptFunction], messages: list[Message]
):
    functions_to_chatgpt = [function.__dict__() for function in functions]

    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo-0613",
        messages=[message.__dict__() for message in messages],
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
        function_to_call = AVAILABLE_FUNCTIONS[function_name]
        function_args = json.loads(response_message["function_call"]["arguments"])
        function_response = function_to_call(function_args)
    else:
        print("Функция не вызвана")
        print(response["choices"][0]["message"])


async def main():
    def hello(args):
        text, suffix = args.values()
        print(text, suffix)

    def get_weather(args):
        country, lang = args.values()

        weather_info = {
            "temperature": "37C",
            "lang": lang,
            "forecast": ["sunny", "windy"],
        }
        print(f"get weather with params: {args.values()}")
        return json.dumps(weather_info)

    hello_func = ChatGptFunction(
        function=hello,
        parameters=prepare_parameters(
            properties=[
                Property(
                    property_name="text", prop_type="string", description="Text to say"
                ),
                Property(
                    property_name="suffix",
                    prop_type="string",
                    description="Suffix to text",
                ),
            ]
        ),
        function_description="Say text",
    )

    get_weather_func = ChatGptFunction(
        function=get_weather,
        parameters=prepare_parameters(
            properties=[
                Property(
                    property_name="country",
                    prop_type="string",
                    description="Country (Russia, USA, etc)",
                ),
                Property(
                    property_name="lang",
                    prop_type="string",
                    description="Language (RU, EN)",
                    enum=["RU", "EN"],
                ),
            ]
        ),
        function_description='Get weather'
    )
    await get_chatgpt_response_with_functions(
        functions=[hello_func, get_weather_func],
        messages=[
            Message(
                role=Roles.USER,
                content='Назови мне погоду на русском в США',
            )
        ],
    )


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(main())


# async def run_conversation(messages: list):
#     # Step 1: send the conversation and available functions to GPT
#     functions = [
#         {
#             "name": "answer_to_user",
#             "description": "Reply to a user with a message",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "answer": {
#                         "type": "string",
#                         "description": "Message to answer",
#                     },
#                     "username": {
#                         "type": "string",
#                         "description": "To the username of the user to whom you want to reply",
#                     },
#                 },
#                 "required": ["answer", "username"],
#             },
#         }
#     ]
#     response = await openai.ChatCompletion.acreate(
#         model="gpt-3.5-turbo-0613",
#         messages=messages,
#         functions=functions,
#         function_call="auto",  # auto is default, but we'll be explicit
#     )
#     response_message = response["choices"][0]["message"]


#     # Step 2: check if GPT wanted to call a function
#     if response_message.get("function_call"):
#         # Step 3: call the function
#         # Note: the JSON response may not always be valid; be sure to handle errors
#         available_functions = {
#             "answer_to_user": answer_to_user,
#         }  # only one function in this example, but you can have multiple
#         function_name = response_message["function_call"]["name"]
#         fuction_to_call = available_functions[function_name]
#         function_args = json.loads(response_message["function_call"]["arguments"])
#         function_response = fuction_to_call(
#             answer=function_args.get("answer"),
#             username=function_args.get("username"),
#         )
#         messages.append(
#             {
#                 "role": "system",
#                 "content": f"**TO: '{function_args.get('username')}'**. {function_args.get('answer')}",
#             }
#         )
#         messages.remove(system_message)
#         if recurse_number == 1:
#             messages.append(
#                 {
#                     "role": "user",
#                     "content": "**USERNAME: 'ivan'**. Я все равно тебе не верю. Ты ведь как и я любишь наркотики?",
#                 },
#             )
#             messages.append(system_message)
#             await run_conversation(messages, recurse_number=recurse_number + 1)
#         # messages.append(
#         #     {
#         #         "role": "system",
#         #         "content": f"Why did you choose {function_args.get('ad')}? Write five clear and understandable reasons in the form of a list",
#         #     }
#         # )
#         # second_response = openai.ChatCompletion.create(
#         #     model="gpt-3.5-turbo-0613",
#         #     messages=messages,
#         # )  # get a new response from GPT where it can see the function response
#         # return second_response["choices"][0]["message"]
#     else:
#         print("Функция не вызвана")
#         print(response["choices"][0]["message"])
