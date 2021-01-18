import json
import logging

import kafka
from pydantic import BaseModel, Field

import setting
from utils.card_recg import extract_card_info_from_pd_ocr
from utils.ocr import ocr_from_base64

logger = logging.getLogger(__name__)


class CBCRResultPhoto(BaseModel):
    value: str = Field(None, description='base64')
    contentType: str = Field(None, description='图片类型')
    position: list = Field(None, description='文字框框的位置')


class CBCRResultName(BaseModel):
    value: str = Field(None, description='姓名')
    position: list = Field(None, description='文字框框的位置')


class CBCRResultTitle(BaseModel):
    value: str = Field(None, description='职位')
    position: list = Field(None, description='文字框框的位置')


class CBCRResultEmail(BaseModel):
    value: str = Field(None, description='电子邮件')
    position: list = Field(None, description='文字框框的位置')


class CBCRResultPhone(BaseModel):
    value: str = Field(None, description='电话')
    position: list = Field(None, description='文字框框的位置')


class CBCRResultLocation(BaseModel):
    value: str = Field(None, description='地址')
    position: list = Field(None, description='文字框框的位置')


class CBCRResultOrganization(BaseModel):
    value: str = Field(None, description='地址')
    position: list = Field(None, description='文字框框的位置')


class CBCRTaskResultData(BaseModel):
    task_id: int = Field(..., description='任务id')
    photo: CBCRResultPhoto = Field(..., description='头像')
    name: CBCRResultName = Field(..., description='人名')
    title: CBCRResultTitle = Field(..., description='职位')
    email: CBCRResultEmail = Field(..., description='电子邮件')
    phone: CBCRResultPhone = Field(..., description='职位')
    location: CBCRResultLocation = Field(..., description='位置')
    organization: CBCRResultOrganization = Field(..., description='组织机构')


class CBCRResult(BaseModel):
    name: CBCRResultName = Field(..., description='人名')
    title: CBCRResultTitle = Field(..., description='职位')
    email: CBCRResultEmail = Field(..., description='电子邮件')
    phone: CBCRResultPhone = Field(..., description='职位')
    location: CBCRResultLocation = Field(..., description='位置')
    organization: CBCRResultOrganization = Field(..., description='组织机构')


class CBCRTaskResult(BaseModel):
    code: str = Field(..., description='200代表成功，否则为失败')
    message: str = Field(..., description='code对应的消息')
    data: CBCRTaskResultData = Field(..., description='结果数据')


class CBCRTask(BaseModel):
    id: int = Field(..., description='任务id')
    method: str = Field(..., description='任务类型')
    bytes: str = Field(..., description='图片')
    contentType: str = Field(..., description='内容类型')
    fileName: str = Field(..., description='文件名')
    size: int = Field(..., description='文件大小')
    compress: int = Field(..., description='压缩率')


def make_photo_data(business_card_info):
    return CBCRResultPhoto()


def fit_position(box):
    # return [box.top_left.x, box.top_left.y, box.bottom_right.x, box.bottom_right.y]
    return [[box.top_left.x, box.top_left.y],
            [box.top_right.x, box.top_right.y],
            [box.bottom_left.x, box.bottom_left.y],
            [box.bottom_right.x, box.bottom_right.y]]


def make_name_data(business_card_info):
    if business_card_info.name:
        return CBCRResultName(value=business_card_info.name[0].value,
                              position=fit_position(business_card_info.name[0].box))
    else:
        return CBCRResultName()


def make_title_data(business_card_info):
    if business_card_info.title:
        return CBCRResultTitle(value=business_card_info.title[0].value,
                               position=fit_position(business_card_info.title[0].box))
    else:
        return CBCRResultTitle()


def make_email_data(business_card_info):
    if business_card_info.email:
        return CBCRResultEmail(value=business_card_info.email[0].value,
                               position=fit_position(business_card_info.email[0].box))
    else:
        return CBCRResultEmail()


def make_phone_data(business_card_info):
    if business_card_info.phone:
        return CBCRResultPhone(value=business_card_info.phone[0].value,
                               position=fit_position(business_card_info.phone[0].box))
    else:
        return CBCRResultPhone()


def make_location_data(business_card_info):
    if business_card_info.location:
        return CBCRResultLocation(value=business_card_info.location[0].value,
                                  position=fit_position(business_card_info.location[0].box))
    else:
        return CBCRResultLocation()


def make_organization_data(business_card_info):
    if business_card_info.organization:
        return CBCRResultOrganization(value=business_card_info.organization[0].value,
                                      position=fit_position(business_card_info.organization[0].box))
    else:
        return CBCRResultOrganization()


def ocr_task_result(task_id, code, message, ocr_result):
    task_data = CBCRTaskResultData(task_id=task_id,
                                   **ocr_result)
    task_result = CBCRTaskResult(code=code,
                                 message=message,
                                 data=task_data)
    return task_result


class CBCRService:
    def __init__(self, hosts=setting.KAFKA_HOST):
        self.kafka_consumer = kafka.KafkaConsumer(setting.KAFKA_CONSUMER_TOPIC, bootstrap_servers=[hosts])
        self.kafka_producer = kafka.KafkaProducer(bootstrap_servers=[hosts])

    def run(self):
        logger.info('Chinese Business Card Recognition Service Listening...')
        for msg in self.kafka_consumer:
            try:
                self.handle_msg(msg)
                continue
            except Exception as e:
                self.kafka_producer.send(setting.KAFKA_PRODUCER_TOPIC,
                                         json.dumps({"code": "500", 'message': str(e)}).encode())

    def handle_msg(self, msg):
        task = CBCRTask(**json.loads(msg.value.decode()))
        self.ocr(task)

    def ocr(self, task):
        ocr_result = ocr_from_base64(task.bytes)
        business_card_info = extract_card_info_from_pd_ocr(ocr_result)
        task_result = CBCRTaskResult(code="200",
                                     message="名片识别成功",
                                     data=CBCRTaskResultData(task_id=task.id,
                                                             photo=make_photo_data(business_card_info),
                                                             name=make_name_data(business_card_info),
                                                             title=make_title_data(business_card_info),
                                                             email=make_email_data(business_card_info),
                                                             phone=make_phone_data(business_card_info),
                                                             location=make_location_data(business_card_info),
                                                             organization=make_organization_data(business_card_info),
                                                             ))
        data = task_result.json().encode()
        self.kafka_producer.send(setting.KAFKA_PRODUCER_TOPIC, data)


if __name__ == '__main__':
    service = CBCRService()
    service.run()
