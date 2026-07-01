import os
from openai import AsyncOpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv
from huggingface_hub import AsyncInferenceClient

load_dotenv()

# Local LM Studio client
lm_studio = AsyncOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"  
)

# Gemini client
gemini_client = genai.Client()

# OpenAI client
openai_client = AsyncOpenAI()

# OpenRouter client
openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://github.com/your-username/law-rag", 
        "X-Title": "Law RAG System",
    }
)
# Euler client
euler_client = AsyncOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed" 
)

hf_client = AsyncInferenceClient(
    model="https://b73yejm83fw58joq.us-east-1.aws.endpoints.huggingface.cloud"
)
