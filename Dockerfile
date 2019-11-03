FROM python:2-stretch

RUN mkdir /app
RUN mkdir /app/db
ADD . /app
WORKDIR /app
RUN chmod +x start.sh

RUN pip install -r requirements.txt
CMD python /app/bot.py
