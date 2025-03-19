# %%
import os
import json
from typing import Any, Dict, List, Mapping, Optional
from dotenv import load_dotenv
from openai import Client, OpenAI

from LLM4Intent.common.utils import get_logger
from LLM4Intent.roles.main_analyzer import MainAnalyzer
from LLM4Intent.roles.stateless_checker import StatelessChecker
from LLM4Intent.roles.sub_analyzer import SubAnalyzer
from LLM4Intent.roles.stateless_scorer import StatelessScorer

from LLM4Intent.tools.annotated import *

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


def collect_fact(transaction_hash: str):
    transaction = get_transaction_from_jsonrpc(transaction_hash)
    receipt = get_transaction_receipt_from_jsonrpc(transaction_hash)
    to_address = transaction["to"]
    from_address = transaction["from"]
    fact = {
        **transaction,
        **receipt,
        "from_label": get_address_label(from_address),
        "to_label": get_address_label(to_address),
    }

    return fact


# %%
def workflow(transaction_hash: str, hierarchical_intents: Mapping, options: List[str]):
    fake_chat_history = [
        {
            "role": "user",
            "content": f"Please analyze the transaction {transaction_hash}.",
        },
        {
            "role": "assistant",
            "content": """
Sure,
To analyze the transaction, I would break down the analysis into several parts:
1. analyze the contract definition and its functions, finding the intent behind each function
2. analyze the context of the transaction, finding the intent behind the sender and receiver
3. analyze the market situation, finding the intent behind the transaction"
""",
        },
    ]

    all_available_tools = [
        get_transaction,
        get_transaction_receipt,
        get_transaction_trace,
        get_address_label,
        get_address_eth_balance_at_block_number,
        get_address_token_balance_at_block_number,
        get_address_token_transfers_within_block_number_range,
        get_contract_code_at_block_number,
        get_contract_storage_at_block_number,
        get_contract_token_transfers_within_block_number_range,
        get_contract_creation,
        get_contract_ABI,
        get_contract_basic_info,
        get_contract_source_code,
        get_contract_code_at_block_number,
        get_function_signature,
        get_event_signature,
        search_webpages,
        extract_webpage_info_by_urls,
    ]

    defi_contract_analyzer = MainAnalyzer(
        "grok-2-latest", client, aspect="DeFi Contract Analysis"
    )
    context_analyzer = MainAnalyzer(
        "grok-2-latest", client, aspect="Transaction Contextual Information"
    )
    market_analyzer = MainAnalyzer("grok-2-latest", client, aspect="Market Analysis")

    transaction_fact = collect_fact(transaction_hash)

    main_analyzer_reports = {}

    for analyzer in [defi_contract_analyzer, context_analyzer, market_analyzer]:
        plan = analyzer.breakdown(transaction_hash)
        chat_histories = []
        for breakdown_question in plan.items:
            sub_analyzer = SubAnalyzer(
                "grok-2-latest",
                client,
                facts=transaction_fact,
                main_aspect=analyzer.aspect,
                tools=all_available_tools,
            )

            chat_histories = sub_analyzer.analyze(chat_histories, breakdown_question, item_prompt=breakdown_question)

        analyzed_intent = analyzer.analyze(chat_histories)
        main_analyzer_reports[analyzer.aspect] = analyzed_intent

    checker = StatelessChecker("grok-2-latest", client)
    final_report = checker.check_and_summarize(hierarchical_intents, main_analyzer_reports)

    print(final_report)

    # scorer = StatelessScorer("grok-2-latest", client)
    # score = scorer.score(final_report, options)


def start():
    with open("config.json") as f:
        config = json.load(f)

    options = config["options"]
    for transaction_hash in config["transactions"]:
        hierarchical_intents = json.load(open("intent_cat.json"))
        workflow(transaction_hash, hierarchical_intents, options)


if __name__ == "__main__":
    start()
