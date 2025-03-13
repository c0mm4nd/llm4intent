import json
from typing import List
from openai import Client
from pydantic import BaseModel, Field
from LLM4Intent.common.state import State
from LLM4Intent.common.utils import get_logger, get_prompt


class CategoryScore(BaseModel):
    """The category score of the intent."""

    category: str = Field(description="Category of the intent.")
    score: float = Field(description="Probability of the intent in this category.")


class ScoreReport(BaseModel):
    """The category scores of the intent."""

    scores: List[CategoryScore] = Field(description="Category scores.")
    reason: str = Field(description="Reason for the scores.")


class Scorer:
    def __init__(self, model: str, state: State, client: Client):
        self.name = "scorer"
        self.model = model

        self.state = state
        self.client = client

        self.system_message = get_prompt("scorer")
        self.log = get_logger("Scorer")

    def score(self) -> ScoreReport:
        human_message = f"Please score the intent: {self.state.last_analysis}"
        system_message = self.system_message.format(
            categories=json.dumps(self.state.options),
            score_report_schema=ScoreReport.model_json_schema(),
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": human_message},
        ]
        response = (
            self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0
            )
            .choices[0]
            .message.content
        )
        report_data = json.loads(response.strip("```json\n").strip("\n```"))
        report = ScoreReport(**report_data)
        self.state.last_speaker = self.name
        with open("score_report.output.md", "w") as f:
            f.write(report.model_dump_json(indent=4))
        return report
