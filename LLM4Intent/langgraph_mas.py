import os
from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv
from web3 import Web3
from web3research import Web3Research
from web3research.common import Hash

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSequence

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor

from LLM4Intent.contexts import get_transaction
from LLM4Intent.data_types import TransactionWithLogsTraces

# Load environment variables
load_dotenv()

# Initialize Web3 clients
w3 = Web3()
w3r = Web3Research(api_token=os.environ.get("W3R_API_KEY"))
eth = w3r.eth(backend=os.environ.get("W3R_BACKEND"))

# Define state type
class AgentState(TypedDict):
    messages: Sequence[HumanMessage | AIMessage]
    next: str
    tx_hash: str
    tx_data: TransactionWithLogsTraces | None
    final_summary: str | None

# Initialize LLM
retriever_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0.1,
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
)

analyzer_llm = retriever_llm  # Using same LLM for both roles

def get_tx_detail(tx_hash: str) -> TransactionWithLogsTraces:
    '''
    Get transaction details.

    Args:
    - tx_hash (str): Transaction hash

    Returns:
    - TransactionWithLogsTraces: Transaction details
    '''
    return get_transaction(eth, tx_hash)

# Define tools
tools = [get_tx_detail]
tool_executor = ToolExecutor(tools)

# Create prompts
retriever_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a transaction data retriever. Your role is to fetch and provide transaction data."),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "Transaction hash: {tx_hash}\nRetrieve the transaction data and provide relevant details."),
])

analyzer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a transaction intent analyzer. Your role is to analyze the intent behind transactions."),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "Based on the transaction data: {tx_data}\nAnalyze the intent and summarize in one word."),
])

# Define agent functions
def retrieve_transaction(state: AgentState) -> AgentState:
    # Get transaction data using tool
    tx_data = tool_executor.execute("get_transaction", state["tx_hash"])
    
    # Generate retriever response
    retriever_chain = retriever_prompt | retriever_llm | StrOutputParser()
    retriever_response = retriever_chain.invoke({
        "messages": state["messages"],
        "tx_hash": state["tx_hash"]
    })
    
    # Update state
    messages = [*state["messages"], AIMessage(content=retriever_response)]
    return {
        **state,
        "messages": messages,
        "tx_data": tx_data,
        "next": "analyze"
    }

def analyze_intent(state: AgentState) -> AgentState:
    # Generate analyzer response
    analyzer_chain = analyzer_prompt | analyzer_llm | StrOutputParser()
    analysis = analyzer_chain.invoke({
        "messages": state["messages"],
        "tx_data": state["tx_data"]
    })
    
    # Update state
    messages = [*state["messages"], AIMessage(content=analysis)]
    return {
        **state,
        "messages": messages,
        "final_summary": analysis,
        "next": END
    }

# Create workflow graph
def create_graph() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_transaction)
    workflow.add_node("analyze", analyze_intent)
    
    # Add edges
    workflow.add_edge("retrieve", "analyze")
    workflow.add_edge("analyze", END)
    
    # Set entry point
    workflow.set_entry_point("retrieve")
    
    return workflow

def start_agents(tx_hash: str) -> dict:
    # Initialize workflow
    workflow = create_graph().compile()
    
    # Initialize state
    initial_state = AgentState(
        messages=[HumanMessage(content=f"Analyze transaction: {tx_hash}")],
        next="retrieve",
        tx_hash=tx_hash,
        tx_data=None,
        final_summary=None
    )
    
    # Execute workflow
    result = workflow.invoke(initial_state)
    
    return {
        "summary": result["final_summary"],
        "messages": result["messages"]
    }

if __name__ == "__main__":
    # Test transaction
    test_tx_hash = "0x43a2cb2a2a4fa683a67db6f828d2db99e1253a33a8eb1032915e50f71d85a9f0"
    
    # Run analysis
    result = start_agents(test_tx_hash)
    print("Final summary:", result["summary"])
    