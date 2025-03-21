import json
from typing import List, Dict, Any, Optional, Mapping
from openai import Client
from pydantic import BaseModel, Field

from LLM4Intent.common.utils import get_logger, get_prompt

logger = get_logger("StatelessChecker")


class AnalysisWeight(BaseModel):
    intent: str = Field(description="The final inferred intent category")
    logical_reasoning: str = Field(description="The logical reasoning for the intent")
    problems: List[str] = Field(
        description="List of contradictions or missing logical mistakes in the analysis"
    )
    perspective: str = Field(description="The analyzing perspective")
    weight: float = Field(
        description="Credibility weight between 0.0 and 1.0", ge=0.0, le=1.0
    )
    reasoning: str = Field(description="Reasoning for the assigned weight")


class CheckReport(BaseModel):
    weighted_analyses: List[AnalysisWeight] = Field(
        description="List of analyses with their assigned credibility weights"
    )


class StatelessChecker:
    def __init__(self, model: str, client: Client):
        self.name = "checker"
        self.model = model
        self.client = client
        self.system_message = get_prompt("stateless_checker")
        self.log = get_logger("Checker")

    def check(
        self, hierarchical_intents: dict, perspective_analyzer_reports: dict
    ) -> CheckReport:
        chat_history = []

        system_message = self.system_message.format()

        analysis = ""
        for perspective, report in perspective_analyzer_reports.items():
            analysis += f"Report on {perspective} perspective:\n{report}\n\n"

        # Format the analyzer history and current analysis
        analysis_content = """
Here are different perspective analysis reports for analyzing a same transaction:
{analysis}

Analyze this content, determine credibility weights for each domain, and identify which intent category 
from the hierarchical intents below best matches the user's intent. Provide justification for your decision.

{hierarchical_intents}

Provide a weighted assessment of intents and credibilities from each perspective in the analysis.
- Review the provided analysis carefully
- For each domain question point, assign a credibility weight (0.0-1.0) based on:
  - Evidence quality
  - Reasoning soundness
  - Consistency with blockchain behaviors
  - Presence of speculation vs. factual reasoning
  - Calculate a confidence score for each domain question point

Return your analysis in the following JSON format:

{check_report_schema}

Make sure your response is valid JSON that follows this schema exactly."""

        messages = [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": analysis_content.format(
                    analysis=analysis,
                    hierarchical_intents=hierarchical_intents,
                    check_report_schema=CheckReport.model_json_schema(),
                ),
            },
        ]

        self.log.debug(messages)
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
        )

        self.log.debug(completion)
        response = completion.choices[0].message.content

        # Extract the JSON part if it's wrapped in a code block
        if "```json" in response:
            response = response.strip("```json\n").strip("\n```")

        report = CheckReport.model_validate_json(response)

        with open("check_report.output.md", "w") as f:
            f.write(report.model_dump_json(indent=4))

        return report
