# Nyaya AI: RAG for Indian Law

Nyaya AI is an advanced Legal Assistant powered by Retrieval-Augmented Generation (RAG) designed to answer questions regarding Indian Law, including the Indian Constitution, Bharatiya Nagarik Suraksha Sanhita (BNSS), IT Act, and more. 

The application utilizes an advanced AI Engine backed by a dynamic vector database to fetch relevant legal excerpts and cite sources accurately alongside its generated responses.

## Features

- **Conversational UI**: A clean, premium dark-mode chat interface to ask complex legal queries.
- **Dynamic RAG System**: The AI retrieves highly relevant sections, articles, and chapters from Indian legal documents to ground its answers.
- **Source Citation**: Transparently displays the legal sources used for each response, including matching scores and exact excerpts.
- **Knowledge Base Management**: An intuitive sidebar to monitor document ingestion stats and directly upload new PDF documents to the vector database.
- **Fast & Responsive**: Built with Next.js and FastAPI for a seamless experience.

## Architecture

- **Frontend**: Next.js / React (styled with custom CSS for a premium aesthetic)
- **Backend**: Python, FastAPI
- **AI Engine**: Groq Llama 3.3 70B (Configurable)
- **Vector Database**: ChromaDB

## Prerequisites

- Node.js (v18+)
- Python 3.9+
- Groq API Key

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/SHREYASH-W/RAG-FOR-INDIAN-LAW.git
cd RAG-FOR-INDIAN-LAW
```

### 2. Backend Setup

Navigate to the `backend` directory and set up the Python environment.

```bash
cd backend
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies (assuming you have a requirements.txt or manually install)
pip install fastapi uvicorn chromadb ...
```

Create a `.env` file in the `backend` directory and add your API keys:

```
GROQ_API_KEY=your_groq_api_key
```

Run the FastAPI server:

```bash
python -m uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

Open a new terminal, navigate to the `frontend` directory.

```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:3000`.

## Usage

1. Open `http://localhost:3000` in your browser.
2. Use the left sidebar to upload PDF documents of Indian laws, acts, or cases to index them into the knowledge base.
3. Start asking questions in the chat interface. The engine will retrieve the most relevant sections from your ingested PDFs and provide a well-structured, cited answer.

## Disclaimer

Nyaya AI is an AI assistant and can make mistakes. The information provided should not be considered professional legal advice. Always verify with original legal texts or consult a qualified legal professional.
