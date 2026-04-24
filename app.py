import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Tentativo di importazione sicura per evitare il crash visualizzato nello screenshot
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st.warning("⚠️ Componente 'streamlit-autorefresh' non trovato. L'app non si aggiornerà da sola. Aggiungilo al file requirements.txt!")
    def st_autorefresh(**kwargs): pass # Funzione vuota per non bloccare l'app

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="centered")

# Auto-refresh ogni 30 secondi (solo se la libreria è presente)
st_autorefresh(interval=30000, key="datarefresh")

# --- CSS OTTIMIZZATO ---
st.markdown("""
<style>
    .stApp { margin-top: -60px; }
    .block-container { padding-top: 1rem !important; max-width: 500px !important; }
    .stTabs [data-baseweb="tab-list"] { position: sticky; top: 0; z-index: 999; background-color: white; }
    .product-card {
        background-color: #ffffff; border-radius: 12px;
        padding: 15px; margin-bottom: 0px; border: 1px solid #f0f0f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .product-header { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
    .prod-name { font-size: 1.1rem !important; font-weight: 700; color: #111; }
    .prod-img { width: 65px !important; height: 65px !important; object-fit: cover; border-radius: 10px; }
    div.stButton > button { width: 100% !important; height: 48px !important; font-weight: 600; border-radius: 10px !important; }
    .border-ortofrutta { border-left: 6px solid #2ecc71 !important; }
    .border-frigo { border-left: 6px solid #3498db !important; }
    .border-carne { border-left: 6px solid #e74c3c !important; }
    .border-generico { border-left: 6px solid #f1c40f !important; }
</style>
""", unsafe_allow_html=True)

# --- CONNESSIONE E DATI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # ttl=0 è vitale per vedere le modifiche fatte dagli altri utenti immediatamente
    df = conn.read(worksheet="Catalogo", ttl=0)
    df = df.dropna(subset=['Prodotto'])
    df['Prodotto'] = df['Prodotto'].astype(str).str.strip()
    df['Stato'] = df['Stato'].fillna('')
    df['Corsia'] = df['Corsia'].fillna('?').astype(str)
    return df.reset_index(drop=True)

def save_data(df):
    conn.update(worksheet="Catalogo", data=df)
    st.session_state.df = df

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- FUNZIONI DI ORDINE ---
ORDINE_CORSIE = {
    "Ortofrutta": 0, "Frighi": 1, "Pescheria": 2, "Gastronomia": 3,
    "Corsia 5": 4, "Corsia 4": 5, "Corsia 3": 6, "Corsia 2": 7, "Corsia 1": 8,
    "Macelleria": 9, "Surgelati": 10
}

def get_style(corsia):
    c = str(corsia).lower()
    if "ortofrutta" in c: return "border-ortofrutta"
    if any(x in c for x in ["frighi", "surgelati"]): return "border-frigo"
    if any(x in c for x in ["macelleria", "pescheria", "gastronomia"]): return "border-carne"
    return "border-generico"

# --- INTERFACCIA TABS ---
tab_lista, tab_spesa, tab_catalogo = st.tabs(["📝 LISTA", "🛒 SPESA", "📦 CATALOGO"])

with tab_lista:
    st.subheader("Da acquistare")
    # Filtro prodotti DA COMPRARE
    df_lista = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy()
    
    if df_lista.empty:
        st.info("La lista è vuota!")
    else:
        # Ordinamento dinamico per corsia
        df_lista['sort'] = df_lista['Corsia'].map(ORDINE_CORSIE).fillna(99)
        df_lista = df_lista.sort_values('sort')
        
        for idx, row in df_lista.iterrows():
            st.markdown(f'''<div class="product-card {get_style(row['Corsia'])}"><div class="product-header">
                <div><div class="prod-name">{row["Prodotto"]}</div><div style="color:gray">📍 {row["Corsia"]}</div></div>
                </div></div>''', unsafe_allow_html=True)
            if st.button("❌ Rimuovi", key=f"del_{idx}"):
                st.session_state.df.at[idx, 'Stato'] = ""
                save_data(st.session_state.df)
                st.rerun()

with tab_spesa:
    # Stessa logica di visualizzazione per la spesa attiva
    df_shopping = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy()
    if df_shopping.empty:
        st.success("Spesa completata! 🎉")
    else:
        df_shopping['sort'] = df_shopping['Corsia'].map(ORDINE_CORSIE).fillna(99)
        for idx, row in df_shopping.sort_values('sort').iterrows():
            st.markdown(f'''<div class="product-card {get_style(row['Corsia'])}"><div class="product-header">
                <div><div class="prod-name">{row["Prodotto"]}</div></div>
                </div></div>''', unsafe_allow_html=True)
            if st.button("✅ PRESO", key=f"buy_{idx}"):
                st.session_state.df.at[idx, 'Stato'] = "NEL CARRELLO"
                save_data(st.session_state.df)
                st.rerun()

with tab_catalogo:
    search = st.text_input("Cerca nel catalogo")
    # Mostra solo i prodotti non manuali (quelli fissi)
    df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy()
    if search:
        df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False)]
    
    for idx, row in df_cat.sort_values("Prodotto").iterrows():
        gia_in = row['Stato'] == "DA COMPRARE"
        st.markdown(f'''<div class="product-card {get_style(row['Corsia'])}">
            <div class="prod-name" style="opacity: {0.4 if gia_in else 1}">{row["Prodotto"]}</div>
            </div>''', unsafe_allow_html=True)
        if not gia_in:
            if st.button("➕ Aggiungi", key=f"add_{idx}"):
                st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                save_data(st.session_state.df)
                st.rerun()
