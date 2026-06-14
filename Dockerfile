# Dockerfile, Image, Container
FROM python:3.12

ADD / .

RUN pip install discord
RUN pip install python-dotenv
RUN pip install qbittorrent-api


CMD ["python", "./main.py"]
