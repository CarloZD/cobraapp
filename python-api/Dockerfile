FROM python:3.11-slim

WORKDIR /app

# Instalamos Tesseract y las dependencias gráficas actualizadas
# Nota: Hemos cambiado libgl1-mesa-glx por libgl1
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]