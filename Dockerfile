FROM python:3.9-alpine3.17 as final

RUN apk update
RUN apk add git
RUN apk add pandoc
RUN apk add build-base linux-headers

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

WORKDIR /code

COPY ./pyproject.toml /code/

RUN python -m pip install --no-cache-dir --upgrade .


COPY ./src/wikmd /code/wikmd
COPY ./wiki_template /wiki_template

# Expose the port that the application listens on.
EXPOSE 5000

# Run the application.
CMD ["python", "-m", "wikmd.wiki"]
