FROM python:3

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
#RUN apk add --update tzdata
ENV TZ=Australia/Melbourne
COPY . .

CMD [ "python", "./monitor.py" ]
