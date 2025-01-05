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

from LLM4Intent.tools.jsonrpc import (
    get_transaction_from_jsonrpc,
    get_transaction_receipt_from_jsonrpc,
    get_transaction_trace_from_jsonrpc,
)
from LLM4Intent.tools.jsonrpc import (
    get_address_eth_balance_at_block_number_from_json,
    get_address_ERC20_token_transfers_within_block_number_range_from_jsonrpc,
    get_address_transactions_within_block_number_range_from_jsonrpc,
    get_address_ERC20_token_balance_at_block_number_from_jsonrpc,
    # get_address_ERC721_NFT_transfers_within_block_number_range_from_jsonrpc,
    # get_address_ERC1155_NFT_single_transfers_within_block_number_range_from_jsonrpc,
    # get_address_ERC1155_NFT_batch_transfers_within_block_number_range_from_jsonrpc,
)
from LLM4Intent.tools.jsonrpc import (
    get_contract_basic_info_from_jsonrpc,
    get_contract_code_at_block_number_from_jsonrpc,
    get_contract_storage_at_block_number_from_jsonrpc,
    get_contract_ERC20_token_transfers_within_block_number_range_from_jsonrpc,
    # get_contract_ERC721_NFT_transfers_within_block_number_range_from_jsonrpc,
    # get_contract_ERC1155_NFT_single_transfers_within_block_number_range_from_jsonrpc,
    # get_address_ERC1155_NFT_batch_transfers_within_block_number_range_from_jsonrpc
)

load_dotenv()


def start_agents():
    # llm_config = {
    #     "config_list": [
    #         {
    #             "model": "gemini-2.0-flash-exp",
    #             "api_key": os.environ.get("GOOGLE_API_KEY"),
    #             "api_type": "google",
    #         },
    #     ],
    #     "temperature": 0,
    # }
    llm_config = {
        "config_list": [
            {
                "model": "gpt-4o",
                "api_key": os.environ.get("OPENAI_API_KEY"),
                "api_type": "openai",
            },
        ],
        "temperature": 0,
    }


    test_transaction_hash = "0x43a2cb2a2a4fa683a67db6f828d2db99e1253a33a8eb1032915e50f71d85a9f0"  # 0x43a2cb2a2a4fa683a67db6f828d2db99e1253a33a8eb1032915e50f71d85a9f0 swap

    user_proxy = UserProxyAgent(
        "user_proxy", llm_config=llm_config, human_input_mode="NEVER"
    )
    blockchain_data_retriever = AssistantAgent(
        "blockchain_data_retriever",
        llm_config=llm_config,
        system_message="You are a helpful AI assistant. "
        "You can help retrieve any block data with tool use. "
        "Return 'TERMINATE' when the task is done.",
    )
    intent_analyzer = AssistantAgent(
        "intent_analyzer",
        llm_config=llm_config,
        system_message="You are a helpful AI assistant. "
        "You can analyze the intent behind the transaction data. "
        "Return 'TERMINATE' when the task is done.",
    )
    context_checker = AssistantAgent(
        "context_checker",
        llm_config=llm_config,
        system_message="You are a helpful AI assistant. "
        "You must check the analyzed intent. "
        "The intent must match the background and transaction context. "
        "The intent must be clearly defined. "
        "The intent must describe the caller(from_address)'s purpose."
        "The intent must consider the source."
        "Return 'TERMINATE' when the task is done.",
    )

    # register transaction info retrieval functions
    register_function(
        get_transaction_from_jsonrpc,
        caller=blockchain_data_retriever,
        executor=user_proxy,
        name="get_transaction",
        description="get_transaction",
    )

    register_function(
        get_transaction_receipt_from_jsonrpc,
        caller=blockchain_data_retriever,
        executor=user_proxy,
        name="get_transaction_receipt",
        description="get_transaction_receipt",
    )

    register_function(
        get_transaction_trace_from_jsonrpc,
        caller=blockchain_data_retriever,
        executor=user_proxy,
        name="get_transaction_trace",
        description="get_transaction_trace",
    )

    # register address info retrieval functions
    register_function(
        get_address_eth_balance_at_block_number_from_json,
        caller=blockchain_data_retriever,
        executor=user_proxy,
        name="get_address_eth_balance_at_block_number_from_json",
        description="get_address_eth_balance_at_block_number_from_json",
    )

    register_function(
        get_address_ERC20_token_balance_at_block_number_from_jsonrpc,
        caller=blockchain_data_retriever,
        executor=user_proxy,
        name="get_address_ERC20_token_balance_at_block_number",
        description="get_address_ERC20_token_balance_at_block_number",
    )

    register_function(
        get_address_ERC20_token_transfers_within_block_number_range_from_jsonrpc,
        caller=blockchain_data_retriever,
        executor=user_proxy,
        name="get_address_ERC20_token_transfers_within_block_number_range",
        description="get_address_ERC20_token_transfers_within_block_number_range",
    )

    register_function(
        get_address_transactions_within_block_number_range_from_jsonrpc,
        caller=blockchain_data_retriever,
        executor=user_proxy,
        name="get_address_transactions_within_block_number_range",
        description="get_address_transactions_within_block_number_range",
    )

    # register contract info retrieval functions
    register_function(
        get_contract_basic_info_from_jsonrpc,
        caller=blockchain_data_retriever,
        executor=user_proxy,
        name="get_contract_basic_info",
        description="get_contract_basic_info",
    )

    register_function(
        get_contract_code_at_block_number_from_jsonrpc,
        caller=blockchain_data_retriever,
        executor=user_proxy,
        name="get_contract_code_at_block_number",
        description="get_contract_code_at_block_number",
    )

    register_function(
        get_contract_storage_at_block_number_from_jsonrpc,
        caller=blockchain_data_retriever,
        executor=user_proxy,
        name="get_contract_storage_at_block_number",
        description="get_contract_storage_at_block_number",
    )

    register_function(
        get_contract_ERC20_token_transfers_within_block_number_range_from_jsonrpc,
        caller=blockchain_data_retriever,
        executor=user_proxy,
        name="get_contract_ERC20_token_transfers_within_block_number_range",
        description="get_contract_ERC20_token_transfers_within_block_number_range",
    )

    # Start the chat
    groupchat = GroupChat(
        agents=[
            user_proxy,
            blockchain_data_retriever,
            intent_analyzer,
            context_checker,
        ],
        messages=[],
        max_round=20,
        speaker_selection_method="auto",
        select_speaker_auto_llm_config=llm_config,
        select_speaker_auto_verbose=True,
        select_speaker_prompt_template="Read the above conversation. Then select the next role from {agentlist} to play. Checker must check the intent after the analyzer speaking. Only return the role.",
    )
    manager = GroupChatManager(
        groupchat=groupchat,
        llm_config=llm_config,
        is_termination_msg=lambda x: (
            x["name"] == "context_checker" and 
            "TERMINATE" in x.get("content", "") or "terminate" in x.get("content", "")
        ),
    )
    result = user_proxy.initiate_chat(
        manager,
        message=f"Analyze the deep DeFi intent behind the transction {test_transaction_hash} with tools and summarize.",
        summary_method="reflection_with_llm",
        summary_args={"llm_config": llm_config},
    )
    print("final result:\t", result.summary)
