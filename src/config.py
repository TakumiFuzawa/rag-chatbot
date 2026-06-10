import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Azure OpenAI
    OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

    # Azure AI Search
    SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
    SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
    SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "rag-index")

    # Document Intelligence
    DOCINTEL_ENDPOINT = os.getenv("DOCINTEL_ENDPOINT")
    DOCINTEL_KEY = os.getenv("DOCINTEL_KEY")
    # Azure Blob Storage
    STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    @classmethod
    def validate(cls):
        """必須キーが揃っているか確認"""
        missing = []
        for key in ["OPENAI_ENDPOINT", "OPENAI_KEY", "SEARCH_ENDPOINT", "SEARCH_KEY"]:
            if not getattr(cls, key):
                missing.append(key)
        if missing:
            raise ValueError(f"❌ .envに未設定の項目があります: {missing}")
        print("✅ 設定値の確認OK")