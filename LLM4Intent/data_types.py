from typing import List, TypedDict


Transaction = TypedDict(
    "Transaction",
    {
        "hash": str,
        "blockHash": str,
        "blockNumber": int,
        "blockTimestamp": int,
        "transactionIndex": int,
        "chainId": int,
        "type": int,
        "from": str,
        "to": str,
        "value": int,
        "nonce": int,
        "input": str,
        "gas": int,
        "gasPrice": int,
        "maxFeePerGas": int,
        "maxPriorityFeePerGas": int,
        "r": str,
        "s": str,
        "v": int,
        "accessList": List,
        "contractAddress": str,
        "cumulativeGasUsed": int,
        "effectiveGasPrice": int,
        "gasUsed": int,
        "logsBloom": str,
        "root": str,
        "status": int,
    },
)


class EventLog(TypedDict):
    address: str
    blockHash: str
    blockNumber: int
    blockTimestamp: int
    transactionHash: str
    transactionIndex: int
    logIndex: int
    removed: bool
    topics: list
    data: str


class Trace(TypedDict):
    blockPos: int
    blockNumber: int
    blockTimestamp: int
    blockHash: str
    transactionHash: str
    traceAddress: list
    subtraces: int
    transactionPosition: int
    error: str
    actionType: str
    actionCallFrom: str
    actionCallTo: str
    actionCallValue: int
    actionCallInput: str
    actionCallGas: int
    actionCallType: str
    actionCreateFrom: str
    actionCreateValue: int
    actionCreateInit: str
    actionCreateGas: int
    actionSuicideAddress: str
    actionSuicideRefundAddress: str
    actionSuicideBalance: int
    actionRewardAuthor: str
    actionRewardValue: int
    actionRewardType: str
    resultType: str
    resultCallGasUsed: int
    resultCallOutput: str
    resultCreateGasUsed: int
    resultCreateCode: str
    resultCreateAddress: str


class TransactionWithLogsTraces(Transaction):
    logs: list[EventLog]
    traces: list[Trace]

class UserContext(TypedDict):
    pass

class ContractContext(TypedDict):
    pass

# class FlowContext(TypedDict):

class SemanticTransaction(TransactionWithLogsTraces):
    '''
    use human language to describe a transaction
    '''

    def __repr__(self):
        assert self.get("status") == 1, "Transaction is failed"
        template = """
Transaction {hash} called by {from_address} to {to_address} with value {value}, gas used {gas}, price {gas_price}, 
with logs as the following:
\t{logs}
and traces as the following:
\t{traces}
"""
        semantic_logs = []
        for log in self["logs"]:
            semantic_logs.append(SemanticEventLog(log))
        semantic_traces = []
        for trace in self["traces"]:
            semantic_traces.append(SemanticTrace(trace))
        
        return template.format(
            hash=self["hash"],
            from_address=self["from"],
            to_address=self["to"],
            value=self["value"],
            gas=self["gas"],
            gas_price=self.get("gasPrice"),
            logs="\n\t".join([str(log) for log in semantic_logs]),
            traces="\n\t".join([str(trace) for trace in semantic_traces]),
        )

class SemanticEventLog(EventLog):
    '''
    use human language to describe an event log
    '''

    def __repr__(self):
        template = """
EventLog {logIndex} in block {blockNumber} at {blockTimestamp} with topics {topics} and data {data}
"""
        
        return template.format(
            logIndex=self["logIndex"],
            blockNumber=self["blockNumber"],
            blockTimestamp=self["blockTimestamp"],
            topics=self["topics"],
            data=self["data"],
        )

class SemanticTrace(Trace):
    '''
    use human language to describe a trace
    '''

    def __repr__(self):
        template = """
Trace {traceAddress} in block {blockNumber} at {blockTimestamp} with subtraces {subtraces} and actionType {actionType}
"""

        return template.format(
            traceAddress=self["traceAddress"],
            blockNumber=self["blockNumber"],
            blockTimestamp=self["blockTimestamp"],
            subtraces=self.get("subtraces", 0),
            actionType=self["actionType"],
        )

