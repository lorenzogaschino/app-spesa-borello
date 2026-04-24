import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Tentativo di importazione sicura per il refresh
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="centered")

if st_autorefresh:
    st_autorefresh(interval=30000, key="datarefresh")

# 2. CSS OTTIMIZZATO (Incluso stile per immagini)
st.markdown("""
<style>
    .stApp { margin-top: -60px; }
    .block-container { padding-top: 1rem !important; max-width: 500px !important; }
    
    .product-card {
        background-color: #ffffff; border-radius: 12px;
        padding: 12px; margin-bottom: 0px; border: 1px solid #f0f0f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .product-header { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
    .prod-name { font-size: 1.1rem !important; font-weight: 700; color: #111; line-height: 1.2; }
    .prod-info { font-size: 0.85rem !important; color: #777; }
    
    /* Gestione Immagine: Quadrata e proporzionata */
    .prod-img { 
        width: 60px !important; 
        height: 60px !important; 
        object-fit: cover; 
        border-radius: 8px; 
        background-color: #f8f9fa;
    }
    
    div.stButton > button { 
        width: 100% !important; height: 42px !important; 
        font-weight: 600; border-radius: 10px !important; 
        margin-top: 5px !important; margin-bottom: 15px !important;
    }

    .border-ortofrutta { border-left: 6px solid #2ecc71 !important; }
    .border-frigo { border-left: 6px solid #3498db !important; }
    .border-carne { border-left: 6px solid #e74c3c !important; }
    .border-generico { border-left: 6px solid #f1c40f !important; }
</style>
""", unsafe_allow_html=True)

# 3. GESTIONE DATI
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(worksheet="Catalogo", ttl=0)
    df = df.dropna(subset=['Prodotto'])
    df['Prodotto'] = df['Prodotto'].astype(str).str.strip()
    df['Stato'] = df['Stato'].fillna('')
    df['Corsia'] = df['Corsia'].fillna('?').astype(str)
    # Assicuriamoci che URL_Foto esista nel DF
    if 'URL_Foto' not in df.columns:
        df['URL_Foto'] = ""
    return df.reset_index(drop=True)

def save_data(df):
    conn.update(worksheet="Catalogo", data=df)
    st.session_state.df = df

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# 4. LOGICA VISUALE
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

def render_product_card(row):
    """Funzione centralizzata per renderizzare la card con immagine"""
    img_url = row.get('URL_Foto', "")
    img_html = f'<img src="{img_url}" class="prod-img">' if pd.notna(img_url) and str(img_url).startswith('http') else '<div></div>'
    
    st.markdown(f'''
        <div class="product-card {get_style(row['Corsia'])}">
            <div class="product-header">
                <div>
                    <div class="prod-name">{row["Prodotto"]}</div>
                    <div class="prod-info">📍 {row["Corsia"]}</div>
                </div>
                {img_html}
            </div>
        </div>
    ''', unsafe_allow_html=True)

# 5. INTERFACCIA TABS
tab_lista, tab_spesa, tab_catalogo = st.tabs(["📝 LISTA", "🛒 SPESA", "📦 CATALOGO"])

with tab_lista:
    df_lista = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy()
    if df_lista.empty:
        st.info("Lista vuota.")
    else:
        df_lista['sort'] = df_lista['Corsia'].map(ORDINE_CORSIE).fillna(99)
        for idx, row in df_lista.sort_values('sort').iterrows():
            render_product_card(row)
            if st.button("❌ Rimuovi", key=f"del_{idx}"):
                st.session_state.df.at[idx, 'Stato'] = ""
                save_data(st.session_state.df)
                st.rerun()

with tab_spesa:
    df_spesa = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy()
    if df_spesa.empty:
        st.success("Tutto preso! 🎉")
    else:
        df_spesa['sort'] = df_spesa['Corsia'].map(ORDINE_CORSIE).fillna(99)
        for idx, row in df_spesa.sort_values('sort').iterrows():
            render_product_card(row)
            if st.button("✅ PRESO", key=f"buy_{idx}"):
                st.session_state.df.at[idx, 'Stato'] = "NEL CARRELLO"
                save_data(st.session_state.df)
                st.rerun()

with tab_catalogo:
    search = st.text_input("Cerca nel catalogo")
    df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy()
    if search:
        df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False)]
    
    for idx, row in df_cat.sort_values("Prodotto").iterrows():
        gia_in = row['Stato'] == "DA COMPRARE"
        # Opacità ridotta se già in lista
        st.write(f'<div style="opacity: {0.4 if gia_in else 1}">', unsafe_allow_html=True)
        render_product_card(row)
        st.write('</div>', unsafe_allow_html=True)
        if not gia_in:
            if st.button("➕ Aggiungi", key=f"add_{idx}"):
                st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                save_data(st.session_state.df)
                st.rerun()
