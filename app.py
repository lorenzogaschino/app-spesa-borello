import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione Pagina
st.set_page_config(page_title="Borello Shopping", page_icon="icona_spesa.png", layout="centered")

# CSS per uno stile pulito
st.markdown("""
    <style>
    .stCheckbox { font-size: 1.2rem !important; }
    h3 { color: #4b5320; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.image("icona_spesa.png", width=80)
st.title("🛒 Lista Spesa Borello")

# 2. Connessione ai Dati
conn = st.connection("gsheets", type=GSheetsConnection)

# Leggiamo il foglio e rimuoviamo le righe completamente vuote
df = conn.read(worksheet="Catalogo")
df = df.dropna(subset=['Prodotto']) # Elimina righe dove il nome prodotto manca

# 3. Visualizzazione Logica
if df.empty:
    st.info("Il catalogo è vuoto. Aggiungi prodotti su Google Sheets!")
else:
    # Raggruppiamo per Corsia per dare ordine
    for corsia in df['Corsia'].unique():
        # Gestiamo il caso in cui la corsia sia vuota
        nome_corsia = corsia if pd.notna(corsia) else "Altro"
        st.subheader(f"📍 {nome_corsia}")
        
        prod_corsia = df[df['Corsia'] == corsia]
        for index, row in prod_corsia.iterrows():
            col_check, col_info = st.columns([0.8, 0.2])
            
            with col_check:
                # Scrittura pulita: Nome Prodotto
                st.checkbox(f"{row['Prodotto']}", key=f"p_{index}")
            
            with col_info:
                # Se c'è la foto, mostra un piccolo popover
                if pd.notna(row['URL_Foto']) and str(row['URL_Foto']).startswith("http"):
                    with st.popover("🖼️"):
                        st.image(row['URL_Foto'], caption=row['Prodotto'])

st.divider()
st.caption("Progetto Spesa Smart - Istanza Separata")
