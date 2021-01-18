import base64
import logging

import fastapi
import pydantic
import uvicorn
from kafka import KafkaProducer, KafkaConsumer

import setting
from cbcr import CBCRTask
from utils.card_recg import extract_card_info_from_pd_ocr, CardInfo
from utils.ocr import ocr_from_bytes, ocr_from_base64

logger = logging.getLogger(__name__)
app = fastapi.FastAPI()
router = fastapi.APIRouter()
debug_router = fastapi.APIRouter()


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


@debug_router.post('/send')
async def debug_send_task(task_id: int = fastapi.Form(10000),
                          method: str = fastapi.Form('cardRecognition/名片识别'),
                          content_type: str = fastapi.Form('image/jpeg'),
                          file_name: str = fastapi.Form('测试.jpg', ),
                          compress: int = fastapi.Form(1600),
                          image: fastapi.UploadFile = fastapi.File(...),
                          topic: str = fastapi.Form(setting.KAFKA_CONSUMER_TOPIC),
                          ):
    image = await image.read()
    task = CBCRTask(id=task_id,
                    method=method,
                    bytes=base64.b64encode(image),
                    contentType=content_type,
                    fileName=file_name,
                    size=len(image),
                    compress=compress)
    producer = KafkaProducer(bootstrap_servers=[setting.KAFKA_HOST])
    future = producer.send(topic=topic or setting.KAFKA_PRODUCER_TOPIC, value=task.json().encode())
    result = future.get(500)
    retval = result._asdict()
    retval['topic_partition'] = retval['topic_partition']._asdict()
    producer.close()
    return retval


@debug_router.get('/recv')
def debug_recv_task(topic: str = fastapi.Query('')):
    consumer = KafkaConsumer(topic or setting.KAFKA_CONSUMER_TOPIC,
                             bootstrap_servers=[setting.KAFKA_HOST],
                             consumer_timeout_ms=1000 * 12,
                             )
    result = {'msg': 'no tasks'}
    for msg in consumer:
        result = msg._asdict()
        break
    consumer.close()
    return result


app.include_router(router, prefix='/api')
app.include_router(debug_router, prefix='/debug')

if __name__ == '__main__':
    logger.info('web server running...')
    uvicorn.run("web:app", host='0.0.0.0', port=8080)
