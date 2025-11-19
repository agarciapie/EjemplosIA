"""
Aplicació de Classificació d'Imatges amb YOLOv8

Aquesta aplicació permet:
1. Pujar imatges (PNG, JPG, JPEG)
2. Classificar-les automàticament en categories:
   - Paisatges (landscapes)
   - Persones (people, person)
   - Cotxes (cars, vehicles)
   - Menjar (food, dishes)
   - Tècnica (technical, objects)
3. Copiar les imatges a les carpetes corresponents
4. Veure estadístiques de cada categoria
5. Mostrar les deteccions realitzades

Característiques principals:
- Interfície amb Streamlit
- Classificació automàtica amb YOLOv8
- Visualització de deteccions
- Emmagatzematge organitzat per categories
- Estadístiques en temps real
"""

import streamlit as st
import os
from PIL import Image
from pathlib import Path
import shutil
import tempfile
import platform
import subprocess
from datetime import datetime
from ultralytics import YOLO  # type: ignore
import numpy as np
import uuid

# ==================== CONFIGURACIÓ ====================
CATEGORIES = {
    'Paisatges': [
        'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
        'backpack', 'umbrella', 'potted plant', 'bench', 'kite', 'sports ball'
    ],
    'Persones': [
        'person'
    ],
    'Cotxes': [
        'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
        'traffic light', 'parking meter'
    ],
    'Menjar': [
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 
        'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 
        'hot dog', 'pizza', 'donut', 'cake', 'dining table'
    ],
    'Tècnica': [
        'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
        'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
        'scissors', 'teddy bear', 'hair drier', 'toothbrush', 'chair', 'couch',
        'bed', 'toilet', 'fire hydrant', 'stop sign', 'frisbee', 'skis',
        'snowboard', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
        'tennis racket', 'handbag', 'tie', 'suitcase'
    ]
}

# Crear carpetes base en el directori actual
BASE_DIR = Path(__file__).parent

def setup_directories():
    """Crear directoris per a cada categoria si no existeixen"""
    for category in CATEGORIES.keys():
        category_dir = BASE_DIR / category
        category_dir.mkdir(exist_ok=True)
    return BASE_DIR

