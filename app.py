import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione Pagina
st.set_page_config(page_title="Borello Shopping", page_icon="🛒", layout="centered")

# 2. CSS per Mobile (Pulsanti grandi e icone leggibili)
st.markdown("""
    <style>
    div.stButton > button { width: 100%; height: 3em; border-radius: 10px; font-weight: bold; }
    .stCheckbox { font-size: 1.2rem; padding: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛒 Lista Spesa Borello")

# 3. Connessione ai Dati
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Catalogo")

# 4. Visualizzazione Logica
if df.empty:
    st.info("Il catalogo è vuoto. Aggiungi il primo prodotto su Google Sheets!")
else:
    # Esempio di visualizzazione semplice per test
    for index, row in df.iterrows():
        col_check, col_info = st.columns([0.8, 0.2])
        with col_check:
            st.checkbox(f"{row['Prodotto']} (Corsia: {row['Corsia']})", key=f"p_{index}")
        with col_info:
            if row['URL_Foto']:
                with st.popover("🖼️"):
                    st.image(row['URL_Foto'], caption=row['Prodotto'])

st.divider()
st.caption("Progetto Spesa Smart - Istanza Separata")
