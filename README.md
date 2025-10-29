# Chat-with-PDF

A Streamlit web application that allows users to upload a PDF, extract its content using Azure Form Recognizer, store the extracted data in ChromaDB, and interact with the document using OpenAI's GPT models.

## Features

- Upload any PDF and extract structured text and tables using Azure Form Recognizer.
- Store extracted content in a ChromaDB vector database for semantic search.
- Query your document using natural language.
- Context-aware responses using OpenAI GPT models.
- Session-based conversation memory in Streamlit.

## Tech Stack

- **Frontend:** Streamlit  
- **Backend:** Python  
- **AI/ML APIs:**  
  - Azure Form Recognizer  
  - OpenAI API (GPT models)  
- **Database:** ChromaDB (for vector embeddings)

## Setup Instructions

1. Clone the Repository
```bash
git clone https://github.com/aasthass/chat-with-pdf.git
cd chat-with-pdf

2. Create and Activate Virtual Environment
python3 -m venv venv
source venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt

4. Environment Variables
Create a .env file in the root directory and add:
AZURE_COGNITIVE_ENDPOINT=your_azure_endpoint
AZURE_API_KEY=your_azure_api_key
OPENAI_API_KEY=your_openai_api_key

5. Run the App
streamlit run main.py

6. Access the Application
Go to http://localhost:8501 in your browser.
Project Structure
chat-with-pdf/
│
├── main.py               # Main Streamlit application
├── requirements.txt      # Python dependencies
├── .gitignore            # Ignored files and folders
└── .env.example          # Example environment variable file

How It Works
Upload a PDF — the app sends it to Azure Form Recognizer (prebuilt-document model).
Text and tables are extracted into structured data.
ChromaDB stores OpenAI embeddings (text-embedding-ada-002) for each text chunk.
When you ask a question, the most relevant sections are retrieved.
GPT-4 generates an answer using the retrieved content.
