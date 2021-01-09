import logging
import os

import opencc
import openpyxl

logger = logging.getLogger(__name__)
opencc_s2t_converter = opencc.OpenCC('s2t.json')

# https://github.com/wainshine/Chinese-Names-Corpus
FAMILY_NAME_XLSX = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', r'data/Chinese_Family_Name（1k）.xlsx'))
FAMILY_NAME_XLSX_SHEET_NAME = '中文姓氏1074个'

simp_family_names = set()  # 简体姓氏
trad_family_names = set()  # 繁体姓氏
full_family_names = set()  # 简体姓氏 + 繁体姓氏


def load_family_name():
    """从xlsx载入姓氏"""
    global logger, simp_family_names, trad_family_names, full_family_names
    if full_family_names:
        logger.info('family dict has loaded.')
        return

    workbook = openpyxl.load_workbook(filename=FAMILY_NAME_XLSX)
    sheet = workbook[FAMILY_NAME_XLSX_SHEET_NAME]

    # 读A列“姓”数据
    is_head_line = True
    for family_name in sheet['A']:
        if is_head_line:
            is_head_line = False
            continue
        simp = family_name.value
        simp_family_names.add(simp)
        trad = opencc_s2t_converter.convert(simp)
        trad_family_names.add(trad)

    full_family_names.update(simp_family_names)
    full_family_names.update(trad_family_names)
    workbook.close()


load_family_name()
