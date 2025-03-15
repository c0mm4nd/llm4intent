import logging
from typing import Any, Callable, Dict, List, Literal, Tuple, Union, get_type_hints
from langchain_core.utils.function_calling import convert_to_openai_tool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def get_prompt(agent_name: str) -> str:
    with open(f"LLM4Intent/prompts/{agent_name}_prompt.txt") as f:
        return f.read()


def convert_tool(tool: Callable) -> Dict[str, Any]:
    if tool is None:
        raise ValueError("Tool cannot be None")

    schema = convert_to_openai_tool(
        tool,
        # strict=True, # Not supported by Grok
    )
    return schema
