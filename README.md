🤖 Bot de Verificación de Pagos (Telegram + n8n + Python OCR)
Este proyecto automatiza la validación de vouchers de pago (Yape/Plin) enviados por Telegram, extrae los datos mediante una API de OCR personalizada en Python y registra la información automáticamente en un Google Sheets.

🚀 Estructura del Proyecto
n8n: Orquestador del flujo de trabajo (Webhooks, Lógica de decisión, Conectores).

Python OCR API: Contenedor Docker con Tesseract/EasyOCR para procesar imágenes.

Google Sheets: Base de datos final para el registro de operaciones.

Telegram: Interfaz de usuario para el envío de comprobantes.

🛠️ Requisitos Previos
Docker Desktop instalado y corriendo.

Ngrok (para exponer n8n a internet si trabajas de forma local).

Un Bot de Telegram (creado vía @BotFather).

Una cuenta de Google Cloud Console (con la API de Google Sheets habilitada).

📦 Instalación y Despliegue
1. Clonar el repositorio
Bash
git clone https://github.com/tu-usuario/nombre-del-proyecto.git
cd nombre-del-proyecto
2. Configurar Variables de Entorno
Crea un archivo .env en la raíz del proyecto y añade tus credenciales:

Fragmento de código
TELEGRAM_BOT_TOKEN=tu_token_aqui
N8N_ENCRYPTION_KEY=una_clave_aleatoria
PYTHON_API_URL=http://python_ocr_api:8000/procesar-pago
3. Levantar con Docker
Bash
docker-compose up -d
Esto levantará:

n8n en http://localhost:5678

Python API en http://localhost:8000

⚙️ Configuración de los Componentes
A. n8n (Importar Flujo)
Accede a http://localhost:5678.

Crea un nuevo workflow y selecciona Import from File.

Selecciona el archivo workflow_pago.json incluido en este repo.

B. Google Sheets (Credenciales OAuth2)
En Google Cloud Console, crea un ID de cliente OAuth 2.0.

Añade la URL de redireccionamiento de tu n8n (ej. https://tu-ngrok.dev/rest/oauth2-credential/callback).

Copia el Client ID y Client Secret en el nodo de Google Sheets en n8n.

C. Python OCR API (Endpoints)
La API espera un POST en /procesar-pago con un archivo bajo la clave file.

Input: Archivo de imagen (JPG/PNG).

Output: JSON con monto, banco, operacion, nombre y estado.

📋 Flujo de Trabajo (Workflow)
Telegram Trigger: Escucha mensajes con fotos.

IF Node: Filtra para asegurar que el mensaje contenga un archivo de imagen.

Get a File: Descarga el archivo desde los servidores de Telegram.

HTTP Request: Envía la imagen a la API de Python (Multipart-Form-Data).

Google Sheets: Inserta una nueva fila (Append) con los datos extraídos.

Telegram Send: Responde al usuario confirmando el registro del pago.

🛠️ Comandos Útiles
Ver logs de la API de Python: docker logs -f python_ocr_api

Reiniciar n8n: docker restart n8n

Detener todo: docker-compose down

📝 Notas de Mantenimiento
Ngrok: Si usas la versión gratuita, la URL cambia cada vez que reinicias. Recuerda actualizar el Webhook en Telegram si eso sucede.

OCR: La precisión del OCR depende de la calidad de la imagen y de que el voucher no esté muy arrugado o borroso.