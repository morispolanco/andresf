import streamlit as st
import requests
import json
from PyPDF2 import PdfReader
import io

# Configuración de la página
st.set_page_config(
    page_title="Chatbot - Médicos de la locura",
    page_icon="🩺",
    layout="wide",
)

# Título de la aplicación
st.title("🤖 Chatbot sobre 'Médicos de la locura'")

# Explicación breve
st.markdown("""
    Este chatbot te permite hacer preguntas sobre el libro **'Médicos de la locura'**.
    Sube el libro en formato PDF o TXT, y comienza a interactuar.
""")

# Función para extraer texto de un archivo PDF
def extract_text_from_pdf(file):
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error al leer el archivo PDF: {e}")
        return None

# Función para extraer texto de un archivo TXT
def extract_text_from_txt(file):
    try:
        stringio = io.StringIO(file.getvalue().decode("utf-8"))
        text = stringio.read()
        return text
    except Exception as e:
        st.error(f"Error al leer el archivo TXT: {e}")
        return None

# Subida del archivo del libro
uploaded_file = st.file_uploader(
    "Sube el libro 'Médicos de la locura' en formato PDF o TXT",
    type=["pdf", "txt"]
)

book_content = ""

if uploaded_file is not None:
    st.success("Archivo cargado con éxito.")
    if uploaded_file.type == "application/pdf":
        book_content = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "text/plain":
        book_content = extract_text_from_txt(uploaded_file)
    else:
        st.error("Formato de archivo no soportado. Por favor, sube un PDF o TXT.")

    if book_content:
        st.info("El libro ha sido procesado y está listo para responder tus preguntas.")
else:
    st.warning("Por favor, sube el libro para comenzar.")

# Entrada para la pregunta del usuario
user_question = st.text_input("Escribe tu pregunta sobre el libro:")

# Botón para enviar la pregunta
if st.button("Enviar"):
    if not uploaded_file:
        st.error("Por favor, sube el libro antes de hacer una pregunta.")
    elif not user_question.strip():
        st.error("Por favor, escribe una pregunta válida.")
    else:
        with st.spinner("Procesando tu pregunta..."):
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

                # Realizar la solicitud POST a la API
                response = requests.post(api_url, headers=headers, data=json.dumps(data))

                # Verificar el estado de la respuesta
                if response.status_code == 200:
                    response_data = response.json()
                    # Extraer la respuesta del asistente
                    assistant_reply = response_data.get("choices")[0].get("message").get("content")
                    st.success("Respuesta del chatbot:")
                    st.write(assistant_reply)
                else:
                    st.error(f"Error en la API: {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
