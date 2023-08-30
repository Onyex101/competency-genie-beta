FROM python:3.9-slim

WORKDIR /app

# Create the environment:
COPY requirements.txt ./requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app

ENTRYPOINT ["./startup.sh"]

# EXPOSE 8501

# ENTRYPOINT ["streamlit", "run", "src/App.py"]