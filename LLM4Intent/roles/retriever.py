
import json
import logging
from openai import Client
from LLM4Intent.common.state import DataMissing, State
from LLM4Intent.common.utils import get_logger, get_prompt


class Retriever():
    def __init__(self, model: str, state: State, client: Client):
        self.name = "retriever"
        self.model = model
        self.state = state
        self.client = client
        self.system_message = get_prompt("retriever")
        self.log = get_logger("Retriever")

    def retrieve(self) -> None:
        data_missing = (
            self.state.current_check_report.data_missing
            if self.state.current_check_report
            else []
        )
        if not data_missing:
            data_missing = [
                DataMissing(
                    tool_name="get_transaction_from_jsonrpc",
                    tool_args={"transaction_hash": self.state.task},
                ),
                DataMissing(
                    tool_name="get_transaction_receipt_without_logs_from_jsonrpc",
                    tool_args={"transaction_hash": self.state.task},
                ),
            ]

        human_message = f"Please retrieve the missing data: {json.dumps([dm.model_dump() for dm in data_missing])}"
        system_message = self.system_message.format(
            data_analyzed=json.dumps(list(self.state.data_analyzed.keys()))
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": human_message},
        ]
        self.log.info(messages)
        completion =            self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                tools=self.state.openai_tools,
                tool_choice="auto",
                parallel_tool_calls=True,
                # tool_choice={"type": "function"}
            )
        print(completion)
        response = (
            completion
            .choices[0]
            .message
        )
        self.log.info(response)

        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                data_key = f"{tool_name}({json.dumps(tool_args).removeprefix('{').removesuffix('}')})"
                if data_key in self.state.data_analyzed:
                    self.state.data_analyzing.append(self.state.data_analyzed[data_key])
                    continue

                # call function from self.state
                tool = getattr(self.state, tool_name, None)
                if tool:
                    try:
                        result = tool(**tool_args)
                        doc = {
                            "content": f"{tool_name}({json.dumps(tool_args).removeprefix('{').removesuffix('')}):\n\n{result}",
                            "metadata": {
                                "tool_name": tool_name,
                                "tool_args": tool_args,
                                "tool_result": result,
                            },
                        }
                        self.state.data_analyzing.append(doc)
                    except Exception as e:
                        self.log.error(f"Error in tool {tool_name} with args {tool_args}: {e}")
                        doc = {
                            "content": f"{tool_name}({json.dumps(tool_args).removeprefix('{').removesuffix('')}):\n\n{str(e)}",
                            "metadata": {
                                "tool_name": tool_name,
                                "tool_args": tool_args,
                                "tool_error": str(e),
                            },
                        }
                        self.state.data_analyzing.append(doc)
                else:
                    self.log.error(f"Tool {tool_name} not found.")
        else:
            self.log.error("No tool calls in response.")
        self.state.last_speaker = self.name

