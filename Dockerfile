FROM python:3.6.6-stretch
WORKDIR /opt/dplaapi
COPY . /opt/dplaapi
EXPOSE 8000
RUN pip install -r requirements.txt
CMD uvicorn -b 0.0.0.0:8000 --log-level warning dplaapi:app
