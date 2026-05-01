import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAZIONE E AUTO-REFRESH (Per multi-utente)
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="centered")

if st_autorefresh:
    # Refresh ogni 30 secondi per vedere i prodotti aggiunti dagli altri in tempo reale
    st_autorefresh(interval=10000, key="datarefresh")

# # 2. CSS UNIFICATO (Forzatura Definitiva Layout Orizzontale)
st.markdown("""
<style>
    .stApp { margin-top: -50px; }
    .block-container { padding-top: 2rem !important; max-width: 550px !important; }
    
    /* Uniformità Intestazioni */
    .mobile-header-container { display: flex; align-items: baseline; gap: 8px; margin-bottom: 15px; }
    .header-text { font-size: 22px !important; font-weight: 700; color: #111; }
    .count-text { font-size: 18px !important; color: #2e7d32; font-weight: 600; }

    /* Card Prodotto */
    .product-card {
        background-color: #ffffff; border-radius: 10px; padding: 10px;
        margin-bottom: 5px; border: 1px solid #eee; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .product-header { display: flex; justify-content: space-between; align-items: center; }
    .prod-name { font-size: 16px !important; font-weight: 700; color: #111; }
    .prod-img { width: 50px !important; height: 50px !important; object-fit: cover; border-radius: 8px; }
    
    /* FORZATURA ORIZZONTALE COLONNE (Risolve il problema delle due righe) */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 8px !important; /* Spazio tra i due bottoni */
    }

    [data-testid="column"] {
        flex: 1 1 50% !important; /* Forza ogni colonna al 50% */
        min-width: 0px !important;
    }
    
    /* Stile Bottoni Compatti */
    div.stButton > button {
        width: 100% !important;
        height: 38px !important;
        font-size: 11px !important; /* Ridotto leggermente per sicurezza */
        font-weight: bold !important;
        padding: 0px 2px !important;
        white-space: nowrap !important;
        text-overflow: clip !important;
    }

    /* Bordi Corsie */
    .border-ortofrutta { border-left: 5px solid #2ecc71 !important; }
    .border-frigo { border-left: 5px solid #3498db !important; }
    .border-carne { border-left: 5px solid #e74c3c !important; }
    .border-generico { border-left: 5px solid #f1c40f !important; }
</style>
""", unsafe_allow_html=True)

# 3. GESTIONE DATI (Connessione e Sincronizzazione)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # ttl=0 garantisce che ogni utente veda i dati aggiornati degli altri
    df = conn.read(worksheet="Catalogo", ttl=0)
    df = df.dropna(subset=['Prodotto'])
    df['Prodotto'] = df['Prodotto'].astype(str).str.strip()
    df['Stato'] = df['Stato'].fillna('')
    df['Corsia'] = df['Corsia'].fillna('?').astype(str).str.strip()
    return df.reset_index(drop=True)

def save_data(df):
    conn.update(worksheet="Catalogo", data=df)
    st.session_state.df = df

if 'df' not in st.session_state:
    st.session_state.df = load_data()

utente_attuale = "Lorenzo" # Potresti rendere questo dinamico con un st.sidebar.selectbox

# 4. LOGICA DI ORDINAMENTO
ORDINE_CORSIE = {
    "Ortofrutta": 0, "Frighi": 1, "Pescheria": 2, "Gastronomia": 3,
    "Corsia 5": 4, "Corsia 4": 5, "Corsia 3": 6, "Corsia 2": 7, "Corsia 1": 8,
    "Macelleria": 9, "Surgelati": 10
}

def get_color_class(corsia):
    c = str(corsia).lower()
    if "ortofrutta" in c: return "border-ortofrutta"
    if any(x in c for x in ["frighi", "surgelati"]): return "border-frigo"
    if any(x in c for x in ["macelleria", "pescheria", "gastronomia"]): return "border-carne"
    return "border-generico"

def sort_df(df):
    df['sort_idx'] = df['Corsia'].map(ORDINE_CORSIE).fillna(99)
    return df.sort_values('sort_idx').drop(columns=['sort_idx'])

def rimuovi_prodotto(idx, row):
    """Gestisce la rimozione logica (catalogo) o fisica (manuale) di un prodotto."""
    if row['Tipo'] == "Manuale":
        # Se è un inserimento manuale, lo eliminiamo del tutto
        st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
    else:
        # Se è da catalogo, resettiamo solo lo stato e l'utente
        st.session_state.df.at[idx, 'Stato'] = ""
        st.session_state.df.at[idx, 'User'] = ""
    save_data(st.session_state.df)
    st.rerun()

# --- TABS ---
tab_lista, tab_spesa, tab_catalogo = st.tabs(["🏠 LISTA", "🛒 SPESA", "📦 CATALOGO"])

