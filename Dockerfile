FROM python:3.9-slim

RUN apt update && apt install -y python3-pip && apt upgrade -y

# this line is just for Python
ENV PYTHONUNBUFFERED=1

## Create a virtual environment
#RUN python3 -m venv /home/seluser/venv
#
#COPY ./requirements.txt requirements.txt
#
#RUN . /home/seluser/venv/bin/activate && pip install --no-cache-dir -r requirements.txt
#
## Use the virtual environment Python for running the script
#ENV PATH="/home/seluser/venv/bin:$PATH"

COPY ./find_appointment.py /app/find_appointment.py
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

CMD python3 /app/find_appointment.py