# running tests etc.
FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /usr/src/app
CMD ["/bin/bash"]