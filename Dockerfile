# Base image Dockerfile https://github.com/nginx/unit/blob/master/pkg/docker/Dockerfile.python3.7
# Official examples https://unit.nginx.org/howto/docker/

FROM nginx/unit:1.13.0-python3.5

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt update && apt install -y --no-install-recommends python3-pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apt remove -y python3-pip \
    && apt autoremove --purge -y \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/*.list

COPY app .
COPY config/conf.json /var/lib/unit/
