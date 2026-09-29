from rapidocr import RapidOCR
import numpy as np
import pymupdf


class OCRService:
    def __init__(self):
        self.engine = RapidOCR()

    def recognize_page(self, page):
        # 1. 将 PDF 页面渲染成 300 DPI 图片
        pix = page.get_pixmap(
            dpi=300,
            colorspace=pymupdf.csRGB,
            alpha=False
        )

        # 2. 转换成 numpy 数组
        image = np.frombuffer(
            pix.samples,
            dtype=np.uint8
        ).reshape(
            pix.height,
            pix.width,
            pix.n
        )

        # 3. OCR 识别
        result = self.engine(image)

        # 4. 处理识别结果
        if result is None or result.txts is None:
            return {
                "text": "",
                "blocks": [],
                "avg_confidence": None
            }

        blocks = []

        for box, text, score in zip(
            result.boxes,
            result.txts,
            result.scores
        ):
            blocks.append({
                "text": text,
                "confidence": float(score),
                "bbox": box.tolist()
            })

        # 5. 生成可供 LLM 使用的文本
        full_text = "\n".join(
            block["text"] for block in blocks
        )

        scores = [
            block["confidence"] for block in blocks
        ]

        avg_confidence = (
            sum(scores) / len(scores)
            if scores else None
        )

        return {
            "text": full_text,
            "blocks": blocks,
            "avg_confidence": avg_confidence
        }