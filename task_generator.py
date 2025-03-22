from LLM4Intent.tools.annotated import (
    get_address_transactions_within_block_number_range,
    get_token_transfers_within_block_number_range,
    get_transactions_to_address_within_block_number_range,
)
import json
import random
import os

contracts = set(
    [
        "0xfddf38947afb03c621c71b06c9c70bce73f12999",
        "0xa700b4eb416be35b2911fd5dee80678ff64ff6c9",
        "0xec53bf9167f50cdeb3ae105f56099aaab9061f83",
        "0x9d39a5de30e57443bff2a8307a4256c8797a3497",
        "0x346e03f8cce9fe01dcb3d0da3e9d00dc2c0e08f0",
        "0x1dfe41cc7f7860ba7f1076ca6d0fedd707c87a00",
        "0x011b6e24ffb0b5f5fcc564cf4183c5bbbc96d515",
        "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2",
        "0x256f2d67e52fe834726d2ddcd8413654f5eb8b53",
        "0x0733f618118bf420b6b604c969498ecf143681a8",
        "0x77777feddddffc19ff86db637967013e6c6a116c",
        "0xba100000625a3754423978a60c9317c58a424e3d",
        "0x8daebade922df735c38c80c7ebd708af50815faa",
        "0xCC4304A31d09258b0029eA7FE63d032f52e44EFe",
        "0x016a7287f0fdbdce5f903334f574b2238be3fa25",
        "0xaed662abcc4fa3314985e67ea993cad064a7f5cf",
        "0x01bfd82675dbcc7762c84019ca518e701c0cd07e",
        "0xff20817765cb7f73d4bde2e66e067e58d11095c2",
        "0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f",
        "0x5283d291dbcf85356a21ba090e6db59121208b44",
        "0x584bC13c7D411c00c01A62e8019472dE68768430",
        "0x0cec1a9154ff802e7934fc916ed7ca50bde6844e",
        "0x6123b0049f904d730db3c36a31167d9d4121fa6b",
        "0x9416ba76e88d873050a06e5956a3ebf10386b863",
        "0x6810e776880c02933d47db1b9fc05908e5386b96",
        "0x111111111117dc0aa78b770fa6a738034120c302",
        "0xbbBBBBB5AA847A2003fbC6b5C16DF0Bd1E725f61",
        "0x66761fa41377003622aee3c7675fc7b5c1c2fac5",
        "0xc55126051b22ebb829d00368f4b12bde432de5da",
        "0x3F382DbD960E3a9bbCeaE22651E88158d2791550",
        "0x3b21418081528845a6df4e970bd2185545b712ba",
        "0xa9c125bf4c8bb26f299c00969532b66732b1f758",
        "0x7728cd70b3dd86210e2bd321437f448231b81733",
        "0x10703ca5e253306e2ababd68e963198be8887c81",
        "0x56ee175fe37cd461486ce3c3166e0cafccd9843f",
        "0x14fee680690900ba0cccfc76ad70fd1b95d10e16",
        "0x88800092ff476844f74dc2fc427974bbee2794ae",
    ]
)

for contract in contracts:
    print(contract)
    if os.path.exists(f"./task_samples/{contract}.json"):
        print(f"Skipping {contract}")
        continue

    tfs = get_token_transfers_within_block_number_range(contract, 0, 23_000_000)
    txs = get_transactions_to_address_within_block_number_range(contract, 0, 23_000_000)
    tfs = [tf["transactionHash"] for tf in tfs]
    txs = [tx["hash"] for tx in txs]
    os.makedirs("./task_samples", exist_ok=True)
    with open(f"./tasks/{contract}.json", "w") as f:
        json.dump(
            {
                "txs": txs,
                "tfs": tfs,
            },
            f,
        )
    os.makedirs("./task_samples", exist_ok=True)
    with open(f"./task_samples/{contract}.json", "w") as f:
        json.dump(
            {
                "txs": random.sample(txs, min(len(txs), 100)),
                "tfs": random.sample(tfs, min(len(tfs), 100)),
            },
            f,
        )
