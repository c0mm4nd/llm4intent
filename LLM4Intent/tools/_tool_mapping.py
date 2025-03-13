from langchain_core.tools import tool
from typing import Dict, List
from dotenv import load_dotenv
from LLM4Intent.tools.jsonrpc import (
    get_transaction_from_jsonrpc as _get_transaction_from_jsonrpc,
    get_transaction_receipt_without_logs_from_jsonrpc as _get_transaction_receipt_without_logs_from_jsonrpc,
    get_transaction_receipt_logs_length_from_jsonrpc as _get_transaction_receipt_logs_length_from_jsonrpc,
    get_transaction_receipt_logs_with_index_range_from_jsonrpc as _get_transaction_receipt_logs_with_index_range_from_jsonrpc,
    get_transaction_trace_length_from_jsonrpc as _get_transaction_trace_length_from_jsonrpc,
    get_transaction_trace_with_index_range_from_jsonrpc as _get_transaction_trace_with_index_range_from_jsonrpc,
    get_address_eth_balance_at_block_number_from_json as _get_address_eth_balance_at_block_number_from_json,
    get_address_ERC20_token_transfers_within_block_number_range_from_jsonrpc as _get_address_ERC20_token_transfers_within_block_number_range_from_json,
    get_address_transactions_within_block_number_range_from_jsonrpc as _get_address_transactions_within_block_number_range_from_jsonrpc,
    get_address_ERC20_token_balance_at_block_number_from_jsonrpc as _get_address_ERC20_token_balance_at_block_number_from_jsonrpc,
    # get_address_ERC721_NFT_transfers_within_block_number_range_from_jsonrpc,
    # get_address_ERC1155_NFT_single_transfers_within_block_number_range_from_jsonrpc,
    # get_address_ERC1155_NFT_batch_transfers_within_block_number_range_from_jsonrpc,
    get_contract_basic_info_from_jsonrpc as _get_contract_basic_info_from_jsonrpc,
    get_contract_code_at_block_number_from_jsonrpc as _get_contract_code_at_block_number_from_jsonrpc,
    get_contract_storage_at_block_number_from_jsonrpc as _get_contract_storage_at_block_number_from_jsonrpc,
    get_contract_ERC20_token_transfers_within_block_number_range_from_jsonrpc as _get_contract_ERC20_token_transfers,
    # get_contract_ERC721_NFT_transfers_within_block_number_range_from_jsonrpc,
    # get_contract_ERC1155_NFT_single_transfers_within_block_number_range_from_jsonrpc,
    # get_address_ERC1155_NFT_batch_transfers_within_block_number_range_from_jsonrpc
)

from LLM4Intent.tools.etherscan import (
    get_verified_contract_abi_from_etherscan as _get_verified_contract_abi_from_etherscan,
    get_verified_contract_source_code_from_etherscan as _get_verified_contract_source_code_from_etherscan,
    get_contract_creation_from_etherscan as _get_contract_creation_from_etherscan,
)


# start: added by Command 0125
load_dotenv()
# end


"""-------------jsonrpc-------------"""


def get_transaction_from_jsonrpc(transaction_hash: str) -> Dict:
    """Retrieves transaction information from a JSON-RPC endpoint

    Args:
        transaction_hash: The hash of the transaction to retrieve

    Returns:
        Dict: Transaction information
    """
    return _get_transaction_from_jsonrpc(transaction_hash)


def get_transaction_receipt_without_logs_from_jsonrpc(transaction_hash: str) -> Dict:
    """Retrieves transaction receipt information **without** event logs from a JSON-RPC endpoint

    Args:
        transaction_hash: The hash of the transaction to retrieve receipt for

    Returns:
        Dict: Transaction receipt information
    """
    return _get_transaction_receipt_without_logs_from_jsonrpc(transaction_hash)


def get_transaction_receipt_logs_length_from_jsonrpc(transaction_hash: str) -> int:
    """Retrieves transaction receipt logs length from a JSON-RPC endpoint

    Args:
        transaction_hash: The hash of the transaction to retrieve logs length for

    Returns:
        int: Transaction receipt logs length
    """
    return _get_transaction_receipt_logs_length_from_jsonrpc(transaction_hash)


def get_transaction_receipt_logs_with_index_range_from_jsonrpc(
    transaction_hash: str, from_index: int, to_index: int
) -> Dict:
    """Retrieves transaction receipt logs within an index range from a JSON-RPC endpoint

    Args:
        transaction_hash: The hash of the transaction to retrieve logs for
        from_index: Starting index
        to_index: Ending index, at most 50 logs can be retrieved at once, i.e. to_index <= from_index + 50

    Returns:
        Dict: Transaction receipt logs
    """
    if to_index > from_index + 50:
        raise ValueError("to_index must not exceed from_index + 50")

    return _get_transaction_receipt_logs_with_index_range_from_jsonrpc(
        transaction_hash, from_index, to_index
    )


