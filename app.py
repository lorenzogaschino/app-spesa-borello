import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione Pagina
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="wide")

# CSS Migliorato per Mobile
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        height: 45px; background-color: #f0f2f6; 
        border-radius: 10px; flex-grow: 1; font-size: 14px;
    }
    .stTabs [aria-selected="true"] { background-color: #4b5320 !important; color: white !important; }
    .stButton>button { width: 100%; border-radius: 10px; }
    div[data-testid="stExpander"] { border: none; background: #fafafa; border-radius: 10px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Connessione e Gestione Dati
conn = st.connection("gsheets", type=GSheetsConnection)

# Utilizziamo lo session_state per evitare troppe letture dal DB
if 'df' not in st.session_state:
    raw_df = conn.read(worksheet="Catalogo")
    raw_df['Corsia'] = raw_df['Corsia'].astype(str)
    # Assicuriamoci che le colonne esistano
    for col in ['Stato', 'User', 'Tipo']:
        if col not in raw_df.columns: raw_df[col] = ""
    st.session_state.df = raw_df

def save_to_gsheets():
    conn.update(worksheet="Catalogo", data=st.session_state.df)

# 3. Header
col_logo, col_user = st.columns([0.2, 0.8])
with col_logo:
    st.write("🛒") # Sostituisci con st.image se preferisci
with col_user:
    utente = st.selectbox("Utente:", ["Lorenzo", "Maria"], label_visibility="collapsed")

# 4. MENU TABS
tab1, tab2, tab3 = st.tabs(["🏠 LISTA", "🛒 SPESA", "📦 CATALOGO"])

# --- TAB 3: CATALOGO (Aggiunta prodotti) ---
with tab3:
    st.subheader("📦 Catalogo Prodotti")
    search = st.text_input("Cerca...", placeholder="Es: Mele")
    
    df_cat = st.session_state.df.copy()
    if search:
        df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False)]

    for corsia in sorted(df_cat['Corsia'].unique()):
        with st.expander(f"📍 Corsia {corsia}"):
            items = df_cat[df_cat['Corsia'] == corsia]
            for idx, row in items.iterrows():
                c1, c2, c3 = st.columns([0.2, 0.6, 0.2])
                with c1:
                    # Piccolo check per URL immagine
                    st.write("📷" if pd.isna(row.get('URL_Foto')) else "🖼️")
                with c2:
                    st.write(f"**{row['Prodotto']}**")
                with c3:
                    if st.button("➕", key=f"add_{idx}"):
                        st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                        st.session_state.df.at[idx, 'User'] = utente
                        save_to_gsheets()
                        st.toast(f"{row['Prodotto']} aggiunto!")

# --- TAB 1: LISTA (Cosa manca a casa) ---
with tab1:
    st.subheader("📝 Da comprare")
    lista_casa = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"]
    
    if lista_casa.empty:
        st.info("La lista è vuota.")
    else:
        for idx, row in lista_casa.iterrows():
            st.write(f"• **{row['Prodotto']}** (da: {row['User']})")
        
        if st.button("🗑️ Svuota Lista"):
            st.session_state.df['Stato'] = ""
            save_to_gsheets()
            st.rerun()

# --- TAB 2: SPESA (In negozio) ---
with tab2:
    st.subheader("🛒 Nel Carrello")
    # Filtriamo solo i prodotti da comprare, ordinati per corsia (logica del percorso nel supermercato)
    spesa_df = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].sort_values("Corsia")
    
    if spesa_df.empty:
        st.success("Tutto preso! 🎉")
    else:
        for idx, row in spesa_df.iterrows():
            c_check, c_text = st.columns([0.2, 0.8])
            with c_check:
                # Se premuto, il prodotto viene segnato come COMPRATO (Stato vuoto)
                if st.button("✅", key=f"buy_{idx}"):
                    st.session_state.df.at[idx, 'Stato'] = "PRESO"
                    save_to_gsheets()
                    st.rerun()
            with c_text:
                st.write(f"**{row['Prodotto']}**")
                st.caption(f"Corsia {row['Corsia']}")
