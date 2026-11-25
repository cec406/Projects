FROM python:3.13-alpine
WORKDIR /app
COPY index.html .
USER 65534:65534
EXPOSE 8080
CMD ["python", "-m", "http.server", "8080"]