#
# def get_transaction_trace_from_jsonrpc(transaction_hash: str) -> Dict:
#     """Retrieves transaction trace information from a JSON-RPC endpoint

#     Args:
#         transaction_hash: The hash of the transaction to retrieve trace for

#     Returns:
#         Dict: Transaction trace information
#     """
#     return _get_transaction_trace_from_jsonrpc(transaction_hash)


def get_transaction_trace_length_from_jsonrpc(transaction_hash: str) -> int:
    """Retrieves transaction trace length from a JSON-RPC endpoint

    Args:
        transaction_hash: The hash of the transaction to retrieve trace length for

    Returns:
        int: Transaction trace length
    """
    return _get_transaction_trace_length_from_jsonrpc(transaction_hash)


def get_transaction_trace_with_index_range_from_jsonrpc(
    transaction_hash: str, from_index: int, to_index: int
) -> Dict:
    """Retrieves transaction trace information within an index range from a JSON-RPC endpoint

    Args:
        transaction_hash: The hash of the transaction to retrieve trace for
        from_index: Starting index
        to_index: Ending index, at most 50 traces can be retrieved at once, i.e. to_index <= from_index + 50

    Returns:
        Dict: Transaction trace information
    """
    if to_index > from_index + 50:
        raise ValueError("to_index must not exceed from_index + 50")

    return _get_transaction_trace_with_index_range_from_jsonrpc(
        transaction_hash, from_index, to_index
    )


def get_address_eth_balance_at_block_number_from_json(
    address: str, block_number: int
) -> str:
    """Retrieves ETH balance for an address at a specific block number

    Args:
        address: The Ethereum address to check balance for
        block_number: The block number to check balance at

    Returns:
        str: ETH balance in wei
    """
    return _get_address_eth_balance_at_block_number_from_json(address, block_number)


def get_address_ERC20_token_transfers_within_block_number_range(
    address: str, from_block: int, to_block: int
) -> List[Dict]:
    """Retrieves ERC20 token transfers for an address within a block number range

    Args:
        address: The address to get transfers for
        from_block: Starting block number
        to_block: Ending block number, at most 1000 blocks can be queried at once, i.e. to_block <= from_block + 1000

    Returns:
        List[Dict]: List of token transfer events
    """
    return _get_address_ERC20_token_transfers_within_block_number_range_from_json(
        address, from_block, to_block
    )


def get_address_transactions_within_block_number_range_from_jsonrpc(
    address: str, from_block: int, to_block: int
) -> List[Dict]:
    """Retrieves transactions for an address within a block number range

    Args:
        address: The address to get transactions for
        from_block: Starting block number
        to_block: Ending block number, at most 1000 blocks can be queried at once, i.e. to_block <= from_block + 1000

    Returns:
        List[Dict]: List of transactions
    """
    return _get_address_transactions_within_block_number_range_from_jsonrpc(
        address, from_block, to_block
    )


def get_address_ERC20_token_balance_at_block_number_from_jsonrpc(
    token_address: str, address: str, block_number: int
) -> str:
    """Retrieves ERC20 token balance for an address at a specific block number

    Args:
        token_address: The address of the ERC20 token contract
        address: The address to check balance for
        block_number: The block number to check balance at

    Returns:
        str: Token balance
    """
    return _get_address_ERC20_token_balance_at_block_number_from_jsonrpc(
        token_address, address, block_number
    )


def get_contract_basic_info_from_jsonrpc(contract_address: str) -> Dict:
    """Retrieves basic information about a smart contract

    Args:
        contract_address: The address of the smart contract

    Returns:
        Dict: Contract information
    """
    print(f"Calling get_contract_basic_info_from_jsonrpc with input:")
    print(f"contract_address: {contract_address}")

    try:
        result = _get_contract_basic_info_from_jsonrpc(contract_address)
        print(f"Result: {result}")
        # if result.get("name") == "Not available":
        #     raise ValueError("Contract does not support ERC20 standard")
        return result
    except Exception as e:
        error_result = {"error": str(e)}
        print(f"Error occurred: {error_result}")
        return error_result


def get_contract_code_at_block_number_from_jsonrpc(
    contract_address: str, block_number: int
) -> str:
    """Retrieves contract bytecode at a specific block number

    Args:
        contract_address: The address of the smart contract
        block_number: The block number to get code at

    Returns:
        str: Contract bytecode
    """
    return _get_contract_code_at_block_number_from_jsonrpc(
        contract_address, block_number
    )


def get_contract_storage_at_block_number_from_jsonrpc(
    contract_address: str, storage_slot: str, block_number: int
) -> str:
    """Retrieves contract storage data at a specific block number

    Args:
        contract_address: The address of the smart contract
        storage_slot: The storage slot to read
        block_number: The block number to get storage at

    Returns:
        str: Storage data
    """
    return _get_contract_storage_at_block_number_from_jsonrpc(
        contract_address, storage_slot, block_number
    )


