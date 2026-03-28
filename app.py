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

def save():
    # Pulizia minima per evitare errori di celle vuote nel DB
    st.session_state.df['Prodotto'] = st.session_state.df['Prodotto'].fillna("Senza Nome")
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

# --- TAB 1: LISTA (MODIFICHE PUNTUALI) ---
with tab1:
    st.subheader("📝 Lista della Spesa")
    
    # Inserimento rapido
    with st.expander("➕ Aggiungi al volo", expanded=False):
        c_n, c_c = st.columns([0.6, 0.4])
        nuovo_p = c_n.text_input("Cosa manca?", key="new_p_input")
        corsia_p = c_c.selectbox("Corsia", ["?", "1", "2", "3", "4", "5", "FRESCHI", "SURGELATI"], key="new_p_corsia")
        if st.button("Inserisci in lista", use_container_width=True):
            if nuovo_p:
                new_row = pd.DataFrame([{
                    "Prodotto": nuovo_p, "Corsia": corsia_p, "Stato": "DA COMPRARE", 
                    "User": utente, "Tipo": "Manuale", "URL_Foto": ""
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                save()
                st.rerun()

    st.divider()

    # Visualizzazione e Edit rapido
    lista_edit = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"]
    
    if lista_edit.empty:
        st.info("Lista vuota.")
    else:
        for idx, row in lista_edit.iterrows():
            with st.container(border=True):
                col_info, col_actions = st.columns([0.7, 0.3])
                with col_info:
                    st.write(f"**{row['Prodotto']}**")
                    # Edit rapido della corsia se necessario
                    nuova_corsia = st.selectbox(f"Sposta C.", ["?", "1", "2", "3", "4", "5", "F.", "S."], 
                                              index=0, key=f"edit_c_{idx}", label_visibility="collapsed")
                    if nuova_corsia != row['Corsia'] and nuova_corsia != "Sposta C.":
                        st.session_state.df.at[idx, 'Corsia'] = nuova_corsia
                        save()
                        st.rerun()
                with col_actions:
                    if st.button("❌", key=f"del_{idx}"):
                        if row['Tipo'] == "Manuale":
                            st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
                        else:
                            st.session_state.df.at[idx, 'Stato'] = ""
                        save()
                        st.rerun()

# --- TAB 2: SPESA (MODIFICHE PUNTUALI) ---
with tab2:
    st.subheader("🛒 Al Supermercato")
    
    # Ordinamento rigoroso per corsia per ottimizzare il percorso a piedi
    spesa_df = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].sort_values(by="Corsia")
    
    if spesa_df.empty:
        st.balloons()
        st.success("Tutto preso! Goditi il tempo libero 🍷")
    else:
        # Progress bar per dare soddisfazione
        total = len(spesa_df)
        st.caption(f"Mancano {total} prodotti")
        
        for idx, row in spesa_df.iterrows():
            # Container cliccabile largo per facilitare l'uso con i guanti o in movimento
            with st.container(border=True):
                c_check, c_name = st.columns([0.25, 0.75])
                if c_check.button("✅", key=f"buy_{idx}", use_container_width=True):
                    st.session_state.df.at[idx, 'Stato'] = "PRESO"
                    # Qui potremmo decidere di non salvare su Sheets ogni singolo click 
                    # per velocità, ma per sicurezza lo manteniamo
                    save()
                    st.rerun()
                with c_name:
                    st.write(f"**{row['Prodotto']}**")
                    st.caption(f"📍 Corsia {row['Corsia']} | 👤 {row['User']}")
