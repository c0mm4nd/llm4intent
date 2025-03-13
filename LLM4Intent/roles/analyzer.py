import json
import logging

from openai import Client
from pydantic import BaseModel, Field
from LLM4Intent.common.state import State
from LLM4Intent.common.utils import get_logger, get_prompt


class Analyzer:
    def __init__(self, model: str, state: State, client: Client):
        self.name = "analyzer"
        self.model = model
        self.client = client
        self.state = state
        self.system_message = get_prompt("analyzer")
        self.log = get_logger("Analyzer")

    def analyze(self) -> str:
        tool_call_docs = self.state.get_data_analyzing()
        all_content = "\n\n".join([doc["content"] for doc in tool_call_docs])
        human_message = f"Please analyze against the data:\n\n{all_content} \n\n"
        system_message = self.system_message.format(
            hierarchical_intents=json.dumps(self.state.hierarchical_intents),
            data_analyzing=json.dumps(self.state.get_data_analyzing_tools()),
            data_analyzed=json.dumps(list(self.state.data_analyzed.keys())),
            memory_graph_encoding=self.state.memory_graph.get_encoding(),
            external_info=self.state.external_info,
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": human_message},
        ]
        self.log.info("analyzer messages: %s", messages)
        response = (
            self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.7
            )
            .choices[0]
            .message.content
        )
        self.log.info("analyzer response: %s", response)

        self.state.last_speaker = self.name
        self.state.current_round += 1
        with open("analysis_report.output.md", "w") as f:
            f.write(response)

        self.state.last_analysis = response
        self.state.last_analysis_checked = False
 
        return response
