import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione Pagina
st.set_page_config(page_title="Borello Shopping", page_icon="icona_spesa.png", layout="centered")

# CSS per uno stile pulito e leggibile su mobile
st.markdown("""
    <style>
    .stCheckbox { font-size: 1.2rem !important; padding: 5px 0; }
    h3 { color: #4b5320; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 20px; }
    .stPopover button { background-color: transparent; border: none; padding: 0; }
    </style>
    """, unsafe_allow_html=True)

st.image("icona_spesa.png", width=80)
st.title("🛒 Lista Spesa Borello")

# 2. Connessione ai Dati
conn = st.connection("gsheets", type=GSheetsConnection)

# Lettura del foglio "Catalogo"
df = conn.read(worksheet="Catalogo")

# Pulizia: rimuoviamo le righe dove la colonna 'Prodotto' è vuota
if 'Prodotto' in df.columns:
    df = df.dropna(subset=['Prodotto'])
    
    if df.empty:
        st.info("Il catalogo è vuoto. Aggiungi prodotti su Google Sheets!")
    else:
        # Raggruppiamo i prodotti per Corsia
        for corsia in sorted(df['Corsia'].unique().astype(str)):
            nome_corsia = corsia if corsia != "nan" else "Altro"
            st.subheader(f"📍 {nome_corsia}")
            
            prod_corsia = df[df['Corsia'].astype(str) == corsia]
            
            for index, row in prod_corsia.iterrows():
                col_check, col_info = st.columns([0.85, 0.15])
                
                with col_check:
                    # Visualizza il nome del prodotto
                    st.checkbox(f"{row['Prodotto']}", key=f"p_{index}")
                
                with col_info:
                    # Se esiste un URL foto valido, mostra l'icona
                    url_foto = str(row['URL_Foto'])
                    if url_foto.startswith("http"):
                        with st.popover("🖼️"):
                            st.image(url_foto, caption=row['Prodotto'])
else:
    st.error("Errore: La colonna 'Prodotto' non è stata trovata nel foglio Google.")

st.divider()
st.caption("Progetto Spesa Smart - Borello")
