FROM python:2.7-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app .

CMD [ "python", "./app.py" ]