# ==================== CONFIGURACIÓ DE STREAMLIT ====================
st.set_page_config(
    page_title="Classificador d'Imatges AI",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialitzar session state
if 'manual_selections' not in st.session_state:
    st.session_state.manual_selections = {}

st.title("🖼️ Classificador Automàtic d'Imatges")
st.markdown("Classificació intel·ligent amb YOLOv8")

# ==================== FUNCIONS ====================

@st.cache_resource
def load_yolo_model():
    """Carregar el model YOLOv8 en memòria cau"""
    try:
        model_path = BASE_DIR / "yolov8n.pt"
        if not model_path.exists():
            st.error(f"❌ Model no trobat a: {model_path}")
            st.stop()
        return YOLO(str(model_path))
    except Exception as e:
        st.error(f"Error carregant el model: {e}")
        st.stop()

def classify_image(image_path, model):
    """Classificar una imatge usant YOLOv8 i retornar objectes detectats"""
    try:
        results = model.predict(source=str(image_path), conf=0.3, verbose=False)
        detected_objects = []
        
        if results and len(results) > 0:
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        class_name = model.names[class_id]
                        confidence = float(box.conf[0])
                        detected_objects.append({
                            'name': class_name,
                            'confidence': confidence
                        })
        
        return detected_objects
    except Exception as e:
        st.error(f"Error classificant la imatge: {e}")
        return []

def get_category_for_detections(detected_objects):
    """Determinar la categoria segons els objectes detectats amb lògica avançada"""
    if not detected_objects:
        return None  # Retornar None si no hi ha deteccions
    
    # Contar deteccions per classe
    class_counts = {}
    for detected in detected_objects:
        obj_name = detected['name'].lower()
        if obj_name not in class_counts:
            class_counts[obj_name] = {'count': 0, 'confidence': 0}
        class_counts[obj_name]['count'] += 1
        class_counts[obj_name]['confidence'] += detected['confidence']
    
    # Puntuació per categoria (combinant comptes i confiança)
    category_scores = {cat: 0 for cat in CATEGORIES.keys()}
    
    for obj_name, stats in class_counts.items():
        count = stats['count']
        avg_confidence = stats['confidence'] / count
        
        # Buscar a quina categoria pertany aquest objecte
        for category, class_names in CATEGORIES.items():
            if obj_name in class_names:
                # Ponderar: confiança + bonus per múltiples deteccions
                # Si detectem múltiples objectes de la mateixa clase, és més segur
                score = avg_confidence * (1 + (count - 1) * 0.3)
                category_scores[category] += score
                break
    
    # LÒGICA ESPECIAL: Evitar falsos positius
    # Si detectem persones però també hi ha molts altres objectes, probablement no és "Persones"
    if 'person' in class_counts:
        person_detections = class_counts['person']['count']
        total_detections = sum(stats['count'] for stats in class_counts.values())
        
        # Si les persones són menys del 40% de les deteccions, reduïr la seva puntuació
        if person_detections < total_detections * 0.4:
            category_scores['Persones'] *= 0.3  # Penalitzar fortement
    
    # LÒGICA ESPECIAL: Detecció de Menjar
    # Si detectem objectes de menjar (plats, begudes, menjar), és menjar
    menjar_objects = {'bowl', 'cup', 'fork', 'knife', 'spoon', 'banana', 'apple', 
                      'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 
                      'donut', 'cake', 'wine glass', 'bottle'}
    detected_menjar = [obj for obj in class_counts.keys() if obj in menjar_objects]
    if len(detected_menjar) > 0:
        # Si detectem articles de menjar, incrementar significativament
        # Usar max per evitar que 0 * 2.5 = 0
        current_score = category_scores['Menjar']
        category_scores['Menjar'] = max(current_score * 2.5, 0.8)
    
    # Retornar la categoria amb puntuació més alta
    max_score = max(category_scores.values())
    if max_score > 0:
        best_category = max(category_scores, key=category_scores.get)
        return best_category
    else:
        return None  # Retornar None si cap categoria té puntuació

def copy_image_to_category(image_file, category):
    """Copiar la imatge a la carpeta de categoria amb nom únic"""
    try:
        category_dir = BASE_DIR / category
        category_dir.mkdir(exist_ok=True)
        
        # Crear nom de fitxer únic usant UUID
        destination = category_dir / image_file.name
        
        # Si el fitxer ja existeix, afegir UUID
        if destination.exists():
            name, ext = os.path.splitext(image_file.name)
            unique_id = str(uuid.uuid4())[:8]
            destination = category_dir / f"{name}_{unique_id}{ext}"
        
        # Desar la imatge
        image = Image.open(image_file)
        image.save(str(destination))
        
        return str(destination)
    except Exception as e:
        st.error(f"Error guardant la imatge: {e}")
        return None

def get_category_stats():
    """Obtenir estadístiques de cada categoria"""
    stats = {}
    for category in CATEGORIES.keys():
        category_dir = BASE_DIR / category
        image_files = [f for f in category_dir.glob("*") 
                      if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']]
        stats[category] = len(image_files)
    return stats

def open_folder(path):
    """Obrir carpeta en l'explorador"""
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path])
        else:  # Linux
            subprocess.run(["xdg-open", path])
        return True
    except Exception as e:
        st.error(f"Error obrint la carpeta: {e}")
        return False

def draw_detections_on_image(image, detected_objects, model):
    """Dibuixar les deteccions en la imatge"""
    try:
        results = model.predict(source=image, conf=0.3, verbose=False)
        if results and len(results) > 0:
            annotated_image = results[0].plot()
            return Image.fromarray(annotated_image)
    except:
        pass
    return image

