import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_autorefresh import st_autorefresh # Necessario per sync multi-utente

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="centered")

# Auto-refresh ogni 30 secondi per sincronizzare gli utenti senza ricaricare l'intera pagina manualmente
st_autorefresh(interval=30000, key="datarefresh")

# 2. CSS OTTIMIZZATO PER MOBILE
st.markdown("""
<style>
    .stApp { margin-top: -60px; }
    .block-container { padding-top: 1rem !important; max-width: 500px !important; }
    
    /* Stickiness dei Tab migliorata */
    .stTabs [data-baseweb="tab-list"] {
        position: sticky; top: 0; z-index: 999;
        background-color: white; padding: 5px 0;
    }

    .product-card {
        background-color: #ffffff; border-radius: 12px;
        padding: 15px; margin-bottom: 0px;
        border: 1px solid #f0f0f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .product-header { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
    .prod-name { font-size: 1.1rem !important; font-weight: 700; color: #111; }
    .prod-info { font-size: 0.9rem !important; color: #777; margin-top: 2px; }
    .prod-img { width: 65px !important; height: 65px !important; object-fit: cover; border-radius: 10px; background-color: #f9f9f9; }
    
    /* Bottoni Touch-Friendly */
    div.stButton > button {
        width: 100% !important; height: 48px !important;
        font-weight: 600 !important; border-radius: 10px !important;
        margin-top: 6px !important; margin-bottom: 18px !important;
        border: none !important; transition: transform 0.1s;
    }
    div.stButton > button:active { transform: scale(0.98); }

    .border-ortofrutta { border-left: 6px solid #2ecc71 !important; }
    .border-frigo { border-left: 6px solid #3498db !important; }
    .border-carne { border-left: 6px solid #e74c3c !important; }
    .border-generico { border-left: 6px solid #f1c40f !important; }
</style>
""", unsafe_allow_html=True)

# 3. LOGICA DATI (CRUD)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_all_data():
    """Legge i dati dal cloud senza usare la cache per garantire il multi-utente"""
    try:
        df = conn.read(worksheet="Catalogo", ttl=0)
        df = df.dropna(subset=['Prodotto'])
        df['Prodotto'] = df['Prodotto'].astype(str).str.strip()
        df['Corsia'] = df['Corsia'].astype(str).fillna('?').str.strip()
        df['Stato'] = df['Stato'].fillna('')
        return df
    except Exception as e:
        st.error(f"Errore connessione: {e}")
        return pd.DataFrame()

def save_and_sync(df):
    """Salva su Google Sheets e aggiorna lo stato locale"""
    conn.update(worksheet="Catalogo", data=df)
    st.session_state.df = df

# Caricamento Iniziale
if 'df' not in st.session_state or st.sidebar.button("🔄 Forza Sincronizzazione"):
    st.session_state.df = load_all_data()

utente_attuale = "Lorenzo"

# --- 4. FUNZIONI DI SUPPORTO ---
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

def get_sorted_list(df, filter_status):
    subset = df[df['Stato'] == filter_status].copy()
    subset['sort_idx'] = subset['Corsia'].map(ORDINE_CORSIE).fillna(99)
    return subset.sort_values('sort_idx')

# --- 5. INTERFACCIA ---
tab_lista, tab_spesa, tab_catalogo = st.tabs(["📝 LISTA", "🛒 SPESA", "📦 CATALOGO"])

# TAB 1: LISTA
with tab_lista:
    with st.expander("➕ Aggiungi al volo"):
        nome = st.text_input("Nome prodotto")
        corsia = st.selectbox("Corsia", list(ORDINE_CORSIE.keys()) + ["?"])
        if st.button("Inserisci"):
            new_item = pd.DataFrame([{"Prodotto": nome, "Corsia": corsia, "Stato": "DA COMPRARE", "Tipo": "Manuale", "User": utente_attuale}])
            save_and_sync(pd.concat([st.session_state.df, new_item], ignore_index=True))
            st.rerun()

    lista_acquisto = get_sorted_list(st.session_state.df, "DA COMPRARE")
    if lista_acquisto.empty:
        st.info("Nulla da comprare. Aggiungi dal Catalogo!")
    else:
        for idx, row in lista_acquisto.iterrows():
            img_html = f"<img src='{row['URL_Foto']}' class='prod-img'>" if pd.notnull(row.get('URL_Foto')) and str(row['URL_Foto']).startswith('http') else "<div></div>"
            st.markdown(f'''<div class="product-card {get_style(row['Corsia'])}"><div class="product-header">
                <div><div class="prod-name">{row["Prodotto"]}</div><div class="prod-info">📍 {row["Corsia"]}</div></div>
                {img_html}</div></div>''', unsafe_allow_html=True)
            if st.button("❌ Rimuovi", key=f"del_{idx}"):
                if row['Tipo'] == "Manuale":
                    st.session_state.df = st.session_state.df.drop(idx)
                else:
                    st.session_state.df.at[idx, 'Stato'] = ""
                save_and_sync(st.session_state.df)
                st.rerun()

# TAB 2: SPESA
with tab_spesa:
    spesa_attiva = get_sorted_list(st.session_state.df, "DA COMPRARE")
    if spesa_attiva.empty:
        st.success("Tutto preso! 🎉")
    else:
        for idx, row in spesa_attiva.iterrows():
            st.markdown(f'''<div class="product-card {get_style(row['Corsia'])}"><div class="product-header">
                <div><div class="prod-name">{row["Prodotto"]}</div><div class="prod-info">📍 {row["Corsia"]}</div></div>
                </div></div>''', unsafe_allow_html=True)
            if st.button(f"✅ PRESO", key=f"buy_{idx}"):
                st.session_state.df.at[idx, 'Stato'] = "NEL CARRELLO"
                save_and_sync(st.session_state.df)
                st.rerun()

    if not st.session_state.df[st.session_state.df['Stato'] == "NEL CARRELLO"].empty:
        st.divider()
        if st.button("🏁 CONCLUDI E PULISCI", type="primary"):
            mask = st.session_state.df['Stato'].isin(["DA COMPRARE", "NEL CARRELLO"])
            st.session_state.df.loc[mask, 'Stato'] = ""
            # Rimuove i manuali definitivi al termine
            final_df = st.session_state.df[~((st.session_state.df['Tipo'] == 'Manuale') & (st.session_state.df['Stato'] == ""))].reset_index(drop=True)
            save_and_sync(final_df)
            st.rerun()

# TAB 3: CATALOGO
with tab_catalogo:
    query = st.text_input("Cerca nel catalogo...", placeholder="Esempio: Latte")
    cat_df = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].sort_values("Prodotto")
    if query:
        cat_df = cat_df[cat_df['Prodotto'].str.contains(query, case=False)]
    
    for idx, row in cat_df.iterrows():
        gia_in = row['Stato'] == "DA COMPRARE"
        st.markdown(f'''<div class="product-card {get_style(row['Corsia'])}"><div class="product-header">
            <div style="opacity: {0.5 if gia_in else 1}"><div class="prod-name">{row["Prodotto"]}</div><div class="prod-info">📍 {row["Corsia"]}</div></div>
            </div></div>''', unsafe_allow_html=True)
        if not gia_in:
            if st.button("➕ Aggiungi", key=f"cat_add_{idx}"):
                st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                save_and_sync(st.session_state.df)
                st.rerun()
