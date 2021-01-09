import logging

import fastapi
import pydantic
import uvicorn

from utils.card_recg import extract_card_info_from_pd_ocr, CardInfo
from utils.ocr import ocr_from_bytes, ocr_from_base64

logger = logging.getLogger(__name__)
app = fastapi.FastAPI()
router = fastapi.APIRouter()


class CBCRImage(pydantic.BaseModel):
    base64_image: str = pydantic.Field(..., description='base64 format image')


@router.post('/base64', response_model=CardInfo)
async def get_result_from_base64(image: CBCRImage):
    ocr_result = ocr_from_base64(image.base64_image)
    business_card_info = extract_card_info_from_pd_ocr(ocr_result)
    return business_card_info


@router.post('/image', response_model=CardInfo)
async def get_result_from_image(image: fastapi.UploadFile = fastapi.File(..., description='business card image')):
    ocr_result = ocr_from_bytes(await image.read())
    business_card_info = extract_card_info_from_pd_ocr(ocr_result)
    return business_card_info


app.include_router(router, prefix='/api')

if __name__ == '__main__':
    logger.info('web server running...')
    uvicorn.run("web:app", host='0.0.0.0', port=8080)