# ==================== INTERFÍCIE PRINCIPAL ====================

# Setup directories
setup_directories()

# Cargar el model
model = load_yolo_model()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.subheader("⚙️ Configuració")
    
    st.markdown("### 📁 Ubicació de les imatges")
    st.code(str(BASE_DIR))
    
    if st.button("📂 Obrir carpeta"):
        if open_folder(str(BASE_DIR)):
            st.success("Carpeta oberta!")
    
    st.divider()
    
    st.markdown("### 📊 Estadístiques actuals")
    stats = get_category_stats()
    for category, count in stats.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(category)
        with col2:
            st.metric("", count)
    
    st.divider()
    
    # Botó per esborrar totes les imatges
    if st.button("🗑️ Netejar totes les categories", type="secondary"):
        try:
            for category in CATEGORIES.keys():
                category_dir = BASE_DIR / category
                for file in category_dir.glob("*"):
                    if file.is_file():
                        file.unlink()
            st.success("✅ Totes les categories han estat netejades")
            st.rerun()
        except Exception as e:
            st.error(f"Error netejant: {e}")

# ==================== SECCIÓ PRINCIPAL ====================

tab1, tab2 = st.tabs(["📤 Classificar Imatges", "📂 Veure Carpetes"])

with tab1:
    st.subheader("Puja imatges per classificar")
    
    uploaded_files = st.file_uploader(
        "Selecciona una o més imatges",
        type=['png', 'jpg', 'jpeg', 'bmp'],
        accept_multiple_files=True,
        key="uploader"
    )
    
    if uploaded_files:
        st.markdown(f"### 📸 Has seleccionat **{len(uploaded_files)}** imatge(s)")
        
        # Mostrar preview de les imatges
        preview_cols = st.columns(3)
        for idx, file in enumerate(uploaded_files):
            with preview_cols[idx % 3]:
                st.image(file, caption=file.name, use_container_width=True)
        
        st.divider()
        
        # Botó per classificar
        if st.button("🚀 Classificar i guardar imatges", type="primary"):
            progress_bar = st.progress(0)
            status_placeholder = st.empty()
            results_container = st.container()
            
            classification_results = []
            total_files = len(uploaded_files)
            
            with results_container:
                st.subheader("📋 Resultats de la classificació")
            
            for idx, uploaded_file in enumerate(uploaded_files):
                # Actualitzar progres
                progress = (idx + 1) / total_files
                progress_bar.progress(progress)
                status_placeholder.info(f"Processant: {uploaded_file.name} ({idx + 1}/{total_files})")
                
                try:
                    # Crear imatge temporal amb UUID únic
                    temp_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
                    temp_image_path = Path(tempfile.gettempdir()) / temp_filename
                    image = Image.open(uploaded_file)
                    image.save(str(temp_image_path))
                    
                    # Classificar la imatge
                    detected_objects = classify_image(temp_image_path, model)
                    category = get_category_for_detections(detected_objects)
                    is_manual = False
                    
                    # Si no es pot classificar automàticament, demanar al usuari
                    if category is None:
                        progress_bar.empty()
                        status_placeholder.empty()
                        
                        st.warning(f"⚠️ No s'ha pogut classificar automàticament: **{uploaded_file.name}**")
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write("**Objectes detectats:**")
                            if detected_objects:
                                for det in detected_objects:
                                    st.write(f"- {det['name']}: {det['confidence']:.1%}")
                            else:
                                st.write("Cap detecció específica")
                        
                        with col2:
                            st.write("**Selecciona manualment:**")
                            category = st.selectbox(
                                "Categoria:",
                                CATEGORIES.keys(),
                                key=f"manual_{idx}_{uploaded_file.name}"
                            )
                            is_manual = True
                        
                        # Retornar progress bar
                        progress_bar = st.progress(progress)
                        status_placeholder = st.empty()
                        status_placeholder.info(f"Processant: {uploaded_file.name} ({idx + 1}/{total_files})")
                    
                    # Guardar la imatge
                    saved_path = copy_image_to_category(uploaded_file, category) if category else None
                    
                    # Neteja el fitxer temporal
                    try:
                        if temp_image_path.exists():
                            temp_image_path.unlink()
                    except:
                        pass
                    
                    if saved_path:
                        result = {
                            'file': uploaded_file.name,
                            'category': category,
                            'detections': detected_objects,
                            'success': True,
                            'manual': is_manual
                        }
                    else:
                        result = {
                            'file': uploaded_file.name,
                            'category': category,
                            'detections': detected_objects,
                            'success': False,
                            'manual': is_manual
                        }
                    
                    classification_results.append(result)
                    
                except Exception as e:
                    classification_results.append({
                        'file': uploaded_file.name,
                        'category': 'Error',
                        'detections': [],
                        'success': False,
                        'error': str(e),
                        'manual': False
                    })
            
            # Mostrar resultats
            progress_bar.empty()
            status_placeholder.empty()
            
            st.success("✅ Classificació completada!")
            
            # Taula de resultats
            col1, col2, col3 = st.columns(3)
            with col1:
                successful = sum(1 for r in classification_results if r['success'])
                st.metric("Imatges guardades", successful)
            with col2:
                failed = sum(1 for r in classification_results if not r['success'])
                if failed > 0:
                    st.metric("Errors", failed)
            with col3:
                st.metric("Total processades", len(classification_results))
            
            st.divider()
            
            # Detalls de cada imatge
            st.subheader("📝 Detalls de cada imatge")
            for result in classification_results:
                icon = "✅" if result['success'] else "❌"
                manual_tag = " (manual)" if result.get('manual') else " (automàtica)"
                with st.expander(f"{icon} {result['file']}{manual_tag}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Categoria:** {result['category']}")
                        st.write(f"**Estat:** {'✅ Guardada' if result['success'] else '❌ Error'}")
                        if result.get('manual'):
                            st.write("**Classificació:** 🖐️ Manual")
                        else:
                            st.write("**Classificació:** 🤖 Automàtica")
                    with col2:
                        if result['detections']:
                            st.write("**Objectes detectats:**")
                            for det in result['detections']:
                                st.write(f"- {det['name']}: {det['confidence']:.1%}")
                        else:
                            st.write("**Objectes detectats:** Cap detecció específica")

