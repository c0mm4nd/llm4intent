import json
import logging

from openai import Client
from pydantic import BaseModel, Field
from LLM4Intent.common.utils import get_logger, get_prompt


class Plan(BaseModel):
    target: str = Field(..., description="The target of the plan")
    items: list[str] = Field(..., description="The TODO items in the plan")
    prompts: list[str] = Field(
        ..., description="The detailed prompts for better handling each TODO item"
    )


BREAKDOWN_PROMPT = """
To analyze the intent behind the Ethereum transaction {transaction_hash}, we have assembled the team with multiple analyzers.

Based on known and unknown facts, please devise a short bullet-point plan for each analyzer to follow. The plan should include the target of the analysis and the TODO items with detailed prompts for better handling each item.

Here are some TIPs to help you with the plan and prompts:
{tips}

Please output an answer in pure JSON format according to the following schema. The JSON object must be parsable as-is. DO NOT OUTPUT ANYTHING OTHER THAN JSON, AND DO NOT DEVIATE FROM THIS SCHEMA:
{plan_json_schema}
"""


class MainAnalyzer:
    def __init__(self, model: str, client: Client, perspective: str, tips: str):
        self.name = "analyzer"
        self.model = model
        self.client = client
        self.perspective = perspective
        self.tips = tips

        self.system_message = get_prompt("main_analyzer").format(perspective=self.perspective)
        self.log = get_logger("MainAnalyzer")

        self.plan = None

    def breakdown(self, transaction_hash) -> Plan:
        breakdown_prompt = BREAKDOWN_PROMPT.format(
            transaction_hash=transaction_hash,
            tips=self.tips,
            plan_json_schema=Plan.model_json_schema(),
        )

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

        self.plan = plan

        return plan

    def analyze(self, hierarchical_intents, merged_chat_history) -> str:
        chat_history = [
            {
                "role": "user",
                "content": f"Please analyze the {self.plan.target}.",
            },
            {
                "role": "assistant",
                "content": f"""Here is the plan to analyze the {self.plan.target}:
{"\n".join(f'- {item}' for item in self.plan.items)}
""",
            },
            *merged_chat_history,
        ]

        while True:
            system_message = self.system_message.format()
            messages = [
                {"role": "system", "content": system_message},
                *chat_history,
                {
                    "role": "user",
                    "content": f"""Please infer the intent behind the {self.plan.target} from the perspective of the {self.perspective}.

The intent inferred should be one of the following:
{hierarchical_intents}
                    """,
                },
            ]
            self.log.debug("analyzer messages: %s", messages)
            completion = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0
            )
            self.log.debug("analyzer completion: %s", completion)
            response = completion.choices[0].message.content

            # Save the analysis to the state
            chat_history.extend(
                [
                    {
                        "role": "user",
                        "content": f"Please analyze against the retrieved data.",
                    },
                    {"role": "assistant", "content": response},
                ]
            )

            with open("analysis_report.output.md", "w") as f:
                f.write(response)

            return response
