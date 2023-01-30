FROM python:3.9.4

#RUN apt-get update; apt-get install -y --no-install-recommends poppler-utils poppler-data libgs-dev ffmpeg libsm6 libxext6

RUN mkdir /code
RUN python -m venv /code/.venv

ENV PATH="/code/.venv/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends libgeos-dev 

RUN apt-get update && apt-get install -y --no-install-recommends libgs-dev

