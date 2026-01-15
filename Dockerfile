FROM python:3.10-slim

# Install ffmpeg and necessary packages
RUN apt-get update && \
    apt-get install -y ffmpeg build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
