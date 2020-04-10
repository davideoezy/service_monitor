FROM ubuntu:18.04
COPY requirements.txt /tmp 
WORKDIR /tmp 
ENV TZ=Australia/Melbourne
RUN apt update && apt install -y python3-pip
RUN pip3 install -r requirements.txt
WORKDIR /.
COPY . /

CMD [ "python3", "./monitor.py" ]
