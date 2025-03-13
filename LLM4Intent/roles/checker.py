
import json
import logging
from typing import List
from openai import Client
from pydantic import BaseModel, Field

from LLM4Intent.common.state import DataMissing, State
from LLM4Intent.common.utils import get_logger, get_prompt


class CheckReport(BaseModel):
    """The approval status of the intent analysis."""

    approval: bool = Field(description="Approval status.")
    data_missing: List[DataMissing] = Field(description="Missing data.")
    behavior_sequence_gap: List[str] = Field(description="Gaps in behavior sequence.")
    contextual_gaps: List[str] = Field(description="Gaps in contextual analysis.")
    factual_errors: List[str] = Field(description="Factual errors.")
    logical_inconsistencies: List[str] = Field(description="Logical inconsistencies.")
    next_speaker: str = Field(description="Next speaker.")



class Checker():
    def __init__(self, model: str, state: State, client: Client):
        self.name = "checker"
        self.model = model
        self.state = state
        self.client = client
        self.system_message = get_prompt("checker")
        self.log = get_logger("Checker")

    def check(self) -> CheckReport:
        if not self.state.last_analysis:
            raise ValueError("No analysis to check.")
        
        if self.state.last_analysis_checked:
            raise ValueError("Analysis already checked.")

        human_message = f"Please check the analysis:\n\n{self.state.last_analysis}"
        system_message = self.system_message.format(
            data_analyzed=json.dumps(list(self.state.data_analyzed.keys())),
            check_report_schema=CheckReport.model_json_schema(),
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": human_message},
        ]
        self.log.info(messages)
        # response = (
        #     self.client.chat.completions.create(
        #         model=self.model, messages=messages, temperature=0,
        #         response_format=CheckReport
        #     )
        #     .choices[0]
        #     .message.content
        # )
        response = (
            self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0,
                response_format={"type": "json_object"}
            )
            .choices[0]
            .message.content
        )
        self.log.info(response)
        report_data = json.loads(response.strip("```json\n").strip("\n```"))
        report = CheckReport(**report_data)

        self.state.current_check_report = report
        self.state.last_speaker = self.name
        self.state.last_analysis_checked = True

        with open("check_report.output.md", "w") as f:
            f.write(report.model_dump_json(indent=4))

        return report
