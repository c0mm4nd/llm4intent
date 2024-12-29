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
from langchain.tools import Tool

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from LLM4Intent.contexts import get_transaction
from LLM4Intent.data_types import TransactionWithLogsTraces

# 修正代理设置
os.environ['http_proxy'] = 'http://localhost:7890'
os.environ['https_proxy'] = 'http://localhost:7890'

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
    '''Get transaction details'''
    return get_transaction(eth, tx_hash)

# 使用 langchain Tool 正确格式化工具
tools = [
    Tool(
        name="get_tx_detail",
        description="Get transaction details from a transaction hash",
        func=get_tx_detail
    )
]

# 创建工具执行器
tool_executor = ToolNode(tools)

# Create prompts
retriever_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a transaction data retriever. Your role is to fetch and provide transaction data."),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "Transaction hash: {tx_hash}\nRetrieve the transaction data and provide relevant details."),
])

analyzer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a transaction intent analyzer. Your role is to analyze the intent behind transactions. Provide a single word to describe the main intent."),
    MessagesPlaceholder(variable_name="messages"),
    ("human", """Here is the transaction data:
    Transaction Hash: {tx_hash}
    Transaction Data: {formatted_data}
    
    Based on this data, what is the intent of this transaction? Reply with a single word."""),
])

def retrieve_transaction(state: AgentState) -> AgentState:
    try:
        # 直接调用函数获取交易数据
        tx_data = get_tx_detail(state["tx_hash"])
        # print("Raw tx_data:", tx_data)  # 打印原始数据
        
        # 提取关键信息，构建更有意义的数据描述
        if tx_data:
            data_description = f"""Transaction Details:
- Hash: {state['tx_hash']}
- Data: {tx_data}
"""
        else:
            data_description = f"Unable to retrieve details for transaction {state['tx_hash']}"
        
        # 添加到消息历史
        messages = [
            *state["messages"],
            AIMessage(content=data_description)
        ]
        
        return {
            **state,
            "messages": messages,
            "tx_data": tx_data,
            "next": "analyze"
        }
        
    except Exception as e:
        error_message = f"Error retrieving transaction data: {str(e)}"
        print(error_message)
        messages = [
            *state["messages"],
            AIMessage(content=error_message)
        ]
        return {
            **state,
            "messages": messages,
            "tx_data": None,
            "next": "analyze"
        }

def analyze_intent(state: AgentState) -> AgentState:
    tx_data = state["tx_data"]
    
    if not tx_data:
        analysis = "Unable to analyze: No transaction data available"
    else:
        analyzer_chain = analyzer_prompt | analyzer_llm | StrOutputParser()
        analysis = analyzer_chain.invoke({
            "messages": state["messages"],
            "tx_hash": state["tx_hash"],
            "formatted_data": str(tx_data)
        })
    
    messages = [*state["messages"], AIMessage(content=analysis)]
    return {
        **state,
        "messages": messages,
        "final_summary": analysis,
        "next": END
    }

def create_graph() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    workflow.add_node("retrieve", retrieve_transaction)
    workflow.add_node("analyze", analyze_intent)
    
    workflow.add_edge("retrieve", "analyze")
    workflow.add_edge("analyze", END)
    
    workflow.set_entry_point("retrieve")
    
    return workflow

def start_agents(tx_hash: str) -> dict:
    workflow = create_graph().compile()
    
    initial_state = AgentState(
        messages=[HumanMessage(content=f"Analyze transaction: {tx_hash}")],
        next="retrieve",
        tx_hash=tx_hash,
        tx_data=None,
        final_summary=None
    )
    
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