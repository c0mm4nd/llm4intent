import string
from typing import Any, Dict, List, TypedDict, Optional
import requests
import json
from web3 import Web3, HTTPProvider
from web3.types import (
    TxData,
    TxReceipt,
    FilterTrace,
    LogReceipt,
    TxParams,
    BlockIdentifier,
)

w3 = Web3(HTTPProvider("http://172.28.1.2:8545"))
# w3 = Web3(HTTPProvider("https://rpc.ankr.com/eth"))


# 用于安全地调用智能合约并转换返回值
def _try_w3_call_fetch_str(
    transaction: TxParams,
    block_identifier: Optional[BlockIdentifier] = None,
) -> str:
    try:
        utf8 = w3.eth.call(transaction=transaction, block_identifier=block_identifier)
        return "".join(
            filter(lambda x: x in string.printable, Web3.to_text(utf8))
        ).strip()
    except Exception as e:
        print("failed to fetch str", e)
        return None


def _try_w3_call_fetch_int(
    transaction: TxParams,
    block_identifier: Optional[BlockIdentifier] = None,
) -> int:
    try:
        raw_bigint = w3.eth.call(
            transaction=transaction, block_identifier=block_identifier
        )
        return Web3.to_int(raw_bigint)
    except Exception as e:
        print("failed to fetch int", e)
        return None


def _try_w3_call_fetch_address(
    transaction: TxParams,
    block_identifier: Optional[BlockIdentifier] = None,
) -> str:
    try:
        raw_address = w3.eth.call(
            transaction=transaction, block_identifier=block_identifier
        )
        raw_address = raw_address[-20:]
        return Web3.to_checksum_address(raw_address)
    except Exception as e:
        print("failed to fetch address", e)
        return None


####################### TRANSACTION INFO #######################


def get_transaction_from_jsonrpc(tx_hash: str) -> dict:
    """
    Get raw transaction details from ethereum node's JSON-RPC API

    Args:
        tx_hash (str): transaction hash

    Returns:
        dict: transaction details
    """
    return json.loads(Web3.to_json(w3.eth.get_transaction(tx_hash)))


def get_transaction_receipt_without_logs_from_jsonrpc(tx_hash: str) -> dict:
    """
    Get transaction receipt **without logs** from ethereum node's JSON-RPC API

    Args:
        tx_hash (str): transaction hash

    Returns:
        dict: transaction receipt without logs
    """
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    receipt = dict(receipt)
    del receipt["logs"]
    return json.loads(Web3.to_json(receipt))


def get_transaction_receipt_logs_length_from_jsonrpc(tx_hash: str) -> dict:
    """
    Get transaction receipt **without logs** from ethereum node's JSON-RPC API

    Args:
        tx_hash (str): transaction hash

    Returns:
        str: transaction receipt logs length in JSON format string
    """
    return json.loads(
        Web3.to_json(len(w3.eth.get_transaction_receipt(tx_hash)["logs"]))
    )


def get_transaction_receipt_logs_with_index_range_from_jsonrpc(
    tx_hash: str, from_index: int, to_index: int
) -> dict:
    """
    Get transaction receipt logs with index range from ethereum node's JSON-RPC API

    Args:
        tx_hash (str): transaction hash
        from_index (int): starting index
        to_index (int): ending index

    Returns:
        str: transaction receipt logs in JSON format string
    """
    return json.loads(
        Web3.to_json(
            w3.eth.get_transaction_receipt(tx_hash)["logs"][from_index:to_index]
        )
    )


# 交易追踪信息
def get_transaction_trace_length_from_jsonrpc(tx_hash: str) -> dict:
    return json.loads(Web3.to_json(len(w3.tracing.trace_transaction(tx_hash))))


def get_transaction_trace_with_index_range_from_jsonrpc(
    tx_hash: str, from_index: int, to_index: int
) -> dict:
    return json.loads(
        Web3.to_json(w3.tracing.trace_transaction(tx_hash)[from_index:to_index])
    )


####################### ADDRESS INFO #######################


# 查询 ETH 余额
def get_address_eth_balance_at_block_number_from_json(
    address: str, block_number: int
) -> int:
    address = Web3.to_checksum_address(address)
    return json.loads(Web3.to_json(w3.eth.get_balance(address, block_number)))


