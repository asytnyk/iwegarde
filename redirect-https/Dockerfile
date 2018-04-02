FROM python:2.7-alpine

RUN adduser -D iwegarde

WORKDIR /home/iwegarde

COPY redirect.py ./
RUN chmod +x redirect.py

RUN chown -R iwegarde:iwegarde ./

USER iwegarde
EXPOSE 5000
ENTRYPOINT ["./redirect.py"]