# TAB 1: LISTA
with tab_lista:
    df_lista = sort_df(st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy())
    
   # Contatore dinamico ottimizzato per layout mobile
    count_lista = len(df_lista)
    st.markdown(f"""
        <div class="mobile-header-container">
            <span class="header-text">📝 Da acquistare</span>
            <span class="count-text">({count_lista} prodotti)</span>
        </div>
        """, unsafe_allow_html=True) 
    
    with st.expander("➕ Aggiungi prodotto non in catalogo"):
        m_nome = st.text_input("Cosa serve?", key="manual_add_name")
        m_corsia = st.selectbox("In quale corsia?", list(ORDINE_CORSIE.keys()) + ["?"], key="manual_add_corsia")
        if st.button("Aggiungi ora", key="manual_add_btn"):
            new_row = pd.DataFrame([{"Prodotto": m_nome, "Corsia": m_corsia, "Stato": "DA COMPRARE", "Tipo": "Manuale", "User": utente_attuale}])
            save_data(pd.concat([st.session_state.df, new_row], ignore_index=True))
            st.rerun()

    st.divider()
    for idx, row in df_lista.iterrows():
        img_html = f'<img src="{row["URL_Foto"]}" class="prod-img">' if pd.notna(row.get("URL_Foto")) and str(row["URL_Foto"]).startswith("http") else ""
        st.markdown(f'''<div class="product-card {get_color_class(row["Corsia"])}"><div class="product-header">
            <div><div class="prod-name">{row["Prodotto"]}</div><div class="prod-info">📍 {row["Corsia"]}</div></div>
            {img_html}</div></div>''', unsafe_allow_html=True)
        
        # Tasto rimuovi singolo per la lista
        if st.button("❌ RIMUOVI", key=f"L_rem_{idx}"):
            rimuovi_prodotto(idx, row)
            
# TAB 2: SPESA
with tab_spesa:
    df_spesa = sort_df(st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy())
    
for idx, row in df_spesa.iterrows():
            img_html = f'<img src="{row["URL_Foto"]}" class="prod-img">' if pd.notna(row.get("URL_Foto")) and str(row["URL_Foto"]).startswith("http") else ""
            st.markdown(f'''<div class="product-card {get_color_class(row["Corsia"])}"><div class="product-header">
                <div><div class="prod-name">{row["Prodotto"]}</div><div class="prod-info">📍 {row["Corsia"]}</div></div>
                {img_html}</div></div>''', unsafe_allow_html=True)
            
            # Creazione colonne: il CSS sopra impedirà che vadano a capo
            c1, c2 = st.columns(2, gap="small")
            with c1:
                if st.button("✅ PRESO", key=f"S_buy_{idx}"):
                    st.session_state.df.at[idx, 'Stato'] = "NEL CARRELLO"
                    save_data(st.session_state.df)
                    st.rerun()
            with c2:
                if st.button("❌ RIMUOVI", key=f"S_rem_{idx}"):
                    rimuovi_prodotto(idx, row)
            
            # Corretto: gap="small" è il valore minimo supportato da Streamlit
            col1, col2 = st.columns(2, gap="small")
            with col1:
                if st.button("✅ PRESO", key=f"S_buy_{idx}"):
                    st.session_state.df.at[idx, 'Stato'] = "NEL CARRELLO"
                    save_data(st.session_state.df)
                    st.rerun()
            with col2:
                if st.button("❌ RIMUOVI", key=f"S_rem_{idx}"):
                    rimuovi_prodotto(idx, row)

    if not st.session_state.df[st.session_state.df['Stato'].isin(["DA COMPRARE", "NEL CARRELLO"])].empty:
        st.divider()
        if st.button("🏁 FINISCI SPESA E SVUOTA", type="primary", key="finish_btn"):
            st.session_state.df.loc[st.session_state.df['Stato'].isin(["DA COMPRARE", "NEL CARRELLO"]), 'Stato'] = ""
            st.session_state.df = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].reset_index(drop=True)
            save_data(st.session_state.df)
            st.rerun()

# TAB 3: CATALOGO (Ripristinato: Immagini, Utente e tasto Disabilitato)
with tab_catalogo:
    st.subheader("📦 Catalogo")
    search = st.text_input("Cerca prodotto...", key="search_bar")
    df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy().sort_values("Prodotto")
    if search:
        df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False, na=False)]
    
    for idx, row in df_cat.iterrows():
        is_in = row['Stato'] == "DA COMPRARE"
        color = "#AAA" if is_in else "#111"
        img_html = f'<img src="{row["URL_Foto"]}" class="prod-img">' if pd.notna(row.get("URL_Foto")) and str(row["URL_Foto"]).startswith("http") else ""
        
        st.markdown(f'''<div class="product-card {get_color_class(row["Corsia"])}"><div class="product-header">
            <div><div class="prod-name" style="color:{color}">{row["Prodotto"]}</div><div class="prod-info">📍 Corsia: {row["Corsia"]}</div></div>
            {img_html}</div></div>''', unsafe_allow_html=True)
        
        if is_in:
            st.button("🛒 IN LISTA", key=f"C_in_{idx}", disabled=True)
        else:
            if st.button("➕ AGGIUNGI", key=f"C_add_{idx}"):
                st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                st.session_state.df.at[idx, 'User'] = utente_attuale
                save_data(st.session_state.df)
                st.rerun()
