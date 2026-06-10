import sys
sys.path.append("src")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from config import Config
import time

app = FastAPI()

# OpenAIクライアント初期化
client = AzureOpenAI(
    azure_endpoint=Config.OPENAI_ENDPOINT,
    api_key=Config.OPENAI_KEY,
    api_version="2024-02-01"
)

class QuestionRequest(BaseModel):
    """質問リクエストのデータ型"""
    question: str

def get_embedding(text: str) -> list[float]:
    """テキストをベクトル化する"""
    response = client.embeddings.create(
        model=Config.EMBEDDING_DEPLOYMENT,
        input=text
    )
    return response.data[0].embedding

def search_documents(query: str, embedding: list[float]) -> list[dict]:
    """AI Searchで関連ドキュメントを検索する"""
    search_client = SearchClient(
        endpoint=Config.SEARCH_ENDPOINT,
        index_name=Config.SEARCH_INDEX,
        credential=AzureKeyCredential(Config.SEARCH_KEY)
    )

    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=3,
        fields="content_vector"
    )

    results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        select=["content", "page"],
        top=3
    )

    documents = []
    for result in results:
        documents.append({
            "content": result["content"],
            "page": result["page"]
        })
    return documents

def generate_answer(query: str, documents: list[dict]) -> str:
    """検索結果を元にAIが回答を生成する"""
    context = ""
    for doc in documents:
        context += f"【ページ{doc['page']}】\n{doc['content']}\n\n"

    system_prompt = """
あなたは親切なAIアシスタントです。
提供されたドキュメントの内容を元に質問に答えてください。
ドキュメントに記載がない内容は「資料に記載がありません」と答えてください。
回答は日本語で簡潔にわかりやすく答えてください。
"""

    user_prompt = f"""
以下のドキュメントを参考に質問に答えてください。

【参考ドキュメント】
{context}

【質問】
{query}
"""

    # リトライ処理
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=Config.OPENAI_DEPLOYMENT,
                max_tokens=500,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(30)
            else:
                raise e

    return response.choices[0].message.content

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """index.htmlを返す"""
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """質問を受け取って回答を返すAPI"""
    try:
        # ① 質問をベクトル化
        embedding = get_embedding(request.question)

        # ② 関連ドキュメントを検索
        documents = search_documents(request.question, embedding)

        if not documents:
            return {
                "answer": "関連する情報が見つかりませんでした。",
                "pages": []
            }

        # ③ 回答を生成
        answer = generate_answer(request.question, documents)
        pages = [doc["page"] for doc in documents]

        return {
            "answer": answer,
            "pages": pages
        }

    except Exception as e:
        return {
            "answer": f"エラーが発生しました：{str(e)}",
            "pages": []
        }