from python:3.8

# 设置镜像的时区为上海
ENV TZ Asia/Shanghai

# 设置apt源
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list

# 安装vim
RUN apt update && apt install -y vim git procps net-tools

# 安装python环境
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -i https://mirror.baidu.com/pypi/simple/ -r /code/requirements.txt


COPY . /code
COPY .paddleocr /root/.paddleocr

RUN sed -i 's/https:.*swagger-ui-bundle.js/\/static\/swagger-ui-bundle.js/g' /usr/local/lib/python3.8/site-packages/fastapi/openapi/docs.py && sed -i 's/https:.*swagger-ui.css"/\/static\/swagger-ui.css"/g' /usr/local/lib/python3.8/site-packages/fastapi/openapi/docs.py
# 设置工作目录
WORKDIR /code



