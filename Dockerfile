from python:3.8

# 设置镜像的时区为上海
ENV TZ Asia/Shanghai

# 设置apt源
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list

# 安装vim
RUN apt update && apt install -y vim git

# 安装python环境
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -i https://mirror.baidu.com/pypi/simple/ -r /code/requirements.txt


COPY . /code
RUN cd /code/tests && python test_paddleocr.py

# 设置工作目录
WORKDIR /code



