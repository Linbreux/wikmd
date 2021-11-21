FROM alpine:latest

RUN apk add --no-cache py3-pip python3-dev git gcc musl-dev linux-headers pandoc

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

ENV LANG=C.UTF-8

RUN pip3 install -r requirements.txt

COPY . /app

RUN git config --global user.email "azer.abdullaev.berlin+git@gmail.com"
RUN git config --global user.name "Azer Abdullaev"

ENTRYPOINT [ "python3"  ]

CMD [ "wiki.py"  ]
