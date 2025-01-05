from LLM4Intent.common.data_types import EventLog, Trace, TransactionWithLogsTraces
import os
import asyncio
from web3 import Web3
from LLM4Intent.common.data_types import EventLog, Trace, TransactionWithLogsTraces
from aiohttp_retry import ExponentialRetry
from asyncio_throttle import Throttler
from aioetherscan import Client
from web3research.eth import EthereumProvider
from web3research.common import Hash, Address
from web3research.evm import ERC20_ABI, ContractDecoder

w3 = Web3()

erc20decoder = ContractDecoder(w3, ERC20_ABI)
TRANSFER_TOPIC = erc20decoder.get_event_topic("Transfer")

throttler = Throttler(rate_limit=4, period=1.0)
retry_options = ExponentialRetry(attempts=2)
etherscan = Client(
    os.environ["ETHERSCAN_API_KEY"], throttler=throttler, retry_options=retry_options
)

def get_transaction_from_etherscan(tx_hash: str) -> dict:
    return asyncio.run(etherscan.proxy.tx_by_hash(tx_hash))
    
def get_transaction_receipt_from_etherscan(tx_hash: str) -> dict:
    return asyncio.run(etherscan.proxy.tx_receipt(tx_hash))

def get_transaction_with_logs_traces_from_etherscan(contract_address: str) -> TransactionWithLogsTraces:
    return asyncio.run(etherscan.contract.contract_source_code(contract_address))

def get_logs_from_etherscan(contract_address: str, from_block: int, to_block: int) -> list:
    return asyncio.run(etherscan.contract.logs(contract_address, from_block, to_block))

def get_address_balance_from_etherscan(address: str) -> str:
    return asyncio.run(etherscan.account.balance(address))

def get_event_logs_by_address_from_etherscan(contract_address: str, from_block: int, to_block: int) -> list:
    return asyncio.run(etherscan.logs.get_logs(contract_address, from_block, to_block))

def get_event_logs_by_topic_from_etherscan(contract_address: str, topic: str, from_block: int, to_block: int) -> list:
    return asyncio.run(etherscan.logs.get_logs(contract_address, from_block, to_block, topics=[topic]))
