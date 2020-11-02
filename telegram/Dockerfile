FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . .
CMD ["/bin/bash"]
#CMD ["python3", "telegram/main.py"]
#VOLUME [".", "/usr/src/app"]
#VOLUME .:/usr/src/app
