"""
Aplicació de Classificació d'Imatges

Aquesta aplicació permet:
1. Pujar imatges en format PNG, JPG o JPEG
2. Classificar-les en 5 categories diferents:
   - Paisatges
   - Persones
   - Menjar
   - Cotxes
   - Tècnica
3. Mantenir un registre de les imatges classificades
4. Veure estadístiques de cada categoria
5. Netejar les categories quan es vulgui

Característiques principals:
- Interfície gràfica amb Streamlit
- Emmagatzematge temporal de les imatges
- Visualització prèvia de les imatges abans de classificar-les
- Accés directe a la carpeta d'emmagatzematge
- Comptador d'imatges per categoria
"""

import streamlit as st
import os
from PIL import Image
import tempfile
from pathlib import Path
import subprocess
import platform

# Configuració de la pàgina
st.set_page_config(page_title="Classificador d'Imatges", page_icon="🖼️")

# Títol
st.title("🖼️ Classificador d'Imatges")

# Definir les categories
categories = ["Paisatges", "Persones", "Menjar", "Cotxes", "Tècnica"]

# Inicialitzar el directori base en una ubicació temporal
if 'base_dir' not in st.session_state:
    temp_dir = tempfile.gettempdir()
    st.session_state.base_dir = Path(temp_dir) / "classificador_imatges"
    
    # Crear directori base si no existeix
    if not st.session_state.base_dir.exists():
        st.session_state.base_dir.mkdir(parents=True)

    # Crear directoris per cada categoria
    for categoria in categories:
        cat_path = st.session_state.base_dir / categoria
        if not cat_path.exists():
            cat_path.mkdir(parents=True)

# Mostrar la ruta de les imatges
st.sidebar.subheader("📁 Ubicació de les imatges")
ruta_actual = str(st.session_state.base_dir)
st.sidebar.code(ruta_actual)

# Botó per obrir la carpeta
def obrir_carpeta(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", path])
    else:  # Linux
        subprocess.run(["xdg-open", path])

if st.sidebar.button("📂 Obrir carpeta d'imatges"):
    try:
        obrir_carpeta(ruta_actual)
        st.sidebar.success("Carpeta oberta!")
    except Exception as e:
        st.sidebar.error(f"Error en obrir la carpeta: {str(e)}")

# Funció per moure la imatge a la carpeta seleccionada
def moure_imatge(imatge, categoria):
    try:
        if imatge is not None:
            # Crear ruta completa
            ruta_categoria = st.session_state.base_dir / categoria
            nom_arxiu = ruta_categoria / imatge.name
            
            # Guardar la imatge
            with open(str(nom_arxiu), "wb") as f:
                f.write(imatge.getbuffer())
            
            return True
    except Exception as e:
        st.error(f"Error en guardar la imatge: {str(e)}")
        return False
    return False

# Pujar imatge
imatge_pujada = st.file_uploader("Selecciona una imatge", type=['png', 'jpg', 'jpeg'])

if imatge_pujada is not None:
    # Mostrar la imatge
    st.image(imatge_pujada, caption="Imatge seleccionada", use_container_width=True)
    
    # Seleccionar categoria
    categoria = st.selectbox("Selecciona la categoria:", categories)
    
    # Botó per classificar
    if st.button("Classificar imatge"):
        if moure_imatge(imatge_pujada, categoria):
            st.success(f"Imatge classificada correctament a la categoria: {categoria}")
        else:
            st.error("Error en classificar la imatge")

# Mostrar estadístiques
st.subheader("📊 Estadístiques")
for categoria in categories:
    ruta_categoria = st.session_state.base_dir / categoria
    try:
        num_imatges = len([arxiu for arxiu in ruta_categoria.glob("*")
                          if arxiu.suffix.lower() in ['.png', '.jpg', '.jpeg']])
        st.text(f"{categoria}: {num_imatges} imatges")
    except Exception as e:
        st.error(f"Error en llegir la categoria {categoria}: {str(e)}")

# Botó per netejar totes les categories
if st.button("🗑️ Netejar totes les categories"):
    try:
        for categoria in categories:
            ruta_categoria = st.session_state.base_dir / categoria
            for arxiu in ruta_categoria.glob("*"):
                if arxiu.is_file():
                    try:
                        arxiu.unlink()
                    except Exception as e:
                        st.error(f"Error en eliminar {arxiu.name}: {str(e)}")
        st.success("S'han netejat totes les categories")
        st.rerun()
    except Exception as e:
        st.error(f"Error en netejar les categories: {str(e)}") 