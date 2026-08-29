import os
import sys

# Add app/scripts directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "app", "services"))

from dotenv import load_dotenv
from llm import LLMService

# Load environment variables
load_dotenv()


def main():
    logger_service = LLMService()

    print("\n--- Testing LLM Service ---\n")

    query = "Explain in one sentence what a vector database is."
    print(f"Query: {query}\n")

    response = logger_service.generate_answer(
        query=query, preferred_provider="gemini"
    )

    print("--- Provider Response ---")
    print(response)


if __name__ == "__main__":
    main()