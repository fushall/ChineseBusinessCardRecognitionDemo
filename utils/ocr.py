import base64
from typing import List

import cv2
import numpy as np
import paddleocr
from pydantic import BaseModel, Field

pd_ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang="ch")


class Point(BaseModel):
    x: float = Field(..., description='x坐标')
    y: float = Field(..., description='y坐标')


class Box(BaseModel):
    top_left: Point = Field(..., description='左上')
    top_right: Point = Field(..., description='右上')
    bottom_left: Point = Field(..., description='左下')
    bottom_right: Point = Field(..., description='右下')


class OCRResultText(BaseModel):
    text: str = Field(..., description='识别的文本')
    box: Box = Field(..., description='框的四个坐标')


class OCRResult(BaseModel):
    texts: List[OCRResultText] = Field(..., description='ocr结果的每一行')


def ocr(img):
    result = pd_ocr.ocr(img, det=True, rec=True)
    if result is None:
        return
    texts = []
    for data in result:
        tl, tr, bl, br = data[0]
        text, accuracy = data[1]
        texts.append(OCRResultText(text=text,
                                   box=Box(top_left=Point(x=tl[0], y=tl[1]),
                                           top_right=Point(x=tr[0], y=tr[1]),
                                           bottom_left=Point(x=bl[0], y=bl[1]),
                                           bottom_right=Point(x=br[0], y=br[1]))))
    return OCRResult(texts=texts)


def ocr_from_base64(base64_img):
    bytes_img = base64.b64decode(base64_img)
    return ocr_from_bytes(bytes_img)


def ocr_from_bytes(bytes_img):
    # refer to https://www.zhihu.com/question/359416150
    np_arr = np.frombuffer(bytes_img, dtype=np.uint8)
    segment_data = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
    return ocr(segment_data)
