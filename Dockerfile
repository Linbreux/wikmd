FROM ubuntu:focal

RUN apt -y update && apt install -y python3-pip python3-dev git gcc pandoc

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

ENV LANG=C.UTF-8

RUN pip3 install -r requirements.txt

COPY . /app

RUN git config --global user.email "azer.abdullaev.berlin+git@gmail.com"
RUN git config --global user.name "Azer Abdullaev"

ENTRYPOINT [ "python3"  ]

CMD [ "wiki.py"  ]
