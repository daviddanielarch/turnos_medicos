FROM python:3.9-slim

RUN apt update && apt install -y python3-pip && apt upgrade -y

# this line is just for Python
ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app

CMD ["/app/find_appointment.py"]