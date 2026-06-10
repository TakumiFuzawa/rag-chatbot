import sys
sys.path.append("src")

from openai import AzureOpenAI
from config import Config

def test_openai_connection():
    """Azure OpenAI 接続テスト"""
    Config.validate()

    client = AzureOpenAI(
        azure_endpoint=Config.OPENAI_ENDPOINT,
        api_key=Config.OPENAI_KEY,
        api_version="2024-02-01"
    )

    response = client.chat.completions.create(
        model=Config.OPENAI_DEPLOYMENT,
        max_tokens=100,
        messages=[
            {"role": "system", "content": "日本語で短く答えてください。"},
            {"role": "user", "content": "こんにちは。接続テストです。一言で答えてください。"}
        ]
    )

    print("✅ Azure OpenAI 接続成功！")
    print(f"モデル: {response.model}")
    print(f"回答: {response.choices[0].message.content}")
    print(f"使用トークン: {response.usage.total_tokens}")

if __name__ == "__main__":
    test_openai_connection()