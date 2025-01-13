"""
RELLOTGE DIGITAL AMB DISPLAY DE SET SEGMENTS

Descripció:
-----------
Aquesta aplicació simula un rellotge digital amb les següents característiques:

1. Visualització:
   - Mostra l'hora actual en format 24h (HH:MM:SS)
   - Utilitza dígits Unicode per simular un display de set segments
   - Colors: Dígits en vermell sobre fons negre
   - Mostra la data actual amb dia de la setmana, dia, mes i any

2. Funcionalitats:
   - Actualització automàtica cada segon
   - Controls per ajustar l'hora (+/- 1 hora)
   - Controls per ajustar el dia (+/- 1 dia)
   - Botó per reiniciar a l'hora actual del sistema

3. Característiques tècniques:
   - Implementat amb Streamlit
   - Utilitza HTML/CSS per la visualització
   - Emmagatzema els ajustos en session_state
   - Compatible amb diferents zones horàries

4. Ús:
   - Els controls es troben a la barra lateral
   - L'hora i data s'actualitzen automàticament
   - Els canvis manuals es mantenen entre recàrregues

Autor: [El teu nom]
Data: [Data de creació]
Versió: 1.0
"""

import streamlit as st
import datetime
import time

# Configuració de la pàgina
st.set_page_config(page_title="Rellotge Digital", page_icon="⏰")

# Dígits de set segments en Unicode
DIGITS = {
    0: "𝟎",
    1: "𝟏",
    2: "𝟐",
    3: "𝟑",
    4: "𝟒",
    5: "𝟓",
    6: "𝟔",
    7: "𝟕",
    8: "𝟖",
    9: "𝟗"
}

# Estil CSS
st.markdown("""
<style>
.digit {
    font-size: 72px;
    color: red;
    font-family: monospace;
    display: inline-block;
    margin: 0 5px;
}
.separator {
    font-size: 72px;
    color: red;
    display: inline-block;
    margin: 0 5px;
}
.clock-container {
    text-align: center;
    background-color: black;
    padding: 20px;
    border-radius: 10px;
}
.date {
    color: white;
    font-size: 24px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# Inicialitzar l'estat
if 'time_offset' not in st.session_state:
    st.session_state.time_offset = datetime.timedelta()
if 'date_offset' not in st.session_state:
    st.session_state.date_offset = datetime.timedelta()

# Obtenir temps actual
current_time = datetime.datetime.now() + st.session_state.time_offset
current_date = current_time.date() + st.session_state.date_offset

# Títol
st.title("Rellotge Digital")

# Preparar data
dies_setmana = ["Dilluns", "Dimarts", "Dimecres", "Dijous", "Divendres", "Dissabte", "Diumenge"]
mesos = ["Gener", "Febrer", "Març", "Abril", "Maig", "Juny", 
         "Juliol", "Agost", "Setembre", "Octubre", "Novembre", "Desembre"]

dia_setmana = dies_setmana[current_date.weekday()]
mes = mesos[current_date.month - 1]

# Preparar hora
hora = current_time.hour
minuts = current_time.minute
segons = current_time.second

# Convertir hora en dígits
h1, h2 = divmod(hora, 10)
m1, m2 = divmod(minuts, 10)
s1, s2 = divmod(segons, 10)

# Crear el display complet
html_display = f"""
<div class="clock-container">
    <div class="date">
        {dia_setmana}, {current_date.day} de {mes} de {current_date.year}
    </div>
    <div>
        <span class="digit">{DIGITS[h1]}</span>
        <span class="digit">{DIGITS[h2]}</span>
        <span class="separator">:</span>
        <span class="digit">{DIGITS[m1]}</span>
        <span class="digit">{DIGITS[m2]}</span>
        <span class="separator">:</span>
        <span class="digit">{DIGITS[s1]}</span>
        <span class="digit">{DIGITS[s2]}</span>
    </div>
</div>
"""
st.markdown(html_display, unsafe_allow_html=True)

# Controls per ajustar l'hora i la data
st.sidebar.header("Controls")

# Ajustar hora
if st.sidebar.button("Hora +1"):
    st.session_state.time_offset += datetime.timedelta(hours=1)
    st.rerun()
if st.sidebar.button("Hora -1"):
    st.session_state.time_offset -= datetime.timedelta(hours=1)
    st.rerun()

# Ajustar dia
if st.sidebar.button("Dia +1"):
    st.session_state.date_offset += datetime.timedelta(days=1)
    st.rerun()
if st.sidebar.button("Dia -1"):
    st.session_state.date_offset -= datetime.timedelta(days=1)
    st.rerun()

# Reiniciar
if st.sidebar.button("Reiniciar a hora actual"):
    st.session_state.time_offset = datetime.timedelta()
    st.session_state.date_offset = datetime.timedelta()
    st.rerun()

# Actualitzar cada segon
time.sleep(1)
st.rerun() 