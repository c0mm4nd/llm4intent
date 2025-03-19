import os
from typing import List
import requests
from tavily import TavilyClient
from web3 import Web3

from LLM4Intent.tools.etherscan import get_verified_contract_abi_from_etherscan

# Step 1. Instantiating your TavilyClient
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

def search_webpages_from_tavily(query) -> dict:
    response = tavily_client.search(query)

    print("Search Response:", response)
    
    return response

def extract_webpage_info_by_urls_from_tavily(urls: List[str]) -> dict:
    response = tavily_client.extract(urls)

    print("Extract Response:", response)
    
    return response



def get_function_signatures_from_signature_database(hex_signature: str) -> dict:
    response = requests.get("https://evmlookup.vercel.app/api/keccak256/function?query={query}".format(query=hex_signature))
    result = response.json()

    return result["data"]

def get_event_signatures_from_signature_database(hex_signature: str) -> dict:
    response = requests.get("https://evmlookup.vercel.app/api/keccak256/event?query={query}".format(query=hex_signature))
    result = response.json()

    return result["data"]


def get_contract_ABI_from_whatsabi(contract_address: str) -> dict:
    url = f"https://evmlookup.web3resear.ch/api/whatsabi?contract={contract_address}"
    return requests.get(url).json()


def get_address_labels_from_github_repo(address: str) -> list:
    url = f"https://eth-labels-production.up.railway.app/labels/{address}"

    response = requests.get(url)

    return response.json()
