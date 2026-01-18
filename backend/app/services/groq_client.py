from langchain_groq import ChatGroq
from app.core.config import settings

def get_llm(purpose: str = "extract"):
    """
    purpose:
      - "extract": field extraction + intent detection
      - "tools": suggestions + compliance (fast)
    """
    model = settings.EXTRACT_MODEL if purpose == "extract" else settings.TOOL_MODEL

    return ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name=model,
        temperature=0.2,
    )