def get_contract_ERC20_token_transfers(
    contract_address: str, from_block: int, to_block: int
) -> List[Dict]:
    """Retrieves ERC20 token transfers for a contract within a block number range

    Args:
        contract_address: The address of the ERC20 token contract
        from_block: Starting block number
        to_block: Ending block number, at most 1000 blocks can be queried at once, i.e. to_block <= from_block + 1000

    Returns:
        List[Dict]: List of token transfer events
    """
    return _get_contract_ERC20_token_transfers(contract_address, from_block, to_block)


"""-------------etherscan-------------"""


def get_contract_creation_from_etherscan(contract_address: str) -> dict:
    """Retrieves contract creation information from Etherscan

    Args:
        contract_address: The Ethereum contract address to get creation info for

    Returns:
        dict: Contract creation information including creator address and transaction details
    """
    return _get_contract_creation_from_etherscan(contract_address)


def get_verified_contract_source_code_from_etherscan(contract_address: str) -> dict:
    """Retrieves verified contract source code from Etherscan

    Args:
        contract_address: The Ethereum contract address to get source code for

    Returns:
        dict: Contract source code and related metadata
    """
    return _get_verified_contract_source_code_from_etherscan(contract_address)


def get_verified_contract_abi_from_etherscan(contract_address: str) -> dict:
    """Retrieves verified contract ABI from Etherscan

    Args:
        contract_address: The Ethereum contract address to get ABI for

    Returns:
        dict: Contract ABI in JSON format
    """
    return _get_verified_contract_abi_from_etherscan(contract_address)


"""-------------database-------------"""


def get_function_signatures_from_signature_database(hex_signature: str) -> str:
    """Retrieves function signature text from signature databases using a hex signature

    Args:
        hex_signature: The hex signature of the function to look up

    Returns:
        str: The text signature of the function if found, None otherwise
    """
    return _get_function_signatures_from_signature_database(hex_signature)


def get_event_signatures_from_signature_database(hex_signature: str) -> str:
    """Retrieves event signature text from signature databases using a hex signature

    Args:
        hex_signature: The hex signature of the event to look up

    Returns:
        str: The text signature of the event if found, None otherwise
    """
    return _get_event_signatures_from_signature_database(hex_signature)


tools_mapping = {
    "get_transaction_from_jsonrpc": get_transaction_from_jsonrpc,
    "get_transaction_receipt_without_logs_from_jsonrpc": get_transaction_receipt_without_logs_from_jsonrpc,
    "get_transaction_receipt_logs_length_from_jsonrpc": get_transaction_receipt_logs_length_from_jsonrpc,
    "get_transaction_receipt_logs_with_index_range_from_jsonrpc": get_transaction_receipt_logs_with_index_range_from_jsonrpc,
    "get_transaction_trace_length_from_jsonrpc": get_transaction_trace_length_from_jsonrpc,
    "get_transaction_trace_with_index_range_from_jsonrpc": get_transaction_trace_with_index_range_from_jsonrpc,
    "get_address_eth_balance_at_block_number_from_json": get_address_eth_balance_at_block_number_from_json,
    "get_address_ERC20_token_transfers_within_block_number_range": get_address_ERC20_token_transfers_within_block_number_range,
    "get_address_transactions_within_block_number_range_from_jsonrpc": get_address_transactions_within_block_number_range_from_jsonrpc,
    "get_address_ERC20_token_balance_at_block_number_from_jsonrpc": get_address_ERC20_token_balance_at_block_number_from_jsonrpc,
    "get_contract_basic_info_from_jsonrpc": get_contract_basic_info_from_jsonrpc,
    "get_contract_code_at_block_number_from_jsonrpc": get_contract_code_at_block_number_from_jsonrpc,
    "get_contract_storage_at_block_number_from_jsonrpc": get_contract_storage_at_block_number_from_jsonrpc,
    "get_contract_ERC20_token_transfers": get_contract_ERC20_token_transfers,
    "get_contract_creation_from_etherscan": get_contract_creation_from_etherscan,
    "get_verified_contract_source_code_from_etherscan": get_verified_contract_source_code_from_etherscan,
    "get_verified_contract_abi_from_etherscan": get_verified_contract_abi_from_etherscan,
    "get_function_signatures_from_signature_database": get_function_signatures_from_signature_database,
    "get_event_signatures_from_signature_database": get_event_signatures_from_signature_database,
}

# except the trace-related functions
_public_tool_mapping = tools_mapping.copy()
_public_tool_mapping.pop("get_transaction_trace_length_from_jsonrpc")
_public_tool_mapping.pop("get_transaction_trace_with_index_range_from_jsonrpc")
public_tool_mapping = _public_tool_mapping