# 查询地址交易历史
def get_address_transactions_within_block_number_range_from_jsonrpc(
    address: str, from_block_number: int, to_block_number: int
) -> List[TxData]:
    address = Web3.to_checksum_address(address)
    txs = []
    for block_number in range(from_block_number, to_block_number + 1):
        for tx_hash in w3.eth.get_block(block_number)["transactions"]:
            tx = w3.eth.get_transaction(tx_hash)
            if tx["from"] == address or tx["to"] == address:
                txs.append(tx)

    return json.loads(Web3.to_json(txs))


# 查询 ERC20 代币余额和转账历史
def get_address_ERC20_token_balance_at_block_number_from_jsonrpc(
    address: str, contract_address: str, block_number: int
) -> int:
    address = Web3.to_checksum_address(address)
    return json.loads(
        Web3.to_json(
            w3.eth.call(
                {
                    "to": contract_address,
                    "data": Web3.keccak(text="balanceOf(address)").hex()[:10]
                    + "0" * 24
                    + Web3.to_bytes(hexstr=address).hex(),
                },
                block_number,
            )
        )
    )


def get_address_ERC20_token_transfers_within_block_number_range_from_jsonrpc(
    address: str, from_block_number: int, to_block_number: int
) -> List[LogReceipt]:
    address = Web3.to_checksum_address(address)

    return json.loads(
        Web3.to_json(
            w3.eth.get_logs(
                {
                    "fromBlock": from_block_number,
                    "toBlock": to_block_number,
                    "topics": [
                        Web3.keccak(text="Transfer(address,address,uint256)").hex(),
                        "0x" + "0" * 24 + Web3.to_bytes(hexstr=address).hex(),
                        # None,
                    ],
                }
            )
        )
    )


# 查询 ERC721 (NFT) 转账历史
def get_address_ERC721_NFT_transfers_within_block_number_range_from_jsonrpc(
    address: str, from_block_number: int, to_block_number: int
) -> List[LogReceipt]:
    address = Web3.to_checksum_address(address)

    return json.loads(
        Web3.to_json(
            w3.eth.get_logs(
                {
                    "fromBlock": from_block_number,
                    "toBlock": to_block_number,
                    "topics": [
                        Web3.keccak(text="Transfer(address,address,uint256)").hex(),
                        "0x" + "0" * 24 + Web3.to_bytes(hexstr=address).hex(),
                        None,
                    ],
                }
            )
        )
    )


# 查询 ERC1155 (多代币标准) 转账历史
def get_address_ERC1155_NFT_single_transfers_within_block_number_range_from_jsonrpc(
    address: str, from_block_number: int, to_block_number: int
) -> List[FilterTrace]:
    address = Web3.to_checksum_address
    return json.loads(
        Web3.to_json(
            w3.eth.get_logs(
                {
                    "fromBlock": from_block_number,
                    "toBlock": to_block_number,
                    "topics": [
                        Web3.keccak(
                            text="TransferSingle(address,address,address,uint256,uint256)"
                        ).hex(),
                        "0x" + "0" * 24 + Web3.to_bytes(hexstr=address).hex(),
                        None,
                        None,
                    ],
                }
            )
        )
    )


#
def get_address_ERC1155_NFT_batch_transfers_within_block_number_range_from_jsonrpc(
    address: str, from_block_number: int, to_block_number: int
) -> List[FilterTrace]:
    address = Web3.to_checksum_address(address)
    return Web3.to_json(
        w3.eth.get_logs(
            {
                "fromBlock": from_block_number,
                "toBlock": to_block_number,
                "topics": [
                    w3.keccak(
                        text="TransferBatch(address,address,address,uint256[],uint256[])"
                    ),
                    w3.to_bytes(address, "address").hex(),
                    None,
                    None,
                ],
            }
        )
    )


####################### CONTRACT INFO #######################


# 获取合约代码
def get_contract_code_at_block_number_from_jsonrpc(
    contract_address: str, block_number: int
) -> str:
    contract_address = Web3.to_checksum_address(contract_address)
    return w3.eth.get_code(contract_address, block_identifier=block_number).hex()


# 获取合约存储数据
def get_contract_storage_at_block_number_from_jsonrpc(
    contract_address: str, position: int, block_number: int
) -> str:
    contract_address = Web3.to_checksum_address(contract_address)

    return w3.eth.get_storage_at(contract_address, position, block_number).hex()


