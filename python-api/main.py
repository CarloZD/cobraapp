from fastapi import FastAPI, UploadFile, File
import pytesseract
import cv2
import numpy as np
import re
from PIL import Image
from datetime import datetime

app = FastAPI()

def extraer_datos(texto):
    # Identificación de Banco
    texto_upper = texto.upper()
    banco = "Otro Banco"
    if "YAPE" in texto_upper: banco = "Yape"
    elif "PLIN" in texto_upper: banco = "Plin"
    elif any(x in texto_upper for x in ["BCP", "CREDITO"]): banco = "BCP"
    elif "INTERBANK" in texto_upper: banco = "Interbank"

    # 1. Monto: Busca patrones como S/ 10, S/. 10.00, s/10
    monto_match = re.search(r'(?:S/|s/|S\.)\s?(\d+(?:\.\d{2})?)', texto, re.IGNORECASE)
    
    # 2. Operación: Busca números de 6 a 15 dígitos
    operacion_match = re.search(r'(?:operaci[oó]n|nro|n[uú]mero|ref|id|transacci[oó]n)[:.\s]*(\d{6,15})', texto, re.IGNORECASE)
    
    # 3. Fecha y Hora: Formato flexible
    fecha_match = re.search(r'(\d{1,2}\s+[a-z]{3}\.?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})', texto, re.IGNORECASE)
    hora_match = re.search(r'(\d{1,2}:\d{2}\s*(?:a\.\s*m\.|p\.\s*m\.|am|pm))', texto, re.IGNORECASE)

    # 4. Extracción de Nombre (Lógica mejorada)
    nombre_final = "No detectado"
    lineas = [l.strip() for l in texto.split('\n') if len(l.strip()) > 2]

    # Intentar por etiquetas comunes
    nombre_match = re.search(r'(?:Destinatario|Para|Enviado a|Pagado a|Nombre)[:\s]+(.*?)(?:\n|$)', texto, re.IGNORECASE)
    
    if nombre_match and not any(x in nombre_match.group(1).upper() for x in ["EXITOSO", "PAGO", "S/."]):
        nombre_final = nombre_match.group(1).strip()
    elif banco == "Yape":
        # En Yape el nombre suele estar 2 líneas después de "Yapeaste" o justo después del monto
        res_yape = re.search(r'(?:S/|s/|S\.)\s?\d+(?:\.\d{2})?\s*\n+(.*?)\n', texto, re.IGNORECASE)
        if res_yape: nombre_final = res_yape.group(1).strip()
    
    # Limpieza final: si el nombre detectado es muy corto o tiene números, se busca en las líneas
    if nombre_final == "No detectado" or len(nombre_final) < 4:
        for linea in lineas:
            if re.search(r'[a-zA-Z]{5,}', linea) and not re.search(r'S/|s/|\d{4}', linea):
                if not any(x in linea.upper() for x in ["OPERACIÓN", "CONSTANCIA", "EXITO", "TRANSACC", "PAGO", "YAPEASTE"]):
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

        # 1. Reescalado: Crucial para imágenes de Telegram/WhatsApp
        h, w = img.shape[:2]
        img = cv2.resize(img, (w*2, h*2), interpolation=cv2.INTER_CUBIC)

        # 2. Procesamiento Simple (Grises + Otsu) para no perder texto blanco
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