import json
import logging
from typing import Callable, Dict, List
from openai import Client
from openai.types.chat import ChatCompletionMessage
from LLM4Intent.common.utils import convert_tool, get_logger, get_prompt

class DomainExpertAnalyzer:
    def __init__(
        self,
        model: str,
        client: Client,
        known_facts: str,
        main_perspective: str,
        tools: List[Callable],
    ):
        self.name = "DomainExpertAnalyzer"
        self.model_name = model
        self.client = client
        self.main_perspective = main_perspective
        self.tools = tools
        self.facts = known_facts
        self.system_prompt = get_prompt("sub_analyzer").format(
            perspective=main_perspective
        )
        self.log = get_logger(f"{self.main_perspective} expert")
        self.tool_map = {tool.__name__: tool for tool in tools}

        # Convert tools safely with error handling
        converted_tools = []
        for tool in self.tools:
            try:
                converted_tool = convert_tool(tool)
                converted_tools.append(converted_tool)
            except ValueError as e:
                self.log.error(f"Failed to convert tool {tool.__name__}: {str(e)}")
                # Skip this tool or create a simplified version if needed
        self.converted_tools = converted_tools

    def call_tools(self, question: str, response: ChatCompletionMessage) -> list:
        tool_messages = [
            response.to_dict(),
        ]

        for tool_call in response.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            self.log.warning(f"For {question} call Tool: {tool_name} with args {tool_args}")

            tool = self.tool_map.get(tool_name)
            if tool:
                try:
                    result = tool(**tool_args)
                    tool_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result),
                        }
                    )
                except Exception as e:
                    error_message = (
                        f"Error in tool {tool_name} with args {tool_args}: {str(e)}"
                    )
                    self.log.error(error_message)
                    tool_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": error_message,
                        }
                    )
            else:
                raise ValueError(f"Tool {tool_name} not found in tool map")

        return tool_messages

    def analyze(self, previous_chat_history: list, question: str, prompt: str) -> str:
        """
        Analyze a specific sub-question using tools and LLM capabilities

        Args:
            previous_chat_history (list): The chat history so far
            question: The sub-question to analyze
            prompt: The prompt to use for the analysis

        Returns:
            str: The analysis result
        """

        chat_history = [
            *previous_chat_history,
            {
                "role": "user",
                "content": f"Known Transaction Facts: {json.dumps(self.facts)}\n\nQuestion to analyze: {question}\n\n{prompt}",
            },
        ]
        max_iterations = 10  # Prevent infinite loops
        iterations = 0

        while iterations < max_iterations:
            iterations += 1
            self.log.info(
                f"Iteration {iterations} for question: {question} ({self.main_perspective})"
            )

            messages = [
                {"role": "system", "content": self.system_prompt},
                *chat_history,
            ]

            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=self.converted_tools,
                tool_choice="auto",
                temperature=0,
            )

            response = completion.choices[0].message

            # Check if the response has tool calls that need to be processed
            if response.tool_calls:
                # Process tool calls and add results to conversation
                tool_messages = self.call_tools(question, response)
                chat_history.extend(
                    tool_messages
                )  # Skip the first item as it's the assistant's message already in conversation
            else:
                # Check if analysis is complete (when "END" appears in the response)
                if "END" in response.content:
                    # Clean up the response by removing the END marker
                    final_response = response.content.replace("END", "").strip()
                    self.log.info(f"Analysis complete after {iterations} iterations")
                    chat_history.append(
                        {
                            "role": "assistant",
                            "content": final_response,
                        }
                    )

                    self.log.info(f"Final response: {final_response}")

                    return [
                        {
                            "role": "user",
                            "content": question,
                        },
                        {
                            "role": "assistant",
                            "content": final_response,
                        },
                    ]

                # No tool calls, add response to conversation
                chat_history.append({"role": "assistant", "content": response.content})

                self.log.info(f"Response: {response.content}")

                # Ask for additional analysis if not complete
                chat_history.append(
                    {
                        "role": "user",
                        "content": "Continue analyzing this question. When you have completed the analysis, include 'END' at the end of your response.",
                    }
                )

        # If we reach max iterations without completion
        self.log.warning(
            f"Reached maximum iterations ({max_iterations}) without completing analysis"
        )

        self.log.warning(f"Final chat history: {chat_history}")

        return [
            {
                "role": "user",
                "content": question,
            },
            {
                "role": "assistant",
                "content": chat_history[-1]["content"],
            },
        ]
