FROM ubuntu:18.04

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev pandoc git

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

ENV LANG=C.UTF-8

RUN pip3 install -r requirements.txt

COPY . /app

RUN git config --global user.email "user@wikmd.com"
RUN git config --global user.name "user"

ENTRYPOINT [ "python3"  ]

CMD [ "wiki.py"  ]

