FROM python:3.12-alpine
WORKDIR /app
COPY . .
EXPOSE 8080
CMD ["python", "-m", "server", "--host", "0.0.0.0"]
