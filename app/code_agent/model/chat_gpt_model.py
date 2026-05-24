from langchain_openai import ChatOpenAI
import os

from dotenv import load_dotenv

load_dotenv()

llm_gpt = ChatOpenAI(
    model="gpt-4o-mini",
    api_key = os.environ["OPENAI_API_KEY"],
    streaming=True
)