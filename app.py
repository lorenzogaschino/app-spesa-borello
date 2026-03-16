import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Borello Shopping", page_icon="icona_spesa.png")

st.image("icona_spesa.png", width=80)
st.title("🛒 Lista Spesa Borello")

conn = st.connection("gsheets", type=GSheetsConnection)

# Carichiamo i dati
df = conn.read(worksheet="Catalogo")

# --- PARTE DI DEBUG: Rimuovila quando l'app funziona ---
if st.checkbox("Mostra dati tecnici (Debug)"):
    st.write("Colonne trovate:", df.columns.tolist())
    st.dataframe(df)
# -------------------------------------------------------

# Pulizia: rimuoviamo righe dove la colonna 'Prodotto' è vuota
if 'Prodotto' in df.columns:
    df = df.dropna(subset=['Prodotto'])
    
    if df.empty:
        st.info("Il foglio è connesso ma non trovo prodotti nella colonna 'Prodotto'.")
    else:
        for index, row in df.iterrows():
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.checkbox(f"{row['Prodotto']} ({row['Corsia']})", key=f"p_{index}")
            with col2:
                # Usiamo il link che mi hai mandato
                if pd.notna(row['URL_Foto']):
                    with st.popover("🖼️"):
                        st.image(row['URL_Foto'])
else:
    st.error("Errore: Non trovo la colonna chiamata 'Prodotto'. Controlla il foglio Google!")
