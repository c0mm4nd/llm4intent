import os
from typing import Annotated, Sequence, TypedDict, List, Dict, Any
from dotenv import load_dotenv
from web3 import Web3
from web3research import Web3Research
from langchain.agents import AgentExecutor, Tool
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain_core.agents import AgentAction, AgentFinish
from langchain_community.chat_models import ChatOpenAI

# Import transaction related functions
from LLM4Intent.contexts import get_transaction
from LLM4Intent.data_types import TransactionWithLogsTraces

# Initialize environment and clients
load_dotenv()
os.environ['http_proxy'] = 'http://localhost:7890'
os.environ['https_proxy'] = 'http://localhost:7890'

w3 = Web3()
w3r = Web3Research(api_token=os.environ.get("W3R_API_KEY"))
eth = w3r.eth(backend=os.environ.get("W3R_BACKEND"))

class TransactionAgent:
    def __init__(self, name: str, role: str, llm: ChatGoogleGenerativeAI):
        self.name = name
        self.role = role
        self.llm = llm
        self.memory: List[BaseMessage] = []

    def generate_response(self, message: str, conversation_history: List[Dict]) -> str:
        # Format conversation history for context
        context = self._format_conversation(conversation_history)
        
        # Create prompt based on role
        if self.role == "retriever":
            prompt = f"""You are {self.name}, a blockchain transaction data retriever.
Previous conversation: {context}
Current request: {message}

Your task is to examine the transaction data and report:
1. Basic transaction info (from, to, value)
2. All token transfers (address and amount)
3. Method calls and their parameters
4. Contract interactions sequence

Focus on reporting facts, not interpretation. Be precise about addresses and values."""

        elif self.role == "analyzer":
            prompt = f"""You are {self.name}, a blockchain transaction intent analyzer.
Previous conversation: {context}
Current request: {message}

Based on the retriever's observations, analyze:
1. Transaction purpose
2. Operation patterns
3. Contract interaction flow
4. Likely user intention

Support your analysis with specific data points from the retriever's report."""

        elif self.role == "validator":
            prompt = f"""You are {self.name}, a validation expert.
Previous conversation: {context}
Current request: {message}

Your tasks:
1. Cross-check data interpretation
2. Verify pattern recognition
3. Validate or challenge proposed intent
4. Highlight any overlooked elements

Be constructively critical and thorough in your review."""

        response = self.llm.predict(prompt)
        self.memory.append(HumanMessage(content=message))
        self.memory.append(AIMessage(content=response))
        return response

    def _format_conversation(self, conversation: List[Dict]) -> str:
        formatted = []
        for msg in conversation:
            formatted.append(f"{msg['agent']}: {msg['message']}")
        return "\n".join(formatted)

def get_transaction_data(tx_hash: str) -> str:
    """Get and format transaction data"""
    print(f"Fetching transaction data for {tx_hash}")
    tx_data = get_transaction(eth, tx_hash)
    return str(tx_data)

class TransactionAnalysisSystem:
    def __init__(self):
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.1,
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
        )
        
        # Initialize agents
        self.retriever = TransactionAgent("Data Retriever", "retriever", self.llm)
        self.analyzer = TransactionAgent("Intent Analyzer", "analyzer", self.llm)
        self.validator = TransactionAgent("Intent Validator", "validator", self.llm)
        
        self.conversation_history: List[Dict] = []

    def analyze_transaction(self, tx_hash: str) -> str:
        print(f"Starting analysis for transaction: {tx_hash}")
        
        # Step 1: Get transaction data
        tx_data = get_transaction_data(tx_hash)
        print("Transaction data retrieved successfully")
        
        # Step 2: Data Retriever analyzes the raw data
        retriever_msg = f"Please analyze this transaction data: {tx_data}"
        print("Getting retriever's analysis...")
        retriever_response = self.retriever.generate_response(retriever_msg, self.conversation_history)
        self.conversation_history.append({
            "agent": "Data Retriever",
            "message": retriever_response
        })
        
        # Step 3: Intent Analyzer processes the retriever's findings
        analyzer_msg = f"Based on the retriever's analysis, what is the transaction's intent?"
        print("Getting analyzer's interpretation...")
        analyzer_response = self.analyzer.generate_response(analyzer_msg, self.conversation_history)
        self.conversation_history.append({
            "agent": "Intent Analyzer",
            "message": analyzer_response
        })
        
        # Step 4: Validator verifies the analysis
        validator_msg = "Please validate the analysis and proposed intent."
        print("Getting validator's assessment...")
        validator_response = self.validator.generate_response(validator_msg, self.conversation_history)
        self.conversation_history.append({
            "agent": "Intent Validator",
            "message": validator_response
        })
        
        # Step 5: Final discussion round if needed
        if "uncertain" in validator_response.lower() or "disagree" in validator_response.lower():
            print("Additional discussion needed...")
            analyzer_msg = "Please address the validator's concerns and provide a final intent determination."
            final_response = self.analyzer.generate_response(analyzer_msg, self.conversation_history)
            self.conversation_history.append({
                "agent": "Intent Analyzer",
                "message": final_response
            })
        
        print("Analysis complete")
        return self.format_conversation()

    def format_conversation(self) -> str:
        output = "\n" + "="*50 + "\n"
        output += "Transaction Analysis Discussion:\n" + "="*50 + "\n\n"
        
        for entry in self.conversation_history:
            output += f"{entry['agent']}:\n{entry['message']}\n\n" + "-"*30 + "\n\n"
        
        return output

if __name__ == "__main__":
    # Test transaction
    test_tx_hash = "0x43a2cb2a2a4fa683a67db6f828d2db99e1253a33a8eb1032915e50f71d85a9f0"
    
    # Initialize and run analysis
    print("Initializing analysis system...")
    analysis_system = TransactionAnalysisSystem()
    result = analysis_system.analyze_transaction(test_tx_hash)
    print(result)