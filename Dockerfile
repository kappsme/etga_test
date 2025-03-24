FROM python:3.11.11-bullseye
WORKDIR /app

COPY requirements.txt .
# COPY .env-admin .
# RUN pip install pkgconfig
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN rm -f requirements.txt
# CMD ["python3"]

EXPOSE 3000
