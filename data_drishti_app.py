from openai import OpenAI
import re
import streamlit as st
import pandas as pd
import numpy as np
from chat2plot import chat2plot
from prompts import get_start_prompt


st.title("🕵️‍♂️DataDristi")

# Create a sidebar with navigation links
st.sidebar.title("🕵️‍♂️DataDrishti")

# PART 1 - Side Navbar

st.sidebar.title("Navigation")
tabs = ["How it Works", "Chat"]

current_tab = st.sidebar.radio("Select a tab", tabs)
author_name = "[@pathakcodes]"
author_github_url = "https://github.com/pathakcodes"  # Replace with the actual GitHub profile URL


# Get user input using a text input widget in the sidebar
OPENAI_API_KEY = st.sidebar.text_input("OpenAPI Key", value = st.secrets.OPENAI_API_KEY, type="password")
DB = st.sidebar.text_input("Database Name", value = "FROSTY_SAMPLE")
TABLE_SCHEMA = st.sidebar.text_input("Table Schema", value = "CYBERSYN_FINANCIAL")
TABLE = st.sidebar.text_input("Table Name", value = "HEALTHDATANEW")
TABLE_DESCRIPTION = st.sidebar.text_input("Table Name", value = "This table has various metrics for health data of India.")
client = OpenAI(api_key=OPENAI_API_KEY)

# Button to trigger the function invocation
if st.sidebar.button("Start Exploring table"):
    client = OpenAI(api_key=OPENAI_API_KEY)
    QUALIFIED_TABLE_NAME = f"{DB}.{TABLE_SCHEMA}.{TABLE}"
    METADATA_QUERY = f"SELECT COLUMN_NAME FROM {DB}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{TABLE_SCHEMA}' AND TABLE_NAME = '{TABLE}';"
    st.session_state.messages = [{"role": "system", "content": get_start_prompt(QUALIFIED_TABLE_NAME, TABLE_DESCRIPTION, METADATA_QUERY)}]

st.sidebar.markdown(f"Made with ❤️ by {author_name}({author_github_url})")
st.sidebar.markdown("at ❄️Snowflake: Data for Good Hackathon")
st.sidebar.markdown("Jan, 2024")


#PART 2 : How it Works Tab

if current_tab == "How it Works":
    st.header("How DataDrishti Works")
    st.markdown(
        """
        DataDrishti is a chat-based interface powered by GPT-3.5 Turbo, which allows you to interact with
        the Snowflake Database and Tables. You can input commands, queries, or ask for information, and DataDrishti will
        respond accordingly.

        **How to Use:**
        1. Enter your message in the chat input on the main tab.
        2. DataDrishti will respond with information or execute SQL queries if applicable.
        3. The assistant can generate plots based on the data, like if asked to make pie chart it will make one

        **Interact with Data:**
        - If DataDrishti detects a SQL query in the response, it will execute the query and display the results.
        - Plots are generated based on the data, providing visual insights.

        **Graph Generation:**
        - Specify graph generation is automatic, to specify a type mention it in query message only
        - DataDrishti uses the data to generate plots and provides recommendations for improving metrics.

        """
    )

    st.video('https://youtu.be/z1Cg5LsKw2A?si=vq4l_JfdlAuuHQZK', format="video/mp4")


#PART 2 : Chat Tab, the magic 
elif current_tab == "Chat":
    # Prompt for user input and save
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})

    if 'messages'  in st.session_state:
        # display the existing chat messages
        for message in st.session_state.messages:
            if message["role"] == "system":
                continue
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "results" in message:
                    if message["results"].empty:
                        st.write("DataFrame is empty")
                    else:
                        st.dataframe(message["results"])
                if "graph" in message:
                    st.plotly_chart(message["graph2"])

        # If the last message is not from the assistant, generate a new response
        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                response = ""
  
                resp_container = st.empty()
                for delta in client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    stream=True,
                ):
                    response += (delta.choices[0].delta.content or "")
                    resp_container.markdown(response)

                message = {"role": "assistant", "content": response}
                # Parse the response for a SQL query and execute if available
                sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)
                if sql_match:
                    sql = sql_match.group(1)
                    conn = st.connection("snowflake")
                    
                    message["results"] = conn.query(sql)
                    if message["results"].empty:
                        st.write("DataFrame is empty")
                    else:
                        st.dataframe(message["results"])

                        c2p = chat2plot(message["results"])

                        result = c2p(st.session_state.messages[-1]["content"] + "description should be one liner, also add a recommendation to improve a metric seeing data")
                        st.write(result.explanation)
                        st.plotly_chart(result.figure)
                        message["graph"] = result.figure


                st.session_state.messages.append(message)