# 查询合约事件日志
def get_contract_events_within_block_number_range_from_jsonrpc(
    contract_address: str, from_block_number: int, to_block_number: int
) -> list:
    contract_address = Web3.to_checksum_address(contract_address)

    return json.loads(Web3.to_json(
        w3.eth.get_logs(
            {
                "fromBlock": from_block_number,
                "toBlock": to_block_number,
                "address": contract_address,
            }
        )
    ))


class AddressType:
    EOA = "EOA"
    CA = "CA"


def get_address_type_from_jsonrpc(address: str) -> str:
    address = Web3.to_checksum_address(address)
    code = w3.eth.get_code(address)
    return AddressType.EOA if code == b"" else AddressType.CA


# 查询各类代币标准(ERC20/721/1155)的转账事件
def get_contract_ERC20_token_transfers_within_block_number_range_from_jsonrpc(
    contract_address: str, from_block_number: int, to_block_number: int
) -> list:
    contract_address = Web3.to_checksum_address(contract_address)

    return json.loads(Web3.to_json(
        w3.eth.get_logs(
            {
                "fromBlock": from_block_number,
                "toBlock": to_block_number,
                "address": contract_address,
                "topics": [
                    w3.keccak(text="Transfer(address,address,uint256)"),
                    None,
                    None,
                ],
            }
        )
    ))


def get_contract_ERC721_NFT_transfers_within_block_number_range_from_jsonrpc(
    contract_address: str, from_block_number: int, to_block_number: int
) -> list:
    contract_address = Web3.to_checksum_address(contract_address)
    return json.loads(Web3.to_json(
        w3.eth.get_logs(
            {
                "fromBlock": from_block_number,
                "toBlock": to_block_number,
                "address": contract_address,
                "topics": [
                    w3.keccak(text="Transfer(address,address,uint256)"),
                    None,
                    None,
                ],
            }
        )
    ))


def get_contract_ERC1155_NFT_single_transfers_within_block_number_range_from_jsonrpc(
    contract_address: str, from_block_number: int, to_block_number: int
) -> list:
    contract_address = Web3.to_checksum_address(contract_address)

    return json.loads(w3.eth.get_logs(
        {
            "fromBlock": from_block_number,
            "toBlock": to_block_number,
            "address": contract_address,
            "topics": [
                w3.keccak(
                    text="TransferSingle(address,address,address,uint256,uint256)"
                ),
                None,
                None,
                None,
            ],
        }
    ))


def get_contract_ERC1155_NFT_batch_transfers_within_block_number_range_from_jsonrpc(
    contract_address: str, from_block_number: int, to_block_number: int
) -> list:
    contract_address = Web3.to_checksum_address(contract_address)

    return json.loads(w3.eth.get_logs(
        {
            "fromBlock": from_block_number,
            "toBlock": to_block_number,
            "address": contract_address,
            "topics": [
                w3.keccak(
                    text="TransferBatch(address,address,address,uint256[],uint256[])"
                ),
                None,
                None,
                None,
            ],
        }
    ))


class ContractBasicProperties(TypedDict):
    name: str
    symbol: str
    total_supply: int
    decimals: int
    owner: str
    may_self_destructed: bool


def get_contract_basic_info_from_jsonrpc(
    contract_address: str,
) -> ContractBasicProperties:
    contract_address = Web3.to_checksum_address(contract_address)

    return ContractBasicProperties(
        name=_try_w3_call_fetch_str(
            {
                "to": contract_address,
                "data": w3.keccak(text="name()").hex()[:10],
            }
        )
        or "Not available",
        symbol=_try_w3_call_fetch_str(
            {
                "to": contract_address,
                "data": w3.keccak(text="symbol()").hex()[:10],
            }
        )
        or "Not available",
        total_supply=_try_w3_call_fetch_int(
            {
                "to": contract_address,
                "data": w3.keccak(text="totalSupply()").hex()[:10],
            }
        )
        or "Not available",
        decimals=_try_w3_call_fetch_int(
            {
                "to": contract_address,
                "data": w3.keccak(text="decimals()").hex()[:10],
            }
        )
        or "Not available",
        owner=_try_w3_call_fetch_address(
            {
                "to": contract_address,
                "data": w3.keccak(text="owner()").hex()[:10],
            }
        )
        or "Not available",
        may_self_destructed=w3.eth.get_code(contract_address) == b"",
    )
