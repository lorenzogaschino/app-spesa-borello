import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Borello Smart Shopping", page_icon="icona_spesa.png", layout="centered")

# CSS Personalizzato per i colori Borello e icone
st.markdown("""
    <style>
    .stApp { background-color: #f9f9f9; }
    h1, h2, h3 { color: #4b5320; }
    .stButton>button { width: 100%; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNESSIONE DATI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Carica il catalogo e assicura che le colonne extra esistano
    df = conn.read(worksheet="Catalogo")
    df = df.dropna(subset=['Prodotto'])
    for col in ['Stato', 'User', 'Tipo']:
        if col not in df.columns:
            df[col] = ""
    return df

df = load_data()

# --- NAVIGAZIONE LATERALE ---
with st.sidebar:
    st.image("icona_spesa.png", width=100)
    st.title("Menu")
    scelta = st.radio("Dove vuoi andare?", ["🏠 A CASA", "🛒 BORELLO", "📦 PRODOTTI"])
    
    st.divider()
    # Selezione Utente (per sapere chi aggiunge i prodotti)
    utente = st.selectbox("Chi sei?", ["Lorenzo", "Maria", "Ospite"])
    icone_utenti = {"Lorenzo": "🧔‍♂️", "Maria": "👩‍🦰", "Ospite": "👤"}

# --- SEZIONE 3: PRODOTTI (Catalogo Completo) ---
if scelta == "📦 PRODOTTI":
    st.header("📦 Database Prodotti")
    st.write("Qui puoi consultare tutto il catalogo Borello.")
    
    # Ricerca rapida
    search = st.text_input("Cerca un prodotto nel catalogo...", "")
    
    # Filtro e ordinamento per Corsia
    df_sorted = df.sort_values(by="Corsia")
    if search:
        df_sorted = df_sorted[df_sorted['Prodotto'].str.contains(search, case=False)]

    for corsia in df_sorted['Corsia'].unique():
        with st.expander(f"📍 Corsia: {corsia}", expanded=True):
            items = df_sorted[df_sorted['Corsia'] == corsia]
            for _, row in items.iterrows():
                col1, col2, col3 = st.columns([0.15, 0.65, 0.2])
                with col1:
                    # Mini anteprima foto
                    if pd.notna(row['URL_Foto']) and str(row['URL_Foto']).startswith("http"):
                        st.image(row['URL_Foto'], width=50)
                with col2:
                    st.write(f"**{row['Prodotto']}**")
                with col3:
                    # Tasto rapido per aggiungere alla lista (Logica A CASA)
                    if st.button("➕", key=f"add_{row['ID']}"):
                        st.toast(f"{row['Prodotto']} aggiunto!")
                        # Qui aggiungeremo la logica per scrivere sul foglio Google

# --- SEZIONE 1: A CASA (Placeholder) ---
elif scelta == "🏠 A CASA":
    st.header("🏠 Crea la tua Lista")
    st.info("Seleziona i prodotti dal menu PRODOTTI o usa la ricerca qui sotto.")
    # Svilupperemo questa parte nel prossimo step

# --- SEZIONE 2: BORELLO (Placeholder) ---
elif scelta == "🛒 BORELLO":
    st.header("🛒 Shopping Mode")
    st.write(f"Ciao {utente}, sei pronto per la spesa?")
    # Svilupperemo questa parte nel prossimo step
