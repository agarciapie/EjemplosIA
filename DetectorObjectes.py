import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import tempfile
from PIL import Image

# Configuració de la pàgina
st.set_page_config(page_title="Detector d'Objectes", page_icon="📷")
st.title("📷 Detector d'Objectes en Temps Real")

# Text explicatiu sobre l'aplicació
st.write("""
Aquesta aplicació utilitza un model YOLO per detectar objectes en temps real a través de la càmera web.
Pots capturar una imatge i veure els objectes detectats directament a la pàgina.
""")

# Carregar el model YOLO
@st.cache_resource
def carregar_model():
    return YOLO('yolov8n.pt')

model = carregar_model()

# Funció per processar el frame
def processar_frame(frame):
    resultats = model(frame)
    for resultat in resultats:
        anotacions = resultat.plot()
        return Image.fromarray(anotacions)
    return Image.fromarray(frame)

# Inicialitzar la càmera
if 'camera' not in st.session_state:
    st.session_state.camera = cv2.VideoCapture(0)

# Columnes per botons
col1, col2 = st.columns(2)

# Botó per capturar
if col1.button("📸 Capturar Imatge"):
    ret, frame = st.session_state.camera.read()
    if ret:
        # Convertir BGR a RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Processar el frame
        frame_processat = processar_frame(frame_rgb)
        # Mostrar el resultat
        st.image(frame_processat, caption="Objectes Detectats", use_container_width=True)
    else:
        st.error("Error en capturar la imatge")

# Botó per aturar la càmera
if col2.button("⏹️ Aturar Càmera"):
    st.session_state.camera.release()
    st.success("Càmera aturada")
    st.session_state.pop('camera', None)
    st.rerun()

# Informació sobre els objectes detectables
with st.expander("ℹ️ Informació sobre objectes detectables"):
    st.write("""
    Aquest detector pot identificar 80 tipus diferents d'objectes, incloent:
    - Persones
    - Animals (gats, gossos, ocells, etc.)
    - Vehicles (cotxes, bicicletes, autobusos, etc.)
    - Objectes quotidians (telèfons, llibres, tasses, etc.)
    - I molt més!
    """)

# Notes d'ús
st.sidebar.header("📝 Notes d'ús")
st.sidebar.write("""
1. Assegura't que tens una càmera web connectada
2. Fes clic a 'Capturar Imatge' per detectar objectes
3. Utilitza 'Aturar Càmera' quan acabis
""")

# Netejar recursos quan es tanca l'aplicació
def cleanup():
    if 'camera' in st.session_state:
        st.session_state.camera.release()

# Registrar la funció de neteja
import atexit
atexit.register(cleanup)