with tab2:
    st.subheader("Veure imatges per categoria")
    
    category_selector = st.selectbox("Selecciona una categoria", CATEGORIES.keys())
    
    category_dir = BASE_DIR / category_selector
    image_files = sorted([f for f in category_dir.glob("*") 
                         if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']])
    
    if image_files:
        st.markdown(f"### 📸 {category_selector} ({len(image_files)} imatges)")
        
        # Mostrar imatges en graella
        cols = st.columns(3)
        for idx, image_file in enumerate(image_files):
            with cols[idx % 3]:
                image = Image.open(image_file)
                st.image(image, caption=image_file.name, use_container_width=True)
                
                # Botó per eliminar
                if st.button(f"🗑️ Eliminar", key=f"delete_{image_file.name}"):
                    try:
                        image_file.unlink()
                        st.success(f"Eliminada: {image_file.name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error eliminant: {e}")
    else:
        st.info(f"📭 No hi ha imatges a la categoria '{category_selector}'")
    
    st.divider()
    
    # Estadístiques finals
    st.subheader("📊 Estadístiques de la categoria")
    stats = get_category_stats()
    
    # Gràfic d'estadístiques
    chart_data = {cat: count for cat, count in stats.items()}
    st.bar_chart(chart_data)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; font-size: 0.8em; color: gray;'>
    🤖 Classificador automàtic d'imatges amb YOLOv8 | Actualització en temps real
</div>
""", unsafe_allow_html=True)
