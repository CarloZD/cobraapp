from fastapi import FastAPI, UploadFile, File
import pytesseract
import cv2
import numpy as np
import re
from PIL import Image
from datetime import datetime

app = FastAPI()

def identificar_banco(texto):
    texto_upper = texto.upper()
    if "YAPE" in texto_upper: return "Yape"
    if "PLIN" in texto_upper: return "Plin"
    if "BCP" in texto_upper or "CREDITO" in texto_upper: return "BCP"
    if "INTERBANK" in texto_upper: return "Interbank"
    if "BBVA" in texto_upper: return "BBVA"
    if "SCOTIABANK" in texto_upper: return "Scotiabank"
    return "Banco Externo"

def extraer_datos(texto):
    banco = identificar_banco(texto)
    
    # 1. Monto: Busca patrones de moneda S/ seguido de números
    monto_match = re.search(r'(?:S/|s/|S\.|s\.)?\s?(\d{1,4}(?:\.\d{2})?)', texto)
    
    # 2. Operación: Busca números largos de 6 a 14 dígitos (BCP e Interbank usan formatos largos)
    operacion_match = re.search(r'(?:operaci[oó]n|nro|n[uú]mero|ref|constancia|transacci[oó]n)[:.\s]*(\d{6,14})', texto, re.IGNORECASE)
    
    # 3. Fecha y Hora: Formato flexible para capturar "14 Abr 2026" o "14/04/2026"
    fecha_match = re.search(r'(\d{1,2}\s+[a-z]{3}\.?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})', texto, re.IGNORECASE)
    hora_match = re.search(r'(\d{1,2}:\d{2}\s*(?:a\.\s*m\.|p\.\s*m\.|am|pm))', texto, re.IGNORECASE)

    # 4. Extracción de Nombre según el Banco
    nombre_final = "Voucher Detectado"
    lineas = [l.strip() for l in texto.split('\n') if len(l.strip()) > 2]

    if banco == "Yape":
        # Lógica específica para el diseño de Yape
        nombre_match = re.search(r'(?:S/|s/|S\.)\s?\d+(?:\.\d{2})?\s*\n+(.*?)\n', texto, re.IGNORECASE)
        if nombre_match: nombre_final = nombre_match.group(1).strip()
    elif banco == "BCP":
        # En BCP suele estar después de "Enviado a" o "Destinatario"
        nombre_match = re.search(r'(?:Enviado a|Destinatario|Para)[:\s]+(.*?)(?:\n|$)', texto, re.IGNORECASE)
        if nombre_match: nombre_final = nombre_match.group(1).strip()
    else:
        # Lógica general para otros bancos: busca la línea más larga que no tenga números
        for linea in lineas:
            if re.search(r'[a-zA-Z]{6,}', linea) and not re.search(r'S/|s/|\d{4}', linea):
                if not any(x in linea.upper() for x in ["OPERACIÓN", "CONSTANCIA", "EXITOSA", "TRANSFERENCIA"]):
                    nombre_final = linea
                    break

    fecha_str = fecha_match.group(1) if fecha_match else "No detectada"
    if hora_match: fecha_str += f" {hora_match.group(1)}"

    return {
        "banco": banco,
        "monto": monto_match.group(1) if monto_match else "No detectado",
        "operacion": operacion_match.group(1) if operacion_match else "No detectado",
        "fecha_voucher": fecha_str,
        "nombre": nombre_final
    }

@app.post("/procesar-pago")
async def procesar_pago(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None: return {"estado": "error", "detalle": "No se pudo decodificar la imagen"}

        # Pre-procesamiento para limpiar ruidos de fondo (especial para vouchers verdes/azules)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        img_pil = Image.fromarray(thresh)
        texto = pytesseract.image_to_string(img_pil, lang='spa')

        datos = extraer_datos(texto)

        return {
            "estado": "procesado",
            "banco": datos["banco"],
            "nombre": datos["nombre"],
            "monto": datos["monto"],
            "operacion": datos["operacion"],
            "fecha_voucher": datos["fecha_voucher"],
            "fecha_proceso": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "texto_completo": texto.strip()
        }
    except Exception as e:
        return {"estado": "error", "detalle": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)