import streamlit as st
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from tabulate import tabulate
from chromadb.utils import embedding_functions
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
import os

# --------------------------------------------------------------------
# 🔹 Load environment variables
# --------------------------------------------------------------------
load_dotenv()

AZURE_COGNITIVE_ENDPOINT = os.getenv("AZURE_COGNITIVE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client (new API)
client_openai = OpenAI(api_key=OPENAI_API_KEY)

# --------------------------------------------------------------------
# 🔹 Initialize ChromaDB client
# --------------------------------------------------------------------
chroma_client = chromadb.Client()
chroma_client.heartbeat()

st.write("# 📄 Chat with PDF")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Save PDF temporarily
    with open("temp_pdf_file.pdf", "wb") as temp_file:
        temp_file.write(uploaded_file.read())

    # Initialize Azure Form Recognizer
    credential = AzureKeyCredential(AZURE_API_KEY)
    document_client = DocumentAnalysisClient(AZURE_COGNITIVE_ENDPOINT, credential)

    with open("temp_pdf_file.pdf", "rb") as f:
        poller = document_client.begin_analyze_document("prebuilt-document", document=f)
        doc_info = poller.result().to_dict()

    res = []
    CONTENT = "content"
    PAGE_NUMBER = "page_number"
    TYPE = "type"
    RAW_CONTENT = "raw_content"
    TABLE_CONTENT = "table_content"

    # Extract raw text
    for p in doc_info.get("pages", []):
        data_dict = {}
        page_content = " ".join([line["content"] for line in p.get("lines", [])])
        data_dict[CONTENT] = str(page_content)
        data_dict[PAGE_NUMBER] = str(p["page_number"])
        data_dict[TYPE] = RAW_CONTENT
        res.append(data_dict)

    # Extract tables
    for table in doc_info.get("tables", []):
        data_dict = {}
        data_dict[PAGE_NUMBER] = str(table["bounding_regions"][0]["page_number"])
        col_headers = []
        cells = table["cells"]

        for cell in cells:
            if cell["kind"] == "columnHeader" and cell["column_span"] == 1:
                col_headers.append(cell["content"])

        data_rows = [[] for _ in range(table["row_count"])]
        for cell in cells:
            if cell["kind"] == "content":
                data_rows[cell["row_index"]].append(cell["content"])

        data_rows = [row for row in data_rows if len(row) > 0]
        markdown_table = tabulate(data_rows, headers=col_headers, tablefmt="pipe")
        data_dict[CONTENT] = markdown_table
        data_dict[TYPE] = TABLE_CONTENT
        res.append(data_dict)

    # Reset ChromaDB collection
    try:
        chroma_client.delete_collection(name="my_collection")
        st.session_state.messages = []
    except Exception:
        pass

    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY, model_name="text-embedding-ada-002"
    )
    collection = chroma_client.create_collection(
        name="my_collection", embedding_function=openai_ef
    )

    # Add extracted data to ChromaDB
    id = 1
    for d in res:
        content = d.get(CONTENT, "")
        page_number = d.get(PAGE_NUMBER, "")
        type_of_content = d.get(TYPE, "")

        content_metadata = {
            PAGE_NUMBER: page_number,
            TYPE: type_of_content,
        }

        collection.add(
            documents=[content],
            metadatas=[content_metadata],
            ids=[str(id)],
        )
        id += 1

# --------------------------------------------------------------------
# 🔹 Streamlit Chat Section
# --------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("💬 What do you want to ask your PDF?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Query ChromaDB for relevant context
    q = collection.query(query_texts=[prompt], n_results=5)
    results = q["documents"][0]

    prompts = []
    for r in results:
        full_prompt = (
            "Please extract the following: "
            + prompt
            + " solely based on the text below. "
            + "Use an unbiased and journalistic tone. "
            + "If you're unsure of the answer, say you cannot find the answer.\n\n"
            + r
        )
        prompts.append(full_prompt)

    prompts.reverse()

    # New OpenAI API call
    response_obj = client_openai.chat.completions.create(
        model="gpt-4o-mini",  # lighter & faster, or use gpt-4-turbo
        messages=[{"role": "user", "content": p} for p in prompts],
        temperature=0,
    )

    response = response_obj.choices[0].message.content

    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
