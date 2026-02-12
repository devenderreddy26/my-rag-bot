# Teams RAG Bot with Azure AI Search, APIM & Arize Tracing

This project implements a **Retrieval-Augmented Generation (RAG)** chatbot for Microsoft Teams. It allows users to ask questions about their own data stored in an Azure AI Search Vector Index.

### Key Features
* **Multi-Turn Conversations:** Supports follow-up questions (e.g., "How much is it?") using query rewriting.
* **Integrated Vectorization:** Uses Azure AI Search's server-side vectorization (no local embedding model needed).
* **APIM Integration:** Connects to Azure OpenAI via Azure API Management for security and governance.
* **Full Observability:** Sends detailed traces (Input -> Search -> LLM -> Output) to **Arize Phoenix** using OpenTelemetry.
* **Volatile Memory:** Uses short-term RAM memory for session context (no database required).

---

## 📋 Prerequisites

Before running, ensure you have the following Azure resources:

1.  **Azure AI Search:** An index with a vector profile configured.
2.  **Azure OpenAI (via APIM):** An API Management endpoint proxying your OpenAI resource.
3.  **Azure Bot Resource:** A "Multi-Tenant" or "Single-Tenant" Bot handle.
4.  **Arize Phoenix:** An account (hosted) or a local collector running.
5.  **Python 3.10+** installed locally.

---

## 🛠️ Local Setup

### 1. Clone/Setup Folder
Create a folder and place the provided files (`app.py`, `bot.py`, `config.py`, `requirements.txt`) inside.

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
