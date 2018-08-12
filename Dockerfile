FROM python:3.6.6-stretch
WORKDIR /opt/dplaapi
COPY . /opt/dplaapi
EXPOSE 8000
RUN pip install -r requirements.txt
CMD workers=`nproc --all`; gunicorn -w $workers -b 0.0.0.0:8000 -k uvicorn.worker.UvicornWorker dplaapi:app
