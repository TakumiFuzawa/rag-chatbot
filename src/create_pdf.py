from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

def create_pdf(input_txt, output_pdf):
    """テキストファイルをPDFに変換する"""

    # 日本語フォント登録
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))

    # PDF作成
    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4

    # フォント設定
    c.setFont('HeiseiKakuGo-W5', 11)

    # テキスト読み込み
    with open(input_txt, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 描画設定
    x = 40
    y = height - 50
    line_height = 18

    for line in lines:
        line = line.rstrip('\n')

        # ページをまたぐ場合は新しいページへ
        if y < 50:
            c.showPage()
            c.setFont('HeiseiKakuGo-W5', 11)
            y = height - 50

        c.drawString(x, y, line)
        y -= line_height

    c.save()
    print(f"✅ PDF作成完了：{output_pdf}")

if __name__ == "__main__":
    create_pdf(
        input_txt="data/sample.txt",
        output_pdf="data/sample.pdf"
    )