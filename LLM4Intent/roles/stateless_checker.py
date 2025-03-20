import json
from typing import List, Dict, Any, Optional, Mapping
from openai import Client
from pydantic import BaseModel, Field

from LLM4Intent.common.utils import get_logger, get_prompt

logger = get_logger("StatelessChecker")


class AnalysisWeight(BaseModel):
    perspective: str = Field(description="The analyzing perspective")
    weight: float = Field(
        description="Credibility weight between 0.0 and 1.0", ge=0.0, le=1.0
    )
    reasoning: str = Field(description="Reasoning for the assigned weight")


class CheckReport(BaseModel):
    weighted_analyses: List[AnalysisWeight] = Field(
        description="List of analyses with their assigned credibility weights"
    )
    identified_intent: str = Field(
        description="The most credible intent category from hierarchy of intents"
    )
    intent_path: List[str] = Field(
        description="The path to the identified intent in the hierarchy of intents"
    )
    confidence_score: float = Field(
        description="Overall confidence score between 0.0 and 1.0", ge=0.0, le=1.0
    )
    knowledge_missing: List[str] = Field(
        description="List of knowledge missing from the analysis"
    )
    summary: str = Field(description="Summary of the intent analysis and justification")


class StatelessChecker:
    def __init__(self, model: str, client: Client):
        self.name = "checker"
        self.model = model
        self.client = client
        self.system_message = get_prompt("stateless_checker")
        self.log = get_logger("Checker")
        # Load intent categories
        with open("/Users/c0mm4nd/llm4intent/intent_cat.json", "r") as f:
            self.intent_categories = json.load(f)

    def check_and_summarize(
        self, hierarchical_intents: dict, perspective_analyzer_reports: dict
    ) -> CheckReport:
        chat_history = []

        system_message = self.system_message.format(
            check_report_schema=CheckReport.model_json_schema(),
            intent_categories=json.dumps(
                self.intent_categories, indent=2, ensure_ascii=False
            ),
        )

        analysis = ""
        for perspective, report in perspective_analyzer_reports.items():
            analysis += f"Perspective: {perspective}\n{report}\n"

        # Format the analyzer history and current analysis
        analysis_content = f"""
Here is the analysis to check:
{analysis}

Analyze this content, determine credibility weights for each sub-analysis, and identify which intent category 
from the hierarchical intents below best matches the user's intent. Provide justification for your decision.

{hierarchical_intents}
"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": analysis_content},
        ]

        self.log.debug(messages)
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )

        self.log.debug(completion)
        response = completion.choices[0].message.content

        # Extract the JSON part if it's wrapped in a code block
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()

        report_data = json.loads(response)
        report = CheckReport(**report_data)

        # Save the check report to the state
        chat_history.extend(
            [
                {"role": "user", "content": analysis_content},
                {"role": "assistant", "content": response},
            ]
        )

        with open("check_report.output.md", "w") as f:
            f.write(report.model_dump_json(indent=4))

        return report
