import os
from ai_providers.groq import call_groq
from ai_providers.open_ai import call_openai

def get_llm():
    llm_provider = os.getenv("LLM_PROVIDER")
    if llm_provider == "groq":
        return call_groq
    
    return call_openai