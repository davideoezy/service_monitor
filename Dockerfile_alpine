FROM python:3.7-alpine
COPY requirements.txt /tmp 
WORKDIR /tmp 
RUN apk add --update tzdata
ENV TZ=Australia/Melbourne
RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
     && pip install cython \
     && apk del .build-deps gcc musl-dev
RUN pip install -r requirements.txt
WORKDIR /.
COPY . /

CMD [ "python", "./monitor.py" ]
