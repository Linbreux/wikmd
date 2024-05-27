FROM python:3.9-alpine3.17 as python-base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# We will be installing venv
ENV VIRTUAL_ENV="/venv"

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


# Add project path to python path, this to ensure we can reach it from anywhere
WORKDIR /code
ENV PYTHONPATH="/code:$PYTHONPATH"

# prepare the virtual env
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m venv $VIRTUAL_ENV

# BUILDER
FROM python-base as python-builder

# Install our dependencies
RUN apk update
RUN apk add git
RUN apk add build-base linux-headers

# Python dependencies
WORKDIR /code

COPY pyproject.toml /code

# Copy the py project and use a package to convert our pyproject.toml file into a requirements file
# We can not install the pyproject with pip as that would install the project and we only
# wants to install the project dependencies.
RUN python -m pip install toml-to-requirements==0.2.0
RUN toml-to-req --toml-file pyproject.toml

RUN python -m pip install --no-cache-dir --upgrade -r ./requirements.txt

# Copy our source content over
COPY ./src/wikmd /code/wikmd

# Change the directory to the root.
WORKDIR /

# Expose the port that the application listens on.
EXPOSE 5000

# Run the application.
CMD ["python", "-m", "wikmd.wiki"]
