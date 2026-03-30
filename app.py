import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="wide")

# 2. CSS UNIFICATO E SICURO (Menu visibile, bottoni grandi, layout pulito)
st.markdown("""
<style>
    /* Spaziatura corretta per non coprire i tab in alto */
    .block-container { padding-top: 4rem !important; }
    
    /* Stile testo prodotti */
    .prod-name { font-size: 24px !important; font-weight: 800; color: #1E1E1E; display: block; line-height: 1.2; }
    .prod-info { font-size: 16px !important; color: #666; display: block; margin-top: 4px; }
    .prod-user { font-size: 13px !important; color: #007BFF; font-style: italic; }
    
    /* Immagini tonde e fisse */
    .prod-img { width: 90px !important; height: 90px !important; object-fit: cover; border-radius: 15px; border: 1px solid #EEE; }
    
    /* Bottoni Grandi per il pollice */
    div.stButton > button {
        width: 100% !important;
        height: 60px !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: 2px solid #333 !important;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 3. GESTIONE DATI (Connessione e Pulizia) - AGGIORNATO
conn = st.connection("gsheets", type=GSheetsConnection)

def save_data():
    conn.update(worksheet="Catalogo", data=st.session_state.df)

if 'df' not in st.session_state:
    raw_df = conn.read(worksheet="Catalogo")
    
    # Pulizia Prodotto
    raw_df['Prodotto'] = raw_df['Prodotto'].astype(str).str.strip()
    raw_df = raw_df[~raw_df['Prodotto'].isin(['nan', '', 'None'])]
    
    # FORZIAMO LE CORSIE A ESSERE TESTO (Evita l'errore di sorting)
    raw_df['Corsia'] = raw_df['Corsia'].astype(str).str.strip().replace('nan', '?')
    
    st.session_state.df = raw_df.reset_index(drop=True)

utente_attuale = "Lorenzo"

# --- 4. STRUTTURA TAB ---
tab_lista, tab_spesa, tab_catalogo = st.tabs(["🏠 LISTA", "🛒 SPESA", "📦 CATALOGO"])

# Definizione dell'ordine logico del supermercato
ORDINE_CORSIE = {
    "Ortofrutta": 0, "Frighi": 1, "Pescheria": 2, "Gastronomia": 3,
    "Corsia 5": 4, "Corsia 4": 5, "Corsia 3": 6, "Corsia 2": 7, "Corsia 1": 8,
    "Macelleria": 9, "Surgelati": 10
}

def sort_by_aisle(df):
    """Funzione di supporto per ordinare il DF secondo il percorso Borello"""
    # Creiamo una colonna temporanea per l'ordinamento
    # Se una corsia non è in lista, la mettiamo in fondo (99)
    df['sort_idx'] = df['Corsia'].map(ORDINE_CORSIE).fillna(99)
    return df.sort_values('sort_idx').drop(columns=['sort_idx'])
    
# ==========================================
# TAB 1: LISTA (Cosa dobbiamo comprare)
# ==========================================
with tab_lista:
    st.subheader("📝 Da acquistare")
    
    # ... (parte expander aggiunta manuale invariata) ...

    st.divider()
    
    items_in_list = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy()
    
    if items_in_list.empty:
        st.info("La lista è vuota.")
    else:
        # Applichiamo l'ordine del supermercato
        items_in_list = sort_by_aisle(items_in_list)
        
        for idx, row in items_in_list.iterrows():
            with st.container(border=True):
                col_txt, col_img = st.columns([0.7, 0.3])
                with col_txt:
                    st.markdown(f'<span class="prod-name">{row["Prodotto"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span class="prod-info">📍 {row["Corsia"]}</span>', unsafe_allow_html=True)
                    # RIMOSSO: User info
                with col_img:
                    url = row.get('URL_Foto', "")
                    if pd.notna(url) and str(url).startswith("http"):
                        st.markdown(f'<img src="{url}" class="prod-img">', unsafe_allow_html=True)
                
                if st.button("❌ RIMUOVI", key=f"L_remove_{idx}"):
                    if row['Tipo'] == "Manuale":
                        st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
                    else:
                        st.session_state.df.at[idx, 'Stato'] = ""
                    save_data()
                    st.rerun()
                    
# ==========================================
# TAB 2: SPESA (IN NEGOZIO - LAYOUT UNIFICATO)
# ==========================================
with tab_spesa:
    st.subheader("🛒 Al Supermercato")
    
    df_spesa = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy()
    
    if df_spesa.empty:
        st.success("Tutto preso! 🎉")
    else:
        # Applichiamo l'ordine del supermercato
        df_spesa = sort_by_aisle(df_spesa)
        
        for idx, row in df_spesa.iterrows():
            with st.container(border=True):
                col_txt, col_img = st.columns([0.7, 0.3])
                with col_txt:
                    st.markdown(f'<span class="prod-name">{row["Prodotto"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span class="prod-info">📍 {row["Corsia"]}</span>', unsafe_allow_html=True)
                with col_img:
                    url = row.get('URL_Foto', "")
                    if pd.notna(url) and str(url).startswith("http"):
                        st.markdown(f'<img src="{url}" class="prod-img">', unsafe_allow_html=True)
                
                if st.button(f"✅ PRESO!", key=f"S_check_{idx}"):
                    st.session_state.df.at[idx, 'Stato'] = "NEL CARRELLO"
                    save_data()
                    st.rerun()

# ==========================================
# TAB 3: CATALOGO (Ricerca e Aggiunta)
# ==========================================
with tab_catalogo:
    st.subheader("📦 Catalogo")
    search = st.text_input("Cerca prodotto...", key="search_bar")
    
    # Ordine Alfabetico per il catalogo
    df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy().sort_values("Prodotto")
           
    if search:
        df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False, na=False)]
    
    for idx, row in df_cat.iterrows():
        is_in_list = row['Stato'] == "DA COMPRARE"
        
        with st.container(border=True):
            col_txt, col_img = st.columns([0.7, 0.3])
            with col_txt:
                color = "#AAA" if is_in_list else "#000"
                st.markdown(f'<span class="prod-name" style="color:{color}">{row["Prodotto"]}</span>', unsafe_allow_html=True)
                st.markdown(f'<span class="prod-info">📍 Corsia: {row["Corsia"]}</span>', unsafe_allow_html=True)
            with col_img:
                url = row.get('URL_Foto', "")
                if pd.notna(url) and str(url).startswith("http"):
                    st.markdown(f'<img src="{url}" class="prod-img">', unsafe_allow_html=True)
            
            if is_in_list:
                st.button("🛒 GIÀ IN LISTA", key=f"C_in_{idx}", disabled=True)
            else:
                if st.button("➕ AGGIUNGI", key=f"C_add_{idx}"):
                    st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                    st.session_state.df.at[idx, 'User'] = utente_attuale
                    save_data()
                    st.rerun()
