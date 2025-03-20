from LLM4Intent.tools.annotated import get_function_signature
from LLM4Intent.tools.web2 import get_address_labels_from_github_repo


def test_get_address_labels_from_github_repo():
    labels = get_address_labels_from_github_repo("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")
    print(labels)
    assert labels

def test_get_function_signature():
    signatures = get_function_signature("0x44087E105137a5095c008AaB6a6530182821F2F0", "0xc71e393f1527f71ce01b78ea87c9bd4fca84f1482359ce7ac9b73f358c61b1e1")
    print(signatures)
    assert signatures == []
