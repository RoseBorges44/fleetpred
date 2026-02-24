import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.normpath(os.path.join(_dir, ".."))

load_dotenv(os.path.join(_backend_dir, ".env"))


def get_llm(temperature=0.2):
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=temperature,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )


def load_prompt(nome: str) -> str:
    path = os.path.join(_backend_dir, "prompts", f"{nome}.txt")
    with open(path, encoding="utf-8") as f:
        return f.read()
