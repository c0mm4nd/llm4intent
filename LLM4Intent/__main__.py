# %%
import os
import json
import concurrent.futures
from typing import Any, Dict, List, Mapping, Optional, Tuple
from dotenv import load_dotenv
from openai import Client, OpenAI
import argparse

from LLM4Intent.common.utils import get_logger
from LLM4Intent.roles.main_analyzer import MetaControlAnalyzer
from LLM4Intent.roles.stateless_checker import StatelessChecker
from LLM4Intent.roles.sub_analyzer import DomainExpertAnalyzer
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
def workflow(transaction_hash: str, hierarchical_intents: Mapping):
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
        get_address_transactions_within_block_number_range,
        get_address_eth_balance_at_block_number,
        get_address_token_balance_at_block_number,
        get_address_token_transfers_within_block_number_range,
        get_contract_code_at_block_number,
        get_contract_storage_at_block_number,
        get_token_transfers_within_block_number_range,
        get_contract_creation,
        get_contract_ABI,
        get_contract_basic_info,
        get_contract_source_code,
        get_contract_code_at_block_number,
        get_function_signature,
        get_event_signature,
        get_transaction_time,
        search_webpages,
        extract_webpage_info_by_urls,
    ]

    defi_contract_analyzer = MetaControlAnalyzer(
        "grok-2-latest",
        client,
        perspective="DeFi Contract Analysis",
        tips="""
To analyze the contract, you must understand its functions and the events it emits.
You can use the following tools (not limited) to analyze the contract:
- get_contract_basic_info: to get the basic information of the contract, if the contract is a proxy, try analyzing the implementation contract
- get_contract_ABI: to get the contract's functions and events
- get_function_signature: to get the signature of a specific function
- get_event_signature: to decode the hex signature of a specific event in the logs
- get_contract_source_code: to get the source code of the contract, if available
- get_address_label: to get the label of the contract creator, token addresses etc.
- get_contract_creation: to get the creator address of the contract, maybe it has a special meaning
NEVER try decoding the raw data directly by yourself, ALWAYS use the tools provided.
""",
    )
    context_analyzer = MetaControlAnalyzer(
        "grok-2-latest",
        client,
        perspective="Transaction Contextual Information",
        tips="""
To analyze the context, you must understand the sender, receiver, and the purpose of the transaction.
You can use the following tools (not limited) to analyze the context:
- get_address_transactions_within_block_number_range: to get the transactions of an address within a block number range
- get_address_token_balance_at_block_number: to get the token balance of an address at a specific block number
- get_address_eth_balance_at_block_number: to get the ETH balance of an address at a specific block number
- get_address_token_transfers_within_block_number_range: to get the token transfers of an address within a block number range
- get_token_transfers_within_block_number_range: to get the token transfers of a contract within a block number range
NEVER try decoding the transaction data or logs directly yourself, ALWAYS use the tools provided.
""",
    )
    market_analyzer = MetaControlAnalyzer(
        "grok-2-latest",
        client,
        perspective="Market Analysis",
        tips=""""
To analyze the market situation, you must understand the market conditions and the impact on the transaction.
You can use the following tools  (not limited) to analyze the market:
- get_transaction_time: to get the time of the transaction
- search_webpages: to search for relevant webpages related to the transaction, contract, or addresses
- extract_webpage_info_by_urls: to extract information from the webpages found
NEVER try decoding the raw data directly by yourself, ALWAYS use the tools provided.
""",
    )
    abnormality_analyzer = MetaControlAnalyzer(
        "grok-2-latest",
        client,
        perspective="Abnormality Detection",
        tips="""
To detect abnormalities, you must understand the normal behavior and patterns in the transaction, trying to compare the transaction with the normal ones.
You can use the following tools (not limited) to detect abnormalities:
- get_transaction_trace: to get the trace of the transaction, checking whether it is an exploit
- get_contract_storage_at_block_number: to get the contract storage at the transaction block number and the previous block number, checking for any changes
- get_contract_code_at_block_number: to get the contract code at a specific block number, checking whether it's a specific contract for exploiting
- get_address_transactions_within_block_number_range: to get the transactions of an address within a block number range, checking the money laundering pattern
- get_address_token_transfers_within_block_number_range: to get the token transfers of an address within a block number range, checking the money laundering pattern
- get_token_transfers_within_block_number_range: to get the ERC20 token transfers(swaps) within a block number range, checking whether it's a rugpull etc.
NEVER try decoding the raw data directly by yourself, ALWAYS use the tools provided.
""",
    )

    transaction_fact = collect_fact(transaction_hash)

    main_analyzer_reports = {}

    def run_analyzer(analyzer: MetaControlAnalyzer) -> Tuple[str, str]:
        plan = analyzer.breakdown(transaction_hash)

        chat_histories = []
        for todo in plan.items:
            breakdown_question, item_prompt = todo.question, todo.prompt
            sub_analyzer = DomainExpertAnalyzer(
                "grok-2-latest",
                client,
                known_facts=transaction_fact,
                main_perspective=analyzer.perspective,
                tools=all_available_tools,
            )

            chat_histories = sub_analyzer.analyze(
                chat_histories, breakdown_question, prompt=item_prompt
            )

        analyzed_intent = analyzer.analyze(hierarchical_intents, chat_histories)
        return analyzer.perspective, analyzed_intent

    analyzers = [
        defi_contract_analyzer,
        context_analyzer,
        market_analyzer,
        abnormality_analyzer,
    ]

    # Execute analyzers in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(run_analyzer, analyzer): analyzer for analyzer in analyzers
        }
        for future in concurrent.futures.as_completed(futures):
            perspective, analyzed_intent = future.result()
            main_analyzer_reports[perspective] = analyzed_intent
    # for analyzer in analyzers:
    #     perspective, analyzed_intent = run_analyzer(analyzer)
    #     main_analyzer_reports[perspective] = analyzed_intent

    # Cross-validate findings between analyzers to detect inconsistencies
    # cross_validation = {
    #     "findings": main_analyzer_reports,
    #     "transaction_fact": transaction_fact,
    # }

    checker = StatelessChecker("grok-2-latest", client)
    check_report = checker.check(hierarchical_intents, main_analyzer_reports)

    logger.info("check_report {}".format(check_report))

    scorer = StatelessScorer("grok-2-latest", client)
    final_report = scorer.score(check_report, hierarchical_intents)

    logger.warning("Final report: {}".format(final_report))


def start():
    # read config from argparser
    parser = argparse.ArgumentParser(description="LLM4Intent")
    parser.add_argument("--config", type=str, default="config.json")
    args = parser.parse_args()

    # read config from file
    config = json.load(open(args.config))
    # read transactions from the file
    txs = config.get("txs", []) + config.get("tfs", [])
    hierarchical_intents = json.load(open("intent_cat.json"))

    for transaction_hash in txs:
        print(f"Analyzing transaction: {transaction_hash}")
        workflow(transaction_hash, hierarchical_intents)


if __name__ == "__main__":
    start()
