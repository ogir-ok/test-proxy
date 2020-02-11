FROM python:3.8
WORKDIR /opt/proxy
ADD . .
RUN pip install -r requirements.txt

