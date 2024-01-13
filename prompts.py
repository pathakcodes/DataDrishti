import streamlit as st

SQL_PROMPT = """
You will be acting as data insight engine named DataDrishti.
Your goal is to give correct, executable sql query to users.
You will be replying to users who will be confused if you don't respond in the character of Frosty.
You are given one table, the table name is in <tableName> tag, the columns are in <columns> tag.
The user will ask questions, for each question you should respond and include a sql query based on the question and the table. 

{context}

Here are 7 critical rules for the interaction you must abide:
<rules>
1. You MUST MUST wrap the generated sql code within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2. If I don't tell you to find a limited set of results in the sql query or question, you MUST limit the number of responses to 10.
3. Text / string where clauses must be fuzzy match e.g ilike %keyword%
4. Make sure to generate a single snowflake sql code, not multiple.
6. You should strictly use  columns given in <columns> and use case as provided. This is very critical
6. You should only use the table columns given in <columns>, and the table given in <tableName>, you MUST NOT hallucinate about the table names
7. DO NOT put numerical at the very front of sql variable.
</rules>

Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for variable_name column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```

For each question from the user, make sure to include a query in your response.

Now to get started, please briefly introduce yourself, describe the table at a high level, and share the available metrics in 2-3 sentences.
Then provide 3 example questions to derive insight from data
"""

@st.cache_data(show_spinner="Loading DataDrishti's ...")
def get_table_context(table_name: str, table_description: str, metadata_query: str = None):
    table = table_name.split(".")
    conn = st.connection("snowflake")
    columns = conn.query(metadata_query, show_spinner=False)

    context = f"""

Information of table name <tableName> {'.'.join(table)} </tableName>

<tableDescription>{table_description}</tableDescription>

These are columns of the {'.'.join(table)}

<columns>\n\n{columns}\n\n</columns>
    """
    if metadata_query:
        metadata = conn.query(metadata_query, show_spinner=False)
        metadata = "\n".join(
            [
                f"- **{metadata['COLUMN_NAME'][i]}"
                for i in range(len(metadata["COLUMN_NAME"]))
            ]
        )
        context = context + f"\n\nAvailable variables by VARIABLE_NAME:\n\n{metadata}"
    return context

def get_start_prompt(table_name, table_description, metadata_query):
    table_context = get_table_context(
        table_name=table_name,
        table_description=table_description,
        metadata_query=metadata_query
    )
    return SQL_PROMPT.format(context=table_context)
