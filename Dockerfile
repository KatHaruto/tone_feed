FROM python:3.8
USER root

RUN apt-get update && apt-get install -y && pip install --upgrade pip
WORKDIR /home/flask_audio_test

RUN apt-get install -y portaudio19-dev libsndfile1

COPY requirements.txt /home/
RUN pip install -r /home/requirements.txt

ENV FLASK_APP '/home/flask_audio_test/app.py'
ENV FLASK_DEBUG 1
