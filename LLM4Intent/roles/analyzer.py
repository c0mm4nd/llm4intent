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
        system_message = self.system_message.format()
        messages = [
            {"role": "system", "content": system_message},
            *self.state.chat_history,
            {
                "role": "user",
                "content": f"""
Please analyze against the retrieved data.""",
            },
        ]
        self.log.debug("analyzer messages: %s", messages)
        completion = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=0.7
        )
        self.log.debug("analyzer completion: %s", completion)
        response = completion.choices[0].message.content

        # Save the analysis to the state
        self.state.chat_history.extend(
            [
                {"role": "user", "content": f"Please analyze against the retrieved data."},
                {"role": "assistant", "content": response},
            ]
        )

        self.state.last_speaker = self.name
        self.state.current_round += 1
        with open("analysis_report.output.md", "w") as f:
            f.write(response)

        self.state.last_analysis = response
        self.state.last_analysis_checked = False

        return response
