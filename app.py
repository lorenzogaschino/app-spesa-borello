import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione Pagina (Mobile First)
st.set_page_config(page_title="Borello Smart", page_icon="icona_spesa.png", layout="wide")

# CSS per menu orizzontale e stile mobile
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; white-space: pre-wrap; background-color: #f0f2f6; 
        border-radius: 10px 10px 0 0; padding: 10px; flex-grow: 1;
    }
    .stTabs [aria-selected="true"] { background-color: #4b5320 !important; color: white !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; }
    [data-testid="stImage"] img { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Connessione Dati
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(worksheet="Catalogo")
    df = df.dropna(subset=['Prodotto'])
    # RISOLUZIONE ERRORE: Trasforma tutto in testo per poter ordinare
    df['Corsia'] = df['Corsia'].astype(str)
    for col in ['Stato', 'User', 'Tipo']:
        if col not in df.columns: df[col] = ""
    return df

df = load_data()

# 3. Header e Selezione Utente
col_logo, col_user = st.columns([0.3, 0.7])
with col_logo:
    st.image("icona_spesa.png", width=60)
with col_user:
    utente = st.selectbox("Utente:", ["Lorenzo", "Maria"], label_visibility="collapsed")

# 4. MENU ORIZZONTALE (Tabs)
tab1, tab2, tab3 = st.tabs(["🏠 CASA", "🛒 BORELLO", "📦 PRODOTTI"])

# --- TAB 3: PRODOTTI (DATABASE) ---
with tab3:
    st.subheader("📦 Catalogo")
    search = st.text_input("Cerca prodotto...", placeholder="es: Broccoli")
    
    df_sorted = df.sort_values(by="Corsia")
    if search:
        df_sorted = df_sorted[df_sorted['Prodotto'].str.contains(search, case=False)]

    for corsia in sorted(df_sorted['Corsia'].unique()):
        with st.expander(f"📍 Corsia {corsia}", expanded=False):
            items = df_sorted[df_sorted['Corsia'] == corsia]
            for idx, row in items.iterrows():
                c1, c2, c3 = st.columns([0.2, 0.5, 0.3])
                with c1:
                    if pd.notna(row['URL_Foto']) and str(row['URL_Foto']).startswith("http"):
                        st.image(row['URL_Foto'], width=50)
                with c2:
                    st.write(f"**{row['Prodotto']}**")
                with c3:
                    if st.button("➕", key=f"add_{idx}"):
                        # LOGICA AGGIUNTA: scrive sul DataFrame e aggiorna Google Sheets
                        df.at[idx, 'Stato'] = "DA COMPRARE"
                        df.at[idx, 'User'] = utente
                        df.at[idx, 'Tipo'] = "Pianificato"
                        conn.update(worksheet="Catalogo", data=df)
                        st.toast(f"Aggiunto: {row['Prodotto']}!")

# --- TAB 1: A CASA (LISTA IN PREPARAZIONE) ---
with tab1:
    st.subheader("📝 Lista da preparare")
    lista_casa = df[df['Stato'] == "DA COMPRARE"]
    
    if lista_casa.empty:
        st.info("La lista è vuota. Vai in PRODOTTI per aggiungere.")
    else:
        for idx, row in lista_casa.iterrows():
            st.write(f"✅ {row['Prodotto']} (Aggiunto da: {row['User']})")
        
        if st.button("🗑️ Svuota tutto"):
            df['Stato'] = ""
            conn.update(worksheet="Catalogo", data=df)
            st.rerun()

# --- TAB 2: BORELLO (SHOPPING MODE) ---
with tab2:
    st.subheader("🛒 Al Supermercato")
    # Qui implementeremo la logica della spunta definitiva
    st.write("Prossimamente: Spunta i prodotti mentre compri!")
