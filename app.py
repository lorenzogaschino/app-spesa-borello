import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAZIONE PAGINA
# Usiamo layout="centered" per evitare che su schermi grandi il testo si disperda troppo a sinistra
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="centered")

# 2. CSS UNIFICATO E SICURO (Ripristino Menu e Layout Compatto)
st.markdown("""
<style>
    /* Rimuove il padding eccessivo che nascondeva i Tab */
    .stApp { margin-top: -50px; } /* Recupera spazio in alto */
    
    .block-container { 
        padding-top: 2rem !important; 
        max-width: 550px !important; 
    }
    
    /* Forza la visibilità della barra dei Tab */
    .stTabs [data-baseweb="tab-list"] {
        position: sticky;
        top: 0;
        z-index: 1000;
        background-color: white;
        padding-top: 10px;
    }

    /* Scheda prodotto compatta a strati */
    .product-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 0px; /* Ridotto per il layout a strati */
        border: 1px solid #eee;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Header: Nome/Info a sinistra, Foto a destra */
    .product-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .prod-name { font-size: 18px !important; font-weight: 700; color: #111; line-height: 1.2; }
    .prod-info { font-size: 14px !important; color: #666; }
    .prod-img { width: 60px !important; height: 60px !important; object-fit: cover; border-radius: 8px; }
    
    /* Bottone largo subito sotto la scheda (Layout a strati) */
    div.stButton > button {
        width: 100% !important;
        height: 42px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        font-size: 15px !important;
        margin-top: 4px !important;
        margin-bottom: 15px !important;
    }
</style>
""", unsafe_allow_html=True)
/* Colori bordi per categoria */
    .border-ortofrutta { border-left: 5px solid #2ecc71 !important; }
    .border-frigo { border-left: 5px solid #3498db !important; }
    .border-carne { border-left: 5px solid #e74c3c !important; }
    .border-generico { border-left: 5px solid #f1c40f !important; }  
                     
# 3. GESTIONE DATI (Connessione e Pulizia)
conn = st.connection("gsheets", type=GSheetsConnection)

def save_data():
    conn.update(worksheet="Catalogo", data=st.session_state.df)

if 'df' not in st.session_state:
    raw_df = conn.read(worksheet="Catalogo")
    
    # Pulizia Prodotto: rimuove righe vuote o 'nan' dallo sheet
    raw_df['Prodotto'] = raw_df['Prodotto'].astype(str).str.strip()
    raw_df = raw_df[~raw_df['Prodotto'].isin(['nan', '', 'None'])]
    
    # Blindatura Corsie: evita errori di sorting se ci sono celle vuote
    raw_df['Corsia'] = raw_df['Corsia'].astype(str).str.strip().replace('nan', '?')
    
    st.session_state.df = raw_df.reset_index(drop=True)

utente_attuale = "Lorenzo"

# --- 4. STRUTTURA TAB (Ora visibili in alto) ---
tab_lista, tab_spesa, tab_catalogo = st.tabs(["🏠 LISTA", "🛒 SPESA", "📦 CATALOGO"])

# Definizione dell'ordine logico del supermercato
ORDINE_CORSIE = {
    "Ortofrutta": 0, "Frighi": 1, "Pescheria": 2, "Gastronomia": 3,
    "Corsia 5": 4, "Corsia 4": 5, "Corsia 3": 6, "Corsia 2": 7, "Corsia 1": 8,
    "Macelleria": 9, "Surgelati": 10
}

def sort_by_aisle(df):
    """Ordina il DataFrame seguendo il percorso fisico del negozio"""
    # Mappa le corsie ai numeri; se la corsia è ignota (?), va in fondo (99)
    df['sort_idx'] = df['Corsia'].map(ORDINE_CORSIE).fillna(99)
    return df.sort_values('sort_idx').drop(columns=['sort_idx'])  
                       
# ==========================================
# TAB 1: LISTA (Cosa dobbiamo comprare)
# ==========================================
with tab_lista:
    st.subheader("📝 Da acquistare")
    
    # Recupero logica Aggiunta Manuale
    with st.expander("➕ Aggiungi prodotto non in catalogo"):
        m_nome = st.text_input("Cosa serve?")
        m_corsia = st.selectbox("In quale corsia?", list(ORDINE_CORSIE.keys()) + ["?"])
        if st.button("Aggiungi ora"):
            new_row = pd.DataFrame([{"Prodotto": m_nome, "Corsia": m_corsia, "Stato": "DA COMPRARE", "Tipo": "Manuale", "User": utente_attuale}])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            save_data()
            st.rerun()

    st.divider()
    items_in_list = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy()
    
    if items_in_list.empty:
        st.info("La lista è vuota.")
    else:
        items_in_list = sort_by_aisle(items_in_list)
        for idx, row in items_in_list.iterrows():
            # NUOVO LAYOUT A STRATI
            st.markdown(f'''
                <div class="product-card">
                    <div class="product-header">
                        <div>
                            <div class="prod-name">{row["Prodotto"]}</div>
                            <div class="prod-info">📍 {row["Corsia"]}</div>
                        </div>
                        {"<img src='" + row['URL_Foto'] + "' class='prod-img'>" if pd.notna(row.get('URL_Foto')) and str(row['URL_Foto']).startswith('http') else ""}
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            
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
        df_spesa = sort_by_aisle(df_spesa)
        for idx, row in df_spesa.iterrows():
            st.markdown(f'''
                <div class="product-card">
                    <div class="product-header">
                        <div>
                            <div class="prod-name">{row["Prodotto"]}</div>
                            <div class="prod-info">📍 {row["Corsia"]}</div>
                        </div>
                        {"<img src='" + row['URL_Foto'] + "' class='prod-img'>" if pd.notna(row.get('URL_Foto')) and str(row['URL_Foto']).startswith('http') else ""}
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            
            if st.button(f"✅ PRESO!", key=f"S_check_{idx}"):
                st.session_state.df.at[idx, 'Stato'] = "NEL CARRELLO"
                save_data()
                st.rerun()

    # Logica Reset Finale
    if not st.session_state.df[st.session_state.df['Stato'].isin(["DA COMPRARE", "NEL CARRELLO"])].empty:
        st.divider()
        if st.button("🏁 FINISCI SPESA E SVUOTA", type="primary"):
            st.session_state.df.loc[st.session_state.df['Stato'].isin(["DA COMPRARE", "NEL CARRELLO"]), 'Stato'] = ""
            st.session_state.df = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].reset_index(drop=True)
            save_data()
            st.rerun()

# ==========================================
# TAB 3: CATALOGO (Ricerca e Aggiunta)
# ==========================================
with tab_catalogo:
    st.subheader("📦 Catalogo")
    search = st.text_input("Cerca prodotto...", key="search_bar")
    df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy().sort_values("Prodotto")
    if search:
        df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False, na=False)]
    
    for idx, row in df_cat.iterrows():
        is_in = row['Stato'] == "DA COMPRARE"
        color = "#AAA" if is_in else "#111"
        
        st.markdown(f'''
            <div class="product-card">
                <div class="product-header">
                    <div>
                        <div class="prod-name" style="color:{color}">{row["Prodotto"]}</div>
                        <div class="prod-info">📍 Corsia: {row["Corsia"]}</div>
                    </div>
                    {"<img src='" + row['URL_Foto'] + "' class='prod-img'>" if pd.notna(row.get('URL_Foto')) and str(row['URL_Foto']).startswith('http') else ""}
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        if is_in:
            st.button("🛒 IN LISTA", key=f"C_in_{idx}", disabled=True)
        else:
            if st.button("➕ AGGIUNGI", key=f"C_add_{idx}"):
                st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                st.session_state.df.at[idx, 'User'] = utente_attuale
                save_data()
                st.rerun()
