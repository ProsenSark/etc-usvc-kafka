#FROM python:2
FROM python:2.7-alpine3.8

COPY requirements.txt /root
COPY reqs2.txt /root
COPY *.py /root/
ADD tests /root/tests

WORKDIR /root

RUN set -ex; \
    #apt-get update; \
    #apt-get install -y librdkafka1; \
    #apt-get clean; \
    apk add --no-cache librdkafka libcurl; \
    #apk add --no-cache python2 py-pip; \
    apk add --no-cache musl-dev gcc librdkafka-dev curl-dev; \
    apk add --no-cache python2-dev; \
    pip2 install --upgrade pip; \
    pip2 install --no-cache-dir -r requirements.txt; \
    pip2 install --no-cache-dir -r reqs2.txt; \
    apk del python2-dev; \
    apk del musl-dev gcc librdkafka-dev curl-dev; \
    echo -e "All dependencies installed ..."

#ENV PYTHONPATH "${PYTHONPATH}:/root/packages"

#ENTRYPOINT ["/bin/bash", "-c"]

WORKDIR /root/tests
CMD ["python2", "-u", "../tusvc_main.py", "-f", "example.yml"]

