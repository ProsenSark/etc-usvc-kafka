FROM python:2

WORKDIR /root
COPY requirements.txt /root

RUN set -ex; \
    apt-get update; \
    apt-get install -y librdkafka1; \
    apt-get clean; \
    pip install --no-cache-dir -r requirements.txt

COPY *.py /root/
ADD tests /root/tests

#ENV PYTHONPATH "${PYTHONPATH}:/root/packages"

#ENTRYPOINT ["/bin/bash", "-c"]

WORKDIR /root/tests
CMD ["python", "-u", "../tusvc_main.py", "-f", "example.yml"]

