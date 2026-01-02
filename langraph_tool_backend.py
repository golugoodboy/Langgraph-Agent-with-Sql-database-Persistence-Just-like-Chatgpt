import streamlit as st
from langgraph_tool_backend2 import workflow, retrieve_all_threads
from langchain_core.messages import SystemMessage, HumanMessage
import uuid


#*******************************************************utility*********************************

def generate_uuid():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_uuid()
    st.session_state["thread_id"] = thread_id
    add_thread(st.session_state["thread_id"])
    st.session_state["message_history"] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state["chat_threads"].append(thread_id)

def load_conversation(thread_id):
    return workflow.get_state(config = {"configurable" : {"thread_id" : thread_id}}).values["messages"]

#***********************************************************************************************


if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_uuid()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()

add_thread(st.session_state["thread_id"])


#*************************************side bar UI****************************************

st.sidebar.title("Golu GPT")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My conversation")

for thread_id in st.session_state["chat_threads"][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            else:
                role = "assistant"
            temp_messages.append({"role" : role, "content" : msg.content})
 
        st.session_state["message_history"] = temp_messages

#********************************************************loading the conversation history*************************
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])


config33 = {"configurable" : {"thread_id" : st.session_state["thread_id"]},
            "metadata" : {
                "thread_id" : st.session_state["thread_id"]
            },
            "run_name" : "chat_run"}  #we wrote this so that we can send the threads to langsmith and organize it 

user_input = st.chat_input("Enter your desires")

if user_input:
    st.session_state['message_history'].append({"role" : "user", "content" : user_input})
    with st.chat_message("user"):
        st.text(user_input)

    #response = workflow.invoke({"messages" : HumanMessage(content = user_input)}, config = config33)
    #ai_message = response["messages"][-1].content
    
    #st.session_state['message_history'].append({"role" : "assistant", "content" : ai_message})
    with st.chat_message("assistant"):

        ai_message = st.write_stream(
        message_chunk.content for message_chunk, metadata in workflow.stream(
             {"messages" : HumanMessage(content = user_input)},
                config = config33,
                stream_mode = "messages"
        )
        )
    st.session_state['message_history'].append({"role" : "assistant", "content" : ai_message})

