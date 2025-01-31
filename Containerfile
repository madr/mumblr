FROM python:alpine AS base
WORKDIR /app

FROM base as deps
WORKDIR /app
COPY ./requirements.txt .
RUN pip install -r requirements.txt

FROM deps as scripts
WORKDIR /app
COPY ./backup.py .
COPY ./entrypoint.sh .

FROM scripts as app
WORKDIR /app
COPY ./src ./src

FROM app AS env
WORKDIR /app
ENV TBS_TS="1999-09-09 09:09"
ENV TBS_CONSUMER_KEY replace_me
ENV TBS_CONSUMER_SECRET replace_me
ENV TBS_OAUTH_TOKEN replace_me
ENV TBS_OAUTH_SECRET replace_me
ENV TBS_BLOG_NAME replace_me

FROM env AS final
ENTRYPOINT ["/app/entrypoint.sh"]
