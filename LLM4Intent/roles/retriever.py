import json
import logging
from typing import List
from openai import Client
from openai.types.chat import ChatCompletionMessage
from LLM4Intent.common.state import DataMissing, State
from LLM4Intent.common.utils import get_logger, get_prompt


class Retriever:
    def __init__(self, model: str, state: State, client: Client):
        self.name = "retriever"
        self.model = model
        self.state = state
        self.client = client
        self.system_message = get_prompt("retriever")
        self.log = get_logger("Retriever")

    def call_tools(self, response: ChatCompletionMessage) -> list:
        if not response.tool_calls:
            raise ValueError("No tool calls in response.")

        tool_messages = [
            response.to_dict(),
        ]

        for tool_call in response.tool_calls:
            tool_name = tool_call.function.name

            tool_args = json.loads(tool_call.function.arguments)
            # if self.state.has_tool_called(tool_name, tool_args):
            #     raise ValueError(f"Tool {tool_name} with args {tool_args} already called.")

            # call function from self.state
            tool = getattr(self.state, tool_name, None)
            if tool:
                try:
                    result = tool(**tool_args)
                    tool_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result),
                        }
                    )
                except Exception as e:
                    self.log.error(
                        f"Error in tool {tool_name} with args {tool_args}: {e}"
                    )
                    tool_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(e),
                        }
                    )
            else:
                raise ValueError(f"Tool {tool_name} not found in state.")
        return tool_messages

    def retrieve(self) -> None:
        # data_missing = (
        #     self.state.data_missing
        #     if self.state.data_missing
        #     else []
        # )

        # human_message = f"Please retrieve the missing data: {json.dumps([dm.model_dump() for dm in data_missing])}"
        system_message = self.system_message.format()
        messages = [
            {"role": "system", "content": system_message},
            *self.state.chat_history,
            {"role": "user", "content": "Please retrieve the missing data."},
        ]
        self.log.info(messages)
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
            tools=self.state.openai_tools,
            tool_choice="auto",
        )
        self.log.info(completion)
        response = completion.choices[0].message

        if response.tool_calls:
            # try:
            results = self.call_tools(response)
            self.state.chat_history.extend(
                [
                    {"role": "user", "content": "Please retrieve the missing data."},
                    *results,
                ]
            )
            self.log.info(f"Results from tool calls: {results}")
        # except Exception as e:
        #     raise ValueError(f"Error calling tools: {e}")
        else:
            raise ValueError("No tool calls in response.")

        self.state.last_speaker = self.name
