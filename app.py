import streamlit as st
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
import asyncio
import shelve
import os
from bot import agent_executor_gem, agent_executor_gpt
from handle_system_files import files_handler
import base64



USER_AVATAR = "👦"
BOT_AVATAR = "🤖"
TOOL_AVATAR = "🔗"

# Load the image and convert it to base64

def gen_response(prompt,thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [("user", prompt)]}
    for s in agent_executor.stream(inputs, config=config, stream_mode="values"):
        message = s["messages"][-1]
        if isinstance(message, AIMessage):
            if message.tool_calls:
                if show_tools:
                    new_message = 'Tool call by Assistant\n'
                    for tool_call in message.tool_calls:
                        name = tool_call['name']
                        args = tool_call['args']
                        new_message += f'Tool name : {name}\n'
                        if args:
                            new_message += f'Arguments : {args}\n'
                    yield new_message, TOOL_AVATAR, "tool"
            else:    
                yield message.content, BOT_AVATAR, "assistant"
        if show_tools and isinstance(message, ToolMessage):
            yield 'Tool Output:\n'+ message.content, TOOL_AVATAR, "tool"


#load_dotenv()

st.title("Smart OS")

st.markdown(
    """
    <style>
    /* Adjust sidebar width */
    .css-1d391kg {  /* Change the class name if necessary */
        width: 300px;  /* Set desired width */
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.title("Select Model")
    if agent_executor_gpt:
        model_option = st.radio("Choose the language model:", ["GPT-3.5", "Gemini 1.5 Flash"])
    else:
        model_option = st.radio("Choose the language model:", ["Gemini 1.5 Flash"])
        

if model_option == "GPT-3.5":
    agent_executor = agent_executor_gpt
elif model_option == "Gemini 1.5 Flash":
    agent_executor = agent_executor_gem  

with st.sidebar:
    with st.expander("Fetch all files"):
        st.write("Do this if you are opening the app for first time, otherwise just do update. It will fetch all files along with their paths and save. It will take around 2-3 mins depending on number of files in your laptop. This will fetch files only in C and D drives.")

        # Display Confirm and Cancel buttons
        col1, col2 = st.columns(2)
        with col1:
            fetch = st.button('Fetch')
        with col2:
            cancel = st.button('Cancel')
        if fetch:
            st.write("Fetching files.. Don't retry until it's done.")
            files_handler.all_files_index = files_handler.index_files_and_directories(files_handler.root_paths) 
            files_handler.save_files()
            st.write('Fetching completed.')    


with st.sidebar:
    with st.expander("Create Embeddings"):
        st.write("Do this if you are opening the app for first time, otherwise just do update. It will create embeddings for fetched files. It will take 2-3 hours depending upon number of files in your laptop.")

        # Display Confirm and Cancel buttons
        col1, col2 = st.columns(2)
        with col1:
            create = st.button('Create')
        with col2:
            cancel2 = st.button('Cancel creation')
        if create:
            st.write("Creating Embeddings... Don't retry until it's done.")
            files_handler.faiss_index_files_and_directories(files_handler.all_files) 
            files_handler.save_faiss_files()
            st.write('Completed.')    

with st.sidebar:
    with st.expander("Update all files"):
        st.write("Do this when there are some changes in the files and directories. It will update files and their embeddings. it will take around 5 mins.")

        # Display Confirm and Cancel buttons
        col1, col2 = st.columns(2)
        with col1:
            update = st.button('Update')
        with col2:
            cancel3 = st.button('Cancel Update')
        if update:
            st.write("Updating files.. Don't retry until it's done.")
            files_handler.check_updates()
            st.write('Completed.')    


# Ensure openai_model is initialized in session state
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = "1"


# Load chat history from shelve file
def load_chat_history():
    with shelve.open("chat_history") as db:
        return db.get("messages", [])


# Save chat history to shelve file
def save_chat_history(messages):
    with shelve.open("chat_history") as db:
        db["messages"] = messages


# Initialize or load chat history
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

with st.sidebar:
    show_tools = st.checkbox("Show Tool Calls.")


# Sidebar with a button to delete chat history
with st.sidebar:
    if st.button("Delete Chat History"):
        st.session_state.messages = []
        save_chat_history([])
        st.session_state["thread_id"] = str(int(st.session_state["thread_id"])+1)

# Display chat messages
for message in st.session_state.messages:
    avatars = {"user":USER_AVATAR, "assistant":BOT_AVATAR, "tool":TOOL_AVATAR}
    avatar = avatars[message["role"]] 
    with st.chat_message(message["role"], avatar=avatar):
        st.text(message["content"])

# Main chat interface
if prompt := st.chat_input("How can I help?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    for s, avt, r in gen_response(prompt,st.session_state["thread_id"]): 
        with st.chat_message(r, avatar=avt):
            response = st.text(s)
            st.session_state.messages.append({"role": r, "content": s})

# Save chat history after each interaction
save_chat_history(st.session_state.messages)        
        
