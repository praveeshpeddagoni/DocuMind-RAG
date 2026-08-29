import os


import sys
import importlib.metadata
from unittest.mock import MagicMock

# 1. Bypass tiktoken C-extension security block
fake_tiktoken = MagicMock()
sys.modules["tiktoken"] = fake_tiktoken
sys.modules["tiktoken._tiktoken"] = fake_tiktoken

# 2. Updated metadata patch to satisfy transformers version bounds
original_version = importlib.metadata.version

def patched_version(distribution_name):
    mock_versions = {
        "huggingface_hub": "1.20.0",
        "huggingface-hub": "1.20.0",
        "tokenizers": "0.23.1",
        "protobuf": "4.25.3",
        "google-protobuf": "4.25.3",
    }
    if distribution_name in mock_versions:
        return mock_versions[distribution_name]
    try:
        ver = original_version(distribution_name)
        return ver if ver is not None else "1.20.0"
    except Exception:
        return "1.20.0"

importlib.metadata.version = patched_version

import warnings
import ast
import pandas as pd
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper




# 1. Initialization & Setup
load_dotenv()
warnings.filterwarnings("ignore", category=DeprecationWarning)
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Helper function to reliably extract text from any response format
def extract_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    text_parts.append(str(item["text"]))
                elif "content" in item:
                    text_parts.append(str(item["content"]))
                else:
                    for k, v in item.items():
                        if isinstance(v, str):
                            text_parts.append(v)
            elif hasattr(item, "text"):
                text_parts.append(str(item.text))
            else:
                text_parts.append(str(item))
        return "".join(text_parts)
    return str(content)

# 2. Load documents and build local vector retriever using local HuggingFace embeddings
print("Setting up local RAG retriever with HuggingFace embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", google_api_key=api_key)

loader = PyPDFDirectoryLoader("./data/documents/")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)

vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 3. Load synthetic test dataset
df = pd.read_csv("synthetic_eval_dataset.csv")
if "reference_contexts" in df.columns:
    df["reference_contexts"] = df["reference_contexts"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

print(f"Loaded {len(df)} test questions. Running direct RAG execution loop...")

# 4. Generate runtime responses and retrieved contexts manually
responses = []
retrieved_contexts_list = []

for idx, row in df.iterrows():
    query = row["user_input"]
    
    retrieved_docs = retriever.invoke(query)
    contexts = [doc.page_content for doc in retrieved_docs]
    retrieved_contexts_list.append(contexts)
    
    context_text = "\n\n".join(contexts)
    prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know, say that you don't know.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {query}"
    )
    
    ai_msg = llm.invoke(prompt)
    clean_content = extract_text(ai_msg.content)
    responses.append(clean_content)

df["response"] = responses
df["retrieved_contexts"] = retrieved_contexts_list

hf_dataset = Dataset.from_pandas(df)

# 5. Configure Ragas evaluation wrappers with gemini-3.5-flash-lite
eval_llm = LangchainLLMWrapper(ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", google_api_key=api_key))
eval_embeddings = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"))

metrics = [
    Faithfulness(),
    AnswerRelevancy(),
    ContextPrecision(),
    ContextRecall(),
]

# 6. Run Evaluation
print("Running Ragas evaluation pipeline...")
result = evaluate(
    dataset=hf_dataset,
    metrics=metrics,
    llm=eval_llm,
    embeddings=eval_embeddings
)

eval_df = result.to_pandas()
eval_df.to_csv("rag_evaluation_report.csv", index=False)

print("\nEvaluation successfully finished and saved to 'rag_evaluation_report.csv'!")
print(result)