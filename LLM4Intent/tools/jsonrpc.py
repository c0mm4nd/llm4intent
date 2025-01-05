import pytest
from typing import List, TypedDict, Optional
from web3 import Web3, HTTPProvider
from web3.types import (
    TxData,
    TxReceipt,
    FilterTrace,
    LogReceipt,
    TxParams,
    BlockIdentifier,
)

w3 = Web3(HTTPProvider("http://localhost:8545"))


# 用于安全地调用智能合约并转换返回值
def _try_w3_call_fetch_str(
    transaction: TxParams,
    block_identifier: Optional[BlockIdentifier] = None,
) -> str:
    try:
        utf8 = w3.eth.call(transaction=transaction, block_identifier=block_identifier)
        return Web3.to_text(utf8)
    except Exception as e:
        print(e)
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
        print(e)
        return None


####################### TRANSACTION INFO #######################


def get_transaction_from_jsonrpc(tx_hash: str) -> str:
    '''
    Get raw transaction details from ethereum node's JSON-RPC API

    Args:
        tx_hash (str): transaction hash
    
    Returns:
        str: raw transaction details in JSON format string
    '''
    return Web3.to_json(w3.eth.get_transaction(tx_hash))


def get_transaction_receipt_from_jsonrpc(tx_hash: str) -> str:
    '''
    Get transaction receipt from ethereum node's JSON-RPC API

    Args:
        tx_hash (str): transaction hash
    
    Returns:
        str: transaction receipt in JSON format string
    '''
    return Web3.to_json(w3.eth.get_transaction_receipt(tx_hash))


# 交易追踪信息
def get_transaction_trace_from_jsonrpc(tx_hash: str) -> str:
    return Web3.to_json(w3.tracing.trace_transaction(tx_hash))


####################### ADDRESS INFO #######################


# 查询 ETH 余额
def get_address_eth_balance_at_block_number_from_json(
    address: str, block_number: int
) -> int:
    return Web3.to_json(w3.eth.get_balance(address, block_number))


# 查询地址交易历史
def get_address_transactions_within_block_number_range_from_jsonrpc(
    address: str, from_block_number: int, to_block_number: int
) -> List[TxData]:
    txs = []
    for block_number in range(from_block_number, to_block_number + 1):
        for tx_hash in w3.eth.get_block(block_number)["transactions"]:
            tx = w3.eth.get_transaction(tx_hash)
            if tx["from"] == address or tx["to"] == address:
                txs.append(tx)

    return Web3.to_json(txs)


# 查询 ERC20 代币余额和转账历史
def get_address_ERC20_token_balance_at_block_number_from_jsonrpc(
    address: str, contract_address: str, block_number: int
) -> int:
    return Web3.to_json(
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


def get_address_ERC20_token_transfers_within_block_number_range_from_jsonrpc(
    address: str, from_block_number: int, to_block_number: int
) -> List[LogReceipt]:
    return Web3.to_json(
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


# 查询 ERC721 (NFT) 转账历史
def get_address_ERC721_NFT_transfers_within_block_number_range_from_jsonrpc(
    address: str, from_block_number: int, to_block_number: int
) -> List[LogReceipt]:
    return Web3.to_json(
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


# 查询 ERC1155 (多代币标准) 转账历史
def get_address_ERC1155_NFT_single_transfers_within_block_number_range_from_jsonrpc(
    address: str, from_block_number: int, to_block_number: int
) -> List[FilterTrace]:
    return Web3.to_json(
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


#
def get_address_ERC1155_NFT_batch_transfers_within_block_number_range_from_jsonrpc(
    address: str, from_block_number: int, to_block_number: int
) -> List[FilterTrace]:
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
    return w3.eth.get_code(contract_address, block_identifier=block_number).hex()


# 获取合约存储数据
def get_contract_storage_at_block_number_from_jsonrpc(
    contract_address: str, position: int, block_number: int
) -> str:
    return w3.eth.get_storage_at(contract_address, position, block_number).hex()


# 查询合约事件日志
def get_contract_events_within_block_number_range_from_jsonrpc(
    contract_address: str, from_block_number: int, to_block_number: int
) -> str:
    return Web3.to_json(
        w3.eth.get_logs(
            {
                "fromBlock": from_block_number,
                "toBlock": to_block_number,
                "address": contract_address,
            }
        )
    )


# 查询各类代币标准(ERC20/721/1155)的转账事件
def get_contract_ERC20_token_transfers_within_block_number_range_from_jsonrpc(
    contract_address: str, from_block_number: int, to_block_number: int
) -> str:
    return Web3.to_json(
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
    )


def get_contract_ERC721_NFT_transfers_within_block_number_range_from_jsonrpc(
    contract_address: str, from_block_number: int, to_block_number: int
) -> List[LogReceipt]:
    return Web3.to_json(
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
    )


def get_contract_ERC1155_NFT_single_transfers_within_block_number_range_from_jsonrpc(
    contract_address: str, from_block_number: int, to_block_number: int
) -> List[FilterTrace]:
    return w3.eth.get_logs(
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
    )


def get_contract_ERC1155_NFT_batch_transfers_within_block_number_range_from_jsonrpc(
    contract_address: str, from_block_number: int, to_block_number: int
) -> List[FilterTrace]:
    return w3.eth.get_logs(
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
    )


class ContractBasicProperties(TypedDict):
    name: str
    symbol: str
    total_supply: int
    decimals: int
    owner: str


def get_contract_basic_info_from_jsonrpc(
    contract_address: str,
) -> ContractBasicProperties:
    return {
        "name": _try_w3_call_fetch_str(
            {
                "to": contract_address,
                "data": w3.keccak(text="name()").hex()[:10],
            }
        )
        or "Not available",
        "symbol": _try_w3_call_fetch_str(
            {
                "to": contract_address,
                "data": w3.keccak(text="symbol()").hex()[:10],
            }
        )
        or "Not available",
        "total_supply": _try_w3_call_fetch_int(
            {
                "to": contract_address,
                "data": w3.keccak(text="totalSupply()").hex()[:10],
            }
        )
        or "Not available",
        "decimals": _try_w3_call_fetch_int(
            {
                "to": contract_address,
                "data": w3.keccak(text="decimals()").hex()[:10],
            }
        )
        or "Not available",
        "owner": _try_w3_call_fetch_str(
            {
                "to": contract_address,
                "data": w3.keccak(text="owner()").hex()[:10],
            }
        )
        or "Not available",
    }


def get_contract_ABI_from_whatsabi(
    contract_address: str, from_block_number: int, to_block_number: int
) -> List[LogReceipt]:
    return w3.eth.get_logs(
        {
            "fromBlock": from_block_number,
            "toBlock": to_block_number,
            "address": contract_address,
            "topics": [w3.keccak(text="Transfer(address,address,uint256)"), None, None],
        }
    )
