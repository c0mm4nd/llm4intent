BACKGROUND_PROMPT = """
In Ethereum, a transaction includes both basic transaction data and its receipt. Key transaction fields include: 'from', 'to', 'value', 'input' (calldata), gas information, and block details. The receipt contains the transaction's execution results: status, gas used, logs created, and contract address (if deployed).

Event logs are indexed records emitted during transaction execution, containing: address (contract), topics (indexed parameters, first topic is event signature), and data (non-indexed parameters).

Traces record the internal calls made during transaction execution, showing: call type (CALL, DELEGATECALL, etc.), from/to addresses, value transferred, input data, and error status.

For token standards:
- ERC20 events decode to: Transfer(from, to, value), Approval(owner, spender, value)
- ERC721 events decode to: Transfer(from, to, tokenId), Approval(owner, approved, tokenId), ApprovalForAll(owner, operator, approved)
- ERC1155 events decode to: TransferSingle(operator, from, to, id, value), TransferBatch(operator, from, to, ids, values), ApprovalForAll(owner, operator, approved)
"""

