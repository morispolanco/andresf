import streamlit as st
import requests
import json
from PyPDF2 import PdfReader
import time

# Configuración de la página con diseño predeterminado (estrecho)
st.set_page_config(
    page_title="Chatbot - Médicos de la locura",
    page_icon="🩺",
    layout="centered",  # Diseño predeterminado y estrecho
)

# Título de la aplicación
st.title("🤖 Chatbot sobre 'Médicos de la locura'")

# Descripción breve
st.markdown("""
    Este chatbot te permite hacer preguntas sobre el libro **'Médicos de la locura'**.
    El contenido del libro está pre-cargado para que puedas interactuar directamente.
""")

# Ruta al archivo PDF pre-cargado en la raíz del proyecto
PDF_PATH = "medicos_de_la_locura.pdf"

@st.cache_data
def extract_text_from_pdf(file_path):
    """
    Extrae el texto de un archivo PDF.

    Args:
        file_path (str): Ruta al archivo PDF.

    Returns:
        str: Contenido del PDF en formato de texto.
    """
    try:
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            text = ""
            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    text += f"--- Página {page_num} ---\n" + page_text + "\n"
        return text
    except FileNotFoundError:
        st.error(f"No se encontró el archivo PDF en la ruta especificada: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error al leer el archivo PDF: {e}")
        return None

# Función para realizar solicitudes con reintentos en caso de error 429
def make_api_request(url, headers, data, max_retries=5, backoff_factor=1):
    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", backoff_factor))
            st.warning(f"Demasiadas solicitudes. Reintentando en {retry_after} segundos...")
            time.sleep(retry_after)
            backoff_factor *= 2  # Incrementa el tiempo de espera exponencialmente
        else:
            st.error(f"Error en la API: {response.status_code} - {response.text}")
            return None
    st.error("Se alcanzó el número máximo de reintentos.")
    return None

# Extraer el contenido del libro
st.info("Procesando el libro. Por favor, espera...")
book_content = extract_text_from_pdf(PDF_PATH)

if book_content:
    st.success("El libro ha sido procesado y está listo para responder tus preguntas.")
else:
    st.error("No se pudo procesar el libro. Asegúrate de que el archivo PDF esté en la ubicación correcta.")
    st.stop()  # Detiene la ejecución si no se pudo cargar el libro

# Entrada para la pregunta del usuario
user_question = st.text_input("📝 Escribe tu pregunta sobre el libro:")

# Botón para enviar la pregunta
if st.button("Enviar 🚀"):
    if not user_question.strip():
        st.error("❌ Por favor, escribe una pregunta válida.")
    else:
        with st.spinner("🔄 Procesando tu pregunta..."):
            try:
                # Obtener la clave de la API desde los secretos
                api_key = st.secrets["xai_api_key"]

                # Endpoint de la API de x.ai
                api_url = "https://api.x.ai/v1/chat/completions"

                # Preparar los mensajes para la API
                messages = [
                    {
                        "role": "system",
                        "content": "Eres un asistente útil que responde preguntas basadas en el libro 'Médicos de la locura'."
                    },
                    {
                        "role": "user",
                        "content": f"{book_content}\n\nPregunta: {user_question}"
                    }
                ]

                # Datos para enviar a la API
                data = {
                    "messages": messages,
                    "model": "grok-2-1212",
                    "stream": False,
                    "temperature": 0.7
                }

                # Encabezados de la solicitud
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }

                # Realizar la solicitud POST a la API con reintentos
                response = make_api_request(api_url, headers, data)

                # Verificar el estado de la respuesta
                if response and response.status_code == 200:
                    response_data = response.json()
                    # Extraer la respuesta del asistente
                    assistant_reply = response_data.get("choices")[0].get("message").get("content")
                    st.success("💬 Respuesta del chatbot:")
                    st.write(assistant_reply)
                elif response:
                    # Ya se manejaron los errores dentro de make_api_request
                    pass

            except Exception as e:
                st.error(f"❌ Ocurrió un error: {e}")
