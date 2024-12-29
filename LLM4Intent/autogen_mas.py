import os
from autogen import (
    AssistantAgent,
    UserProxyAgent,
    ConversableAgent,
    register_function,
    GroupChat,
    GroupChatManager,
)
from dotenv import load_dotenv
from web3 import Web3
from web3research import Web3Research
from web3research.common import Hash

from LLM4Intent.contexts import get_transaction
from LLM4Intent.data_types import (
    TransactionWithLogsTraces,
)

load_dotenv()

def start_agents():
    # analysis_llm_config = {
    #     "config_list": [
    #         {
    #             "model": "llama-3.3-70b-versatile",
    #             "api_key": os.environ.get("GROQ_API_KEY"),
    #             "api_rate_limit": 30,
    #             "api_type": "groq",
    #         }
    #     ],
    #     "temperature": 0.9,
    # }

    # retrieve_llm_config = {
    #     "config_list": [
    #         {
    #             "model": "llama-3.1-8b-instant",
    #             "api_key": os.environ.get("GROQ_API_KEY"),
    #             "api_rate_limit": 30,
    #             "api_type": "groq",
    #         },
    #     ],
    #     "temperature": 0.1,
    # }

    retrieve_llm_config = {
        "config_list": [
            {
                "model": "gemini-2.0-flash-exp",
                "api_key": os.environ.get("GOOGLE_API_KEY"),
                "api_type": "google"
            },
        ],
        "temperature": 0.1,
    }


    analysis_llm_config = retrieve_llm_config

    w3 = Web3()
    w3r = Web3Research(api_token=os.environ.get("W3R_API_KEY"))
    eth = w3r.eth(backend=os.environ.get("W3R_BACKEND"))

    print("w3r ready")

    def _get_transaction(transaction_hash: str) -> TransactionWithLogsTraces:
        return get_transaction(eth, transaction_hash)

    test_transaction_hash = "0x43a2cb2a2a4fa683a67db6f828d2db99e1253a33a8eb1032915e50f71d85a9f0"  # 0x43a2cb2a2a4fa683a67db6f828d2db99e1253a33a8eb1032915e50f71d85a9f0 swap

    user_proxy = UserProxyAgent(
        "user_proxy",
        llm_config=retrieve_llm_config,
        human_input_mode="NEVER",
        # system_message="You interact with AI assistant."
        # system_message="You are a user proxy. You can interact with the AI assistant."
        # "Return 'TERMINATE' when the task is done."
    )
    basic_transaction_retriever = AssistantAgent(
        "basic_transaction_retriever",
        llm_config=retrieve_llm_config,
        # system_message="You retrieve transaction data."
        # system_message="You are a helpful AI assistant. "
        # "You can help retrieve transaction data with tool use. "
        # "Return 'TERMINATE' when the task is done.",
    )
    intent_analyzer = AssistantAgent(
        "intent_analyzer",
        llm_config=analysis_llm_config,
        # system_message="You analyze intent behind transaction data. "
        # system_message="You are a helpful AI assistant. "
        # "You can analyze the intent behind the transaction data. "
        # "Return 'TERMINATE' when the task is done.",
    )
    intent_checker = AssistantAgent(
        "intent_checker",
        llm_config=analysis_llm_config,
        # system_message="You analyze intent behind transaction data. "
        # system_message="You are a helpful AI assistant. "
        # "You can analyze the intent behind the transaction data. "
        # "Return 'TERMINATE' when the task is done.",
    )

    # Start the chat
    groupchat = GroupChat(
        agents=[user_proxy, basic_transaction_retriever, intent_analyzer, intent_checker],
        messages=[],
        max_round=4,
        send_introductions=True,
        # speaker_selection_method="auto",
    )
    manager = GroupChatManager(groupchat=groupchat, llm_config=retrieve_llm_config)
    register_function(
        _get_transaction,
        caller=basic_transaction_retriever,
        executor=user_proxy,
        name="get_transaction",
        description="Get the transaction details for a given transaction hash",
    )
    result = user_proxy.initiate_chat(
        manager,
        message=f"Analyze the intent behind the transction with hash {test_transaction_hash} by data from basic transaction retriever and summarize in one-word",
        max_turns=4,
        summary_method="reflection_with_llm",
    )

    print("final result:\t", result.summary)
