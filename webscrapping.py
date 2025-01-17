import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date
import urllib3
import warnings

# Desactivar advertències SSL i altres warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

def scrape_pitch_cat(data_inici, data_fi):
    url = "http://pitch.cat/noticies/index.php?cat=70"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        with st.spinner('Obtenint dades...'):
            response = requests.get(url, headers=headers, verify=False)
            
            if response.status_code != 200:
                st.error(f"Error en accedir a la web. Codi d'estat: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            dates = []
            titols = []
            descripcions = []
            enllacos = []
            
            noticies = soup.find_all('div', class_='noticia')
            
            for noticia in noticies:
                try:
                    # Buscar la data en l'element h6
                    data_element = noticia.find('h6')
                    if not data_element:
                        continue
                        
                    data_text = data_element.text.strip()
                    # Convertir el format de data de DD.MM.YYYY a DD/MM/YYYY
                    data_parts = data_text.split('.')
                    if len(data_parts) == 3:
                        data_text = f"{data_parts[0]}/{data_parts[1]}/{data_parts[2]}"
                    
                    try:
                        data_noticia = datetime.strptime(data_text, '%d/%m/%Y').date()
                    except ValueError:
                        continue
                    
                    if data_inici <= data_noticia <= data_fi:
                        dates.append(data_text)
                        
                        # Buscar el títol en l'element h5 > a
                        titol_element = noticia.find('h5').find('a')
                        titols.append(titol_element.text.strip() if titol_element else "Sense títol")
                        
                        # Buscar la descripció en el div directe
                        desc_element = noticia.find('div', recursive=False)
                        descripcions.append(desc_element.text.strip() if desc_element else "Sense descripció")
                        
                        # Buscar l'enllaç en h5 > a
                        link_element = noticia.find('h5').find('a')
                        if link_element and link_element.get('href'):
                            enllac_complet = f"http://pitch.cat/noticies/{link_element['href']}"
                        else:
                            enllac_complet = "Enllaç no disponible"
                        enllacos.append(enllac_complet)
                        
                except Exception as e:
                    continue
            
            if not dates:
                st.info("No s'han trobat notícies en l'interval de dates seleccionat")
                return pd.DataFrame()
                
            df = pd.DataFrame({
                'Data': dates,
                'Títol': titols,
                'Descripció': descripcions,
                'Enllaç': enllacos
            })
            
            return df
            
    except Exception as e:
        st.error(f"Error en el scraping: {str(e)}")
        return None

def main():
    st.title("Scraper de Notícies Pitch&Putt")
    
    # Afegir informació sobre la seguretat
    st.info("""
    ℹ️ Nota: Aquesta aplicació accedeix a una web HTTP (no segura). 
    Les dades es recullen de manera segura però el navegador pot mostrar advertències.
    """)
    
    # Moure els controls de dates a la columna principal
    col1, col2 = st.columns(2)
    
    with col1:
        data_inici = st.date_input(
            "Data d'inici",
            date(2024, 1, 1),
            key="data_inici"
        )
    
    with col2:
        data_fi = st.date_input(
            "Data final",
            date.today(),
            key="data_fi"
        )
    
    # Botó de cerca al centre
    col_button = st.columns([1, 2, 1])[1]
    with col_button:
        cerca = st.button("🔍 Cercar Notícies", use_container_width=True)
    
    # Separador visual
    st.markdown("---")
    
    if cerca:
        if data_inici > data_fi:
            st.error("❌ La data d'inici no pot ser posterior a la data final")
        else:
            with st.spinner("Cercant notícies..."):
                df = scrape_pitch_cat(data_inici, data_fi)
                
                if df is not None and not df.empty:
                    # Guardar els resultats a la sessió
                    st.session_state.last_results = df
                    st.session_state.last_dates = (data_inici, data_fi)
                    
                    # Mostrar resum
                    st.success(f"✅ S'han trobat {len(df)} notícies entre {data_inici} i {data_fi}")
                    
                    # Pestanyes per diferents vistes
                    tab1, tab2 = st.tabs(["📊 Taula", "🔗 Enllaços"])
                    
                    with tab1:
                        st.dataframe(df, use_container_width=True)
                        
                        # Botó de descàrrega
                        csv = df.to_csv(index=False).encode('utf-8')
                        nom_arxiu = f'noticies_seniors_{data_inici}_{data_fi}.csv'
                        
                        st.download_button(
                            label="📥 Descarregar CSV",
                            data=csv,
                            file_name=nom_arxiu,
                            mime='text/csv',
                            use_container_width=True
                        )
                    
                    with tab2:
                        for index, row in df.iterrows():
                            st.markdown(f"**{row['Data']}**: [{row['Títol']}]({row['Enllaç']})")
                
                elif df is not None and df.empty:
                    st.warning("⚠️ No s'han trobat notícies en aquest interval de dates")
    
    # Mostrar els últims resultats si existeixen
    elif 'last_results' in st.session_state:
        df = st.session_state.last_results
        data_inici, data_fi = st.session_state.last_dates
        
        st.info(f"📌 Mostrant els últims resultats ({data_inici} - {data_fi})")
        
        tab1, tab2 = st.tabs(["📊 Taula", "🔗 Enllaços"])
        
        with tab1:
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            nom_arxiu = f'noticies_seniors_{data_inici}_{data_fi}.csv'
            
            st.download_button(
                label="📥 Descarregar CSV",
                data=csv,
                file_name=nom_arxiu,
                mime='text/csv',
                use_container_width=True
            )
        
        with tab2:
            for index, row in df.iterrows():
                st.markdown(f"**{row['Data']}**: [{row['Títol']}]({row['Enllaç']})")

if __name__ == "__main__":
    main()
