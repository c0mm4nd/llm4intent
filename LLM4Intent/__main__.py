# %%
import os
import json
from typing import Any, Dict, List, Mapping, Optional
from dotenv import load_dotenv
from openai import Client, OpenAI
from LLM4Intent.common.state import State
from LLM4Intent.common.utils import get_logger
from LLM4Intent.roles.retriever import Retriever
from LLM4Intent.roles.analyzer import Analyzer
from LLM4Intent.roles.checker import Checker
from LLM4Intent.roles.scorer import Scorer

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 默认模型配置
DEFAULT_MODEL_NAME = "openai/gpt-4o-mini"  # 根据需要替换为实际模型，例如 "gpt-4o"
SUMMARIZING_MODEL_NAME = "gpt-4o-mini"
THINKING_MODEL_NAME = "gpt-4o-mini"
TOKEN_LIMIT = 128000  # 根据模型调整


# %%
logger = get_logger("Workflow")

# %%
def workflow(transaction_hash: str, hierarchical_intents: Mapping, options: List[str]):
    state = State(
        task=transaction_hash,
        hierarchical_intents=hierarchical_intents,
        options=options,
    )

    retriever = Retriever(
        model="grok-2-latest",
        state=state,
        client=client,
    )
    analyzer = Analyzer(
        model="grok-2-latest",
        state=state,
        client=client,
    )
    checker = Checker(
        model="grok-2-latest",
        state=state,
        client=client,
    )
    scorer = Scorer(
        model="grok-2-latest",
        state=state,
        client=client,
    )

    while True:
        logger.info(f"Last speaker: {state.last_speaker}")
        if state.last_speaker == "human":
            retriever.retrieve()
        elif state.last_speaker == "retriever":
            analyzer.analyze()
        elif state.last_speaker == "analyzer":
            report = checker.check()
            if report.approval or state.current_round > 20:
                break
        elif state.last_speaker == "checker":
            retriever.retrieve()

    scorer.score()


def start():
    with open("config.json") as f:
        config = json.load(f)

    options = config["options"]
    for transaction_hash in config["transactions"]:
        hierarchical_intents = json.load(open("intent_cat.json"))
        workflow(transaction_hash, hierarchical_intents, options)


if __name__ == "__main__":
    start()
