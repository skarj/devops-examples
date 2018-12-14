FROM nginx/unit:1.6-python2.7

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update -y && \
    apt-get install python-pip -y && \
    pip install pip --upgrade && \
    apt-get clean
    
RUN pip install --no-cache-dir -r requirements.txt

COPY app .
COPY config/conf.json /var/lib/unit/
