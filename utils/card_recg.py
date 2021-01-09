import abc
from typing import List

import regex as re
from pydantic import Field, BaseModel

from utils.family_name import full_family_names
from utils.ocr import OCRResult, Box

EMAIL_PATTERN = r'[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}'
PHONE_PATTERN = r'\+?\(?\d+[)-]?\d+'
TITLE_KEYWORDS = ['委员', '主席', '首席', '合伙人', '顾问', '负责人', '行长', '厂长', '合伙人', '经纪人', '中介',
                  '董事长', '总监', '总裁', '专员', '助理', '主管', '工程师', '经理', '督导', '代表', '指导', '员']
LOCATION_KEYWORDS = ['省', '自治区', '市', '路', '号', '单元', '楼']
NAME_PATTERN = f'[{"|".join(full_family_names)}]' + r'[\u4e00-\u9fa5]{1,3}'


class Extractor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def extract(self, text):
        pass


class EmailExtractor(Extractor):
    def extract(self, text):
        if '@' in text:
            match = re.search(EMAIL_PATTERN, text)
            if match:
                return match.group()


class PhoneExtractor(Extractor):
    def extract(self, text):
        match = re.search(PHONE_PATTERN, text)
        if match:
            phone = match.group()
            if len(phone) >= 7:
                return phone


class TitleExtractor(Extractor):
    def extract(self, text):
        for title in TITLE_KEYWORDS:
            if text.endswith(title):
                return title


class LocationExtractor(Extractor):
    def extract(self, text):
        if '地址' in text:
            return text.replace('地址')
        for keyword in LOCATION_KEYWORDS:
            if keyword in text and len(text) > 9:
                return text


class OrganizationExtractor(Extractor):
    def extract(self, text):
        if '公司' in text or '公司' in text:
            return text


class NameExtractor(Extractor):
    def extract(self, text):
        if 1 <= len(text) <= 3:
            match = re.search(NAME_PATTERN, text)
            if match:
                return text


class Name(BaseModel):
    value: str = Field(..., description='姓名')
    box: Box = Field(..., description='边框')


class Phone(BaseModel):
    value: str = Field(..., description='电话')
    box: Box = Field(..., description='边框')


class Email(BaseModel):
    value: str = Field(..., description='邮件')
    box: Box = Field(..., description='边框')


class Location(BaseModel):
    value: str = Field(..., description='地点')
    box: Box = Field(..., description='边框')


class Title(BaseModel):
    value: str = Field(..., description='职位')
    box: Box = Field(..., description='边框')


class Organization(BaseModel):
    value: str = Field(..., description='组织')
    box: Box = Field(..., description='边框')


class CardInfo(BaseModel):
    name: List[Name] = Field(default_factory=list, description='姓名')
    phone: List[Phone] = Field(default_factory=list, description='电话/传真')
    email: List[Email] = Field(default_factory=list, description='邮件')
    location: List[Location] = Field(default_factory=list, description='地点')
    title: List[Title] = Field(default_factory=list, description='职位职务')
    organization: List[Organization] = Field(default_factory=list, description='组织/机构/公司')


def extract_card_info_from_pd_ocr(pd_ocr_result: OCRResult):
    card_info = CardInfo()
    for text in pd_ocr_result.texts:
        t = text.text
        t = t.replace(' ', '').strip()

        name = NameExtractor().extract(t)
        if name:
            card_info.name.append(Name(value=name, box=text.box))
        phone = PhoneExtractor().extract(t)
        if phone:
            card_info.phone.append(Phone(value=phone, box=text.box))
        email = EmailExtractor().extract(t)
        if email:
            card_info.email.append(Email(value=email, box=text.box))
        location = LocationExtractor().extract(t)
        if location:
            card_info.location.append(Location(value=location, box=text.box))
        title = TitleExtractor().extract(t)
        if title:
            card_info.title.append(Title(value=title, box=text.box))
        organization = OrganizationExtractor().extract(t)
        if organization:
            card_info.organization.append(Organization(value=organization, box=text.box))

    return card_info
