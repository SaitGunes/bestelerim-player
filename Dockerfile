FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Railway dinamik port verir
ENV PORT=8080
EXPOSE $PORT

CMD uvicorn server:app --host 0.0.0.0 --port $PORT
