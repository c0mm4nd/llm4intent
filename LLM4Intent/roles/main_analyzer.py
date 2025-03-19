import json
import logging

from openai import Client
from pydantic import BaseModel, Field
from LLM4Intent.common.utils import get_logger, get_prompt

FACT_PROMPT = """
Below I will present you a request. Before we begin addressing the request, please answer the following pre-survey to the best of your ability. Keep in mind that you are Ken Jennings-level with trivia, and Mensa-level with puzzles, so there should be a deep well to draw from.

Here is the request:

{task}

Here is the pre-survey:

    1. Please list any specific facts or figures that are GIVEN in the request itself. It is possible that there are none.
    2. Please list any facts that may need to be looked up, and WHERE SPECIFICALLY they might be found. In some cases, authoritative sources are mentioned in the request itself.
    3. Please list any facts that may need to be derived (e.g., via logical deduction, simulation, or computation)
    4. Please list any facts that are recalled from memory, hunches, well-reasoned guesses, etc.

When answering this survey, keep in mind that "facts" will typically be specific names, dates, statistics, etc. Your answer should use headings:

    1. GIVEN OR VERIFIED FACTS
    2. FACTS TO LOOK UP
    3. FACTS TO DERIVE
    4. EDUCATED GUESSES

DO NOT include any other headings or sections in your response. DO NOT list next steps or plans until asked to do so.
"""

class Plan(BaseModel):
    target: str = Field(..., description="The target of the plan")
    items: list[str] = Field(..., description="The TODO items in the plan")

BREAKDOWN_PROMPT = """
To address this request we have assembled the team with multiple analyzers.

Based on known and unknown facts, please devise a short bullet-point plan for addressing the original request. 

Please output an answer in pure JSON format according to the following schema. The JSON object must be parsable as-is. DO NOT OUTPUT ANYTHING OTHER THAN JSON, AND DO NOT DEVIATE FROM THIS SCHEMA:
{plan_json_schema}
"""

class MainAnalyzer:
    def __init__(self, model: str, client: Client, aspect: str):
        self.name = "analyzer"
        self.model = model
        self.client = client
        self.aspect = aspect

        self.system_message = get_prompt("main_analyzer").format(aspect=self.aspect)
        self.log = get_logger("MainAnalyzer")

    def breakdown(self) -> Plan:
        breakdown_prompt = BREAKDOWN_PROMPT.format(plan_json_schema=Plan.model_json_schema())

        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "assistant", "content": breakdown_prompt},
        ]
        completion = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=0.7
        )
        response = completion.choices[0].message.content
        self.log.info("Breakdown response: %s", response)

        plan_data = response.strip("```json\n").strip("\n```")

        plan = Plan.model_validate_json(plan_data)
        self.log.info("Plan: %s", plan)

        return plan

    def analyze(self) -> str:
        chat_history = []

        while True:
            system_message = self.system_message.format()
            messages = [
                {"role": "system", "content": system_message},
                *chat_history,
                {
                    "role": "user",
                    "content": f"""Please analyze against the retrieved data.""",
                },
            ]
            self.log.debug("analyzer messages: %s", messages)
            completion = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.7
            )
            self.log.debug("analyzer completion: %s", completion)
            response = completion.choices[0].message.content

            # Save the analysis to the state
            chat_history.extend(
                [
                    {"role": "user", "content": f"Please analyze against the retrieved data."},
                    {"role": "assistant", "content": response},
                ]
            )

            with open("analysis_report.output.md", "w") as f:
                f.write(response)

            return response

