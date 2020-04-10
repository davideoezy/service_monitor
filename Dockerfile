FROM ubuntu:18.04
COPY requirements.txt /tmp 
WORKDIR /tmp 
#RUN apk add --update tzdata
ENV TZ=Australia/Melbourne
#RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt
WORKDIR /.
COPY . /

CMD [ "python3", "./monitor.py" ]
