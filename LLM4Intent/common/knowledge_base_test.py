import json
from LLM4Intent.common.knowledge_base import MemoryGraph
from LLM4Intent.tools.jsonrpc import get_address_type_from_jsonrpc, get_transaction_from_jsonrpc, get_transaction_receipt_logs_with_index_range_from_jsonrpc

def test_MemoryGraph():
    memory_graph = MemoryGraph()
    response = get_transaction_from_jsonrpc("0x343888f0139d467f6b61607400cfae6f8fd26e19fc89aa919c7f8d15718878d1")

    memory_graph.add_transaction(response)

    print(memory_graph.get_encoding())
