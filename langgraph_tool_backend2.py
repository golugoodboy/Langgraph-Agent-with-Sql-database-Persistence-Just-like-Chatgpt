from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from typing import TypedDict , Literal , Annotated
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import SystemMessage, HumanMessage , BaseMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langgraph.prebuilt import tools_condition
import sqlite3
import requests
from langgraph.prebuilt import ToolNode

class chatstate(TypedDict):

    messages : Annotated[list[BaseMessage], add_messages]

load_dotenv()

#***************tools***************************************

search_tool = DuckDuckGoSearchRun(region = "us-en")

@tool
def calculator(first_num : float, second_num : float, operation : str) -> dict:
    """
    Perform basic arithmetic operation on two numbers.
    Supported operation : add, Sub, Multiply, Division
    """
    try:
        if operation == "add":
            result = first_num, + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return{"Error": "division by zero is not allowed"}
            result = first_num / second_num
        else : 
            return {"error" : f"Unsupported operation {operation}"}
        
        return {"first_num" : first_num, "second_num" : second_num, "operation": operation, "result" : result}
    except Exception as e:
        return {"error" : str(e)}

@tool
def get_stock_price(symbol : str) -> dict:
    """
    Fetch latest stock price for a given symbol (eg. "AAPL", "TSLA")
    using alpha vantage with api key in the URL.
    """
    url = f""
    r = requests.get(url)
    return r.json()


tools = [search_tool, get_stock_price, calculator]
#******************************************************************************************

llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2", 
    task="text-generation",
    max_new_tokens=250,
    do_sample=True,
    temperature=0.0,
)



# Wrap as chat model
model = ChatHuggingFace(llm=llm)

model_with_tools = model.bind_tools(tools)


def chat_node(state : chatstate):

    messages = state["messages"]

    response = model_with_tools.invoke(messages)

    return {"messages" : [response]}



tool_node = ToolNode(tools)
 


conn = sqlite3.connect(database = "chatbot.db", check_same_thread = False) 

checkpointer = SqliteSaver(conn = conn) 

graph = StateGraph(chatstate)

graph.add_node('chat node', chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat node")
graph.add_conditional_edges("chat node", tools_condition)
graph.add_edge("tools", END)


workflow = graph.compile(checkpointer = checkpointer)



#**************************************************************
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    
    return list(all_threads)

#*****************************testing**************************

"""config33 = {"configurable" : {"thread_id" : "thread-1"}}

response = workflow.invoke(
             {"messages" : HumanMessage(content = "what is cricket?")},
                config = config33,
        )

print(response) """
#***************************************************************

"""for message_chunk, metadata in workflow.stream(
                {"messages" : HumanMessage(content = "What is the recipe to make pasta ?")},
                config = {"configurable" : {"thread_id" : "thread-1"}},
                stream_mode = "messages"
                ):
    
    if message_chunk.content:
        print(message_chunk.content, end = " ", flush = True) """

#loop 

"""thread_id = 1

while True:

    user_input = input("Type your text here : ")

    print("user : ", user_input)

    if user_input.strip().lower() in ["exit","bye","quit"]:
        break

    config = {"configurable" : {"thread_id" : thread_id}}

    response = workflow.invoke({"messages" : HumanMessage(content = user_input)}, config = config)

    print("AI : ", response["messages"][-1].content)

"""