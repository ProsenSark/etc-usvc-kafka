#FROM python:3
FROM python:3.6-alpine3.8

COPY requirements.txt /root
COPY reqs3.txt /root
COPY *.py /root/
ADD tests /root/tests

WORKDIR /root

RUN set -ex; \
    #apt-get update; \
    #apt-get install -y librdkafka1; \
    #apt-get clean; \
    apk add --no-cache librdkafka libcurl; \
    #apk add --no-cache python3; \
    apk add --no-cache musl-dev gcc librdkafka-dev curl-dev; \
    apk add --no-cache python3-dev; \
    pip3 install --upgrade pip; \
    pip3 install --no-cache-dir -r requirements.txt; \
    pip3 install --no-cache-dir -r reqs3.txt; \
    apk del python3-dev; \
    apk del musl-dev gcc librdkafka-dev curl-dev; \
    echo -e "All dependencies installed ..."

#ENV PYTHONPATH "${PYTHONPATH}:/root/packages"

#ENTRYPOINT ["/bin/bash", "-c"]

WORKDIR /root/tests
CMD ["python3", "-u", "../tusvc_main.py", "-f", "example.yml"]

