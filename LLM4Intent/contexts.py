import os
from web3 import Web3
from LLM4Intent.data_types import EventLog, Trace, TransactionWithLogsTraces
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


def get_transaction(
    eth: EthereumProvider, transaction_hash: str
) -> TransactionWithLogsTraces:
    print(f"Getting transaction details for hash {transaction_hash}")
    txhash = Hash(transaction_hash)
    transaction = TransactionWithLogsTraces(list(eth.transactions(f"hash={txhash}"))[0])

    event_logs = [EventLog(log) for log in eth.events(f"transactionHash={txhash}")]
    transaction["logs"] = event_logs
    # TODO: decode topics
    # for log in event_logs:
    #     log["topics"] = [Hash(topic) for topic in log["topics"]]

    traces = [Trace(trace) for trace in eth.traces(f"transactionHash={txhash}")]
    transaction["traces"] = traces

    return transaction


def is_contract(address: str):
    return w3.eth.get_code(address).hex() != "0x"


def get_caller_context(eth: EthereumProvider, caller_address: str):
    print(f"Getting caller context for address {caller_address}")
    # caller must be a user
    return _get_contract_context(eth, caller_address)


def get_callee_context(eth: EthereumProvider, callee_address: str):
    print(f"Getting callee context for address {callee_address}")
    # callee can be a contract or a user
    if is_contract(eth.w3, callee_address):
        return _get_contract_context(eth, callee_address)
    else:
        return _get_user_context(eth, callee_address)


def get_address_transaction_context(eth: EthereumProvider, user_address: str):
    print(f"Getting user context for address {user_address}")

    user_addr = Address(user_address)

    {
        "sent_transactions": list(eth.transactions(f"from={user_addr}")),
        "received_transactions": list(eth.transactions(f"to={user_addr}")),
    }


def get_address_transfer_context(eth: EthereumProvider, user_address: str):
    print(f"Getting user context for address {user_address}")

    user_addr = Address(user_address)
    sent_transfer_events = list(
        eth.events(f"topic0={Hash(TRANSFER_TOPIC)} and topic1={user_addr}")
    )
    received_transfer_events = list(
        eth.events(f"topic0={Hash(TRANSFER_TOPIC)} and topic2={user_addr}")
    )

    sent_transfers = []
    for event in sent_transfer_events:
        erc20decoder.decode_event_log(event)
        event["decoded"] = erc20decoder.decode_event_log(event)
        sent_transfers.append(event)

    received_transfers = []
    for event in received_transfer_events:
        erc20decoder.decode_event_log(event)
        event["decoded"] = erc20decoder.decode_event_log(event)
        received_transfers.append(event)

    return {
        "sent_transfer": sent_transfers,
        "received_transfer": received_transfers,
        "warnings": "TRANSFER events may not only be ERC20 transfers, but also ERC721 transfers, "
        "so check the decoded data and contract name to confirm the type of transfer",
    }


def get_contract_name(eth: EthereumProvider, contract_address: str, days: str = 1):
    print(f"Getting contract context for address {contract_address}")

    contract_addr = Address(contract_address)
