import os
import logging
from abc import ABC, abstractmethod
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseLLM(ABC):
    """Abstract base class for all LLM providers."""
    
    def __init__(self, model_name: str, api_key_env_var: str):
        self.model_name = model_name
        self.api_key = os.environ.get(api_key_env_var, "").strip()
        self._available = False
        
    @abstractmethod
    def test_connection(self) -> bool:
        pass
        
    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        pass
        
    def is_available(self) -> bool:
        return self._available

class OpenAILLM(BaseLLM):
    """Dedicated class for OpenAI models."""
    
    def __init__(self):
        model = os.environ.get("OPENAI_MODEL", "gpt-4o")
        super().__init__(model_name=model, api_key_env_var="OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not set. OpenAILLM will be unavailable.")
            return
            
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key)
        
        if os.environ.get("LLM_TEST_CONNECTION", "").lower() == "true":
            self.test_connection()
        else:
            self._available = True
            
    def test_connection(self) -> bool:
        try:
            logger.info(f"Testing OpenAI connection with model {self.model_name}...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Ping."}],
                max_tokens=10
            )
            if response.choices:
                logger.info("OpenAI connection successful.")
                self._available = True
                return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            
        self._available = False
        return False
        
    def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        if not self._available:
            return "Error: OpenAI LLM is not available."
            
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return f"Error: {str(e)}"


class GeminiLLM(BaseLLM):
    """Dedicated class for Google Gemini models using the official google-genai SDK."""
    
    def __init__(self):
        model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
        super().__init__(model_name=model, api_key_env_var="GEMINI_API_KEY")
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. GeminiLLM will be unavailable.")
            return
            
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            logger.error("google-genai package is missing. Run 'pip install google-genai'.")
            return
            
        if os.environ.get("LLM_TEST_CONNECTION", "").lower() == "true":
            self.test_connection()
        else:
            self._available = True
            
    def test_connection(self) -> bool:
        try:
            logger.info(f"Testing Gemini connection with model {self.model_name}...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents="Ping."
            )
            if response.text:
                logger.info("Gemini connection successful.")
                self._available = True
                return True
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            
        self._available = False
        return False
        
    def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        if not self._available:
            return "Error: Gemini LLM is not available."
            
        try:
            from google.genai import types
            
            config = None
            if system_prompt:
                config = types.GenerateContentConfig(
                    system_instruction=system_prompt,
                )
                
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return f"Error: {str(e)}"


class GroqLLM(BaseLLM):
    """Dedicated class for Groq models using direct API requests."""
    
    def __init__(self):
        model = os.environ.get("GROQ_MODEL", "llama3-8b-8192")
        super().__init__(model_name=model, api_key_env_var="GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set. GroqLLM will be unavailable.")
            return
            
        if os.environ.get("LLM_TEST_CONNECTION", "").lower() == "true":
            self.test_connection()
        else:
            self._available = True
            
    def test_connection(self) -> bool:
        try:
            logger.info(f"Testing Groq connection with model {self.model_name}...")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "Ping."}],
                "max_tokens": 10
            }
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Groq connection successful.")
            self._available = True
            return True
        except Exception as e:
            logger.error(f"Groq connection test failed: {e}")
            
        self._available = False
        return False
        
    def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        if not self._available:
            return "Error: Groq LLM is not available."
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq generation error: {e}")
            return f"Error: {str(e)}"


class LLMService:
    """Service to manage LLMs and handle fallback logic."""
    
    def __init__(self):
        self.providers = {
            "openai": OpenAILLM(),
            "gemini": GeminiLLM(),
            "groq": GroqLLM()
        }
        self.priority = ["gemini", "openai", "groq"]
        
    def get_available_provider(self, preferred: str = None) -> BaseLLM:
        if preferred and preferred in self.providers and self.providers[preferred].is_available():
            logger.info(f"Using preferred provider: {preferred}")
            return self.providers[preferred]
            
        for provider_name in self.priority:
            if provider_name != preferred and self.providers[provider_name].is_available():
                logger.info(f"Falling back to provider: {provider_name}")
                return self.providers[provider_name]
                
        logger.error("No LLM providers are available.")
        return None

    def generate_answer(self, query: str, context: str = "", preferred_provider: str = None) -> str:
        provider = self.get_available_provider(preferred_provider)
        
        if not provider:
            return "Error: No AI models are currently available. Please check your API keys."
            
        system_prompt = (
            "You are a helpful AI assistant. "
            "Use the provided context to answer the user's query. "
            "If the answer is not in the context, use your general knowledge but mention it."
        )
        
        full_prompt = f"Context: {context}\n\nQuery: {query}" if context else query
        
        return provider.generate_response(full_prompt, system_prompt)