FROM python:3.10

WORKDIR /app
COPY . /app

RUN pip install openai PyGithub

CMD ["python", "src/self_healing.py"]
