import sys
sys.path.append("src")

from azure.storage.blob import BlobServiceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchField as VectorField,
)
from openai import AzureOpenAI
from config import Config
import os

def upload_pdf_to_blob(pdf_path: str) -> str:
    """PDFをBlob Storageにアップロードする"""
    print("📤 PDFをBlob Storageにアップロード中...")

    # Blob Storageに接続
    blob_service_client = BlobServiceClient.from_connection_string(
        Config.STORAGE_CONNECTION_STRING
    )

    # コンテナ作成（なければ自動作成）
    container_name = "documents"
    try:
        blob_service_client.create_container(container_name)
        print(f"✅ コンテナ作成：{container_name}")
    except Exception:
        print(f"✅ コンテナ既存：{container_name}")

    # PDFをアップロード
    blob_name = os.path.basename(pdf_path)
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_name
    )

    with open(pdf_path, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)

    print(f"✅ アップロード完了：{blob_name}")
    return blob_client.url


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """Document IntelligenceでPDFからテキストを抽出する"""
    print("📄 PDFからテキストを抽出中...")

    # Document Intelligenceに接続
    doc_client = DocumentAnalysisClient(
        endpoint=Config.DOCINTEL_ENDPOINT,
        credential=AzureKeyCredential(Config.DOCINTEL_KEY)
    )

    # PDFを解析
    with open(pdf_path, "rb") as f:
        poller = doc_client.begin_analyze_document("prebuilt-read", f)
    result = poller.result()

    # ページごとにテキストを抽出
    chunks = []
    for i, page in enumerate(result.pages):
        page_text = ""
        for line in page.lines:
            page_text += line.content + "\n"

        if page_text.strip():
            chunks.append({
                "id": f"page_{i+1}",
                "content": page_text,
                "page": i + 1
            })
            print(f"✅ ページ{i+1}抽出完了")

    return chunks


def create_search_index():
    """AI Searchのインデックスを作成する"""
    print("🔍 AI Searchインデックスを作成中...")

    index_client = SearchIndexClient(
        endpoint=Config.SEARCH_ENDPOINT,
        credential=AzureKeyCredential(Config.SEARCH_KEY)
    )

    # インデックスの定義
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="page", type=SearchFieldDataType.Int32),
        VectorField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="myHnswProfile"
        )
    ]

    # ベクトル検索の設定
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="myHnsw")],
        profiles=[VectorSearchProfile(
            name="myHnswProfile",
            algorithm_configuration_name="myHnsw"
        )]
    )

    # インデックス作成
    index = SearchIndex(
        name=Config.SEARCH_INDEX,
        fields=fields,
        vector_search=vector_search
    )

    try:
        index_client.create_index(index)
        print(f"✅ インデックス作成完了：{Config.SEARCH_INDEX}")
    except Exception:
        print(f"✅ インデックス既存：{Config.SEARCH_INDEX}")


def vectorize_and_upload(chunks: list[dict]):
    """テキストをベクトル化してAI Searchに保存する"""
    print("🔢 テキストをベクトル化中...")

    # OpenAIクライアント
    openai_client = AzureOpenAI(
        azure_endpoint=Config.OPENAI_ENDPOINT,
        api_key=Config.OPENAI_KEY,
        api_version="2024-02-01"
    )

    # AI Searchクライアント
    search_client = SearchClient(
        endpoint=Config.SEARCH_ENDPOINT,
        index_name=Config.SEARCH_INDEX,
        credential=AzureKeyCredential(Config.SEARCH_KEY)
    )

    # 各チャンクをベクトル化
    documents = []
    for chunk in chunks:
        # テキストをベクトル化
        response = openai_client.embeddings.create(
            model=Config.EMBEDDING_DEPLOYMENT,
            input=chunk["content"]
        )
        vector = response.data[0].embedding

        documents.append({
            "id": chunk["id"],
            "content": chunk["content"],
            "page": chunk["page"],
            "content_vector": vector
        })
        print(f"✅ ページ{chunk['page']}ベクトル化完了")

    # AI Searchに保存
    search_client.upload_documents(documents)
    print(f"✅ AI Searchへの保存完了：{len(documents)}件")


def main():
    """メイン処理"""
    pdf_path = "data/sample.pdf"

    # 設定値確認
    Config.validate()

    # ① PDFをBlob Storageにアップロード
    upload_pdf_to_blob(pdf_path)

    # ② PDFからテキスト抽出
    chunks = extract_text_from_pdf(pdf_path)

    # ③ AI Searchインデックス作成
    create_search_index()

    # ④ ベクトル化してAI Searchに保存
    vectorize_and_upload(chunks)

    print("\n🎉 インデックス作成完了！")
    print("次はchatbot.pyで質問できます！")


if __name__ == "__main__":
    main()