import os
import random
import warnings
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.testset import TestsetGenerator

load_dotenv()
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

def load_sampled_pdf_chunks(directory_path, pages_per_pdf=5):
    sampled_docs = []
    
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)
        return sampled_docs

    for file in os.listdir(directory_path):
        if file.endswith(".pdf"):
            full_path = os.path.join(directory_path, file)
            reader = PdfReader(full_path)
            total_pages = len(reader.pages)
            
            # Sample random pages per PDF
            selected_pages = random.sample(
                range(total_pages), min(pages_per_pdf, total_pages)
            )
            
            for page_num in selected_pages:
                text = reader.pages[page_num].extract_text() or ""
                if text.strip():
                    sampled_docs.append(
                        Document(
                            page_content=text,
                            metadata={"filename": file, "page": page_num + 1}
                        )
                    )
    return sampled_docs

def generate_dataset():
    docs_dir = "./data/documents/"  
    
    print("Loading PDF document chunks...")
    documents = load_sampled_pdf_chunks(docs_dir, pages_per_pdf=5)
    
    if not documents:
        print(f"No PDF documents found in '{docs_dir}'. Please place your PDFs there.")
        return

    print(f"Loaded {len(documents)} total page chunks across all PDFs.")

    # 1. Initialize Gemini 3.5 Flash-Lite & Embeddings wrapped for Ragas
    llm_instance = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    embeddings_instance = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

    generator_llm = LangchainLLMWrapper(llm_instance)
    generator_embeddings = LangchainEmbeddingsWrapper(embeddings_instance)

    # 2. Instantiate Ragas TestsetGenerator with Gemini 3.5 Flash-Lite
    generator = TestsetGenerator(
        llm=generator_llm,
        embedding_model=generator_embeddings
    )

    # 3. Generate Synthetic Test Dataset directly from pre-chunked docs
    print("Generating 10 synthetic test questions using Gemini 3.5 Flash-Lite...")
    testset = generator.generate_with_chunks(
        chunks=documents,
        testset_size=10
    )

    # 4. Export to CSV
    df = testset.to_pandas()
    df.to_csv("synthetic_eval_dataset.csv", index=False)
    print("\nSuccessfully generated dataset saved to 'synthetic_eval_dataset.csv'!")

if __name__ == "__main__":
    generate_dataset()