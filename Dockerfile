FROM python:3.6.6-stretch
LABEL maintainer="DPLA Tech Team <tech@dp.la"
WORKDIR /opt/dplaapi
COPY . /opt/dplaapi
EXPOSE 8000
RUN pip install -r requirements.txt
CMD workers=`nproc --all`; gunicorn -w $workers -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker dplaapi:app
