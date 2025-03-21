import json
from typing import List
from openai import Client
from pydantic import BaseModel, Field
from LLM4Intent.common.utils import get_logger, get_prompt
from LLM4Intent.roles.stateless_checker import CheckReport


class CheckEval(BaseModel):
    """The evaluation of the check reports"""

    coherence: float = Field(
        description="Coherence with known knowledge and the provided evaluation criteria in each domain check report, between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
    )
    strength: float = Field(
        description="Supporting evidence strength in each domain analysis report, between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
    )
    # Cross-validation with other analysis perspectives in the dataset


class FinalReport(BaseModel):
    check_evaluations: List[CheckEval] = Field(
        description="The evaluation of the analysis check reports in each domain"
    )
    final_intent: str = Field(
        description="The most credible and most possible intent category from hierarchy of intents"
    )
    intent_path: List[str] = Field(
        description="The path to the identified intent in the hierarchy of intents"
    )
    confidence_score: float = Field(
        description="Overall confidence score between 0.0 and 1.0", ge=0.0, le=1.0
    )
    summary: str = Field(description="Summary of the intent analysis and justification")
    improvement: List[str] = Field(
        description="List of improvements needed for a better analysis and more accurate intent identification"
    )


class StatelessScorer:
    def __init__(self, model: str, client: Client):
        self.name = "FinalEvaluator"
        self.model = model

        self.client = client

        self.system_message = get_prompt("stateless_scorer")
        self.log = get_logger("FinalEvaluator")

    def score(
        self, check_report: CheckReport, hierarchical_intents: dict
    ) -> FinalReport:
        human_message = """
Evaluate step by step as below:
1. Evaluate the logical consistency of the reasoning chain in the analysis result. 
2. Identify any contradictions or missing logical links. 
3. Explain the reasoning behind any detected inconsistencies. 
4. Infer the overall intent from the provided analysis reports and credibilities. 
5. Provide an explanation for the classifications. 

Wrap the output in `json` tags with the structure of the FinalReport.

{final_report_schema}"""

        system_message = self.system_message.format(
            categories=json.dumps(hierarchical_intents),
        )
        messages = [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": "check each perspective analysis",
            },
            {
                "role": "assistant",
                "content": "The check report as below:\n\n{check_report}".format(
                    check_report=check_report,
                ),
            },
            {
                "role": "user",
                "content": human_message.format(
                    final_report_schema=FinalReport.model_json_schema()
                ).strip(),
            },
        ]
        self.log.debug(messages)
        response = (
            self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0
            )
            .choices[0]
            .message.content
        )
        self.log.debug(response)
        response = response.strip("```json\n").strip("\n```")
        report = FinalReport.model_validate_json(response)

        with open("score_report.output.md", "w") as f:
            f.write(report.model_dump_json(indent=4))

        return report
