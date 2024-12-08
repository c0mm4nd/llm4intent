from LLM4Intent.data_types import EventLog, Trace, TransactionWithLogsTraces
from web3research.eth import EthereumProvider
from web3research.common import Hash


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
