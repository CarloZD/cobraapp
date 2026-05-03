# Usa una imagen de Python ligera
FROM python:3.9-slim

# Instala Tesseract OCR y dependencias modernas para OpenCV (libgl1 en lugar de libgl1-mesa-glx)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copia los requisitos e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la API
COPY main.py .

# Expone el puerto que usa FastAPI
EXPOSE 8000

# Comando para arrancar
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]