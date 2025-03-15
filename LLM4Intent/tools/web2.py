import os
from typing import List
import requests
from tavily import TavilyClient
from web3 import Web3

# Step 1. Instantiating your TavilyClient
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

def search_webpage_from_google(query) -> dict:
    response = tavily_client.search(query)

    print("Search Response:", response)
    
    return response

def extract_webpage_info_by_urls(urls: List[str]) -> dict:
    response = tavily_client.extract(urls)

    print("Extract Response:", response)
    
    return response



def get_function_signatures_from_signature_database(hex_signature: str) -> dict:
    response = requests.get("https://evmlookup.vercel.app/api/signatures?q={query}".format(query=hex_signature))
    result = response.json()

    return result["data"]

def get_event_signatures_from_signature_database(hex_signature: str) -> dict:
    response = requests.get("https://evmlookup.vercel.app/api/signatures?q={query}".format(query=hex_signature))
    result = response.json()

    return result["data"]


def get_contract_ABI_from_whatsabi(contract_address: str) -> dict:
    url = f"https://evmlookup.web3resear.ch/api/whatsabi?contract={contract_address}"
    return requests.get(url).json()

