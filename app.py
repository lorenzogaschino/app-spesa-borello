import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione Pagina
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="wide")

# 1. Configurazione Pagina e CSS Ultra-Compatto per Mobile
st.markdown("""
<style>
    /* 1. FORZA ORIZZONTALE E ELIMINA SCROLL */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 0.5rem !important; /* Spazio minimo tra colonne */
    }

    /* 2. PROPORZIONI FISSE COLONNE */
    [data-testid="column"] {
        width: auto !important;
        flex-math: none !important;
        flex-shrink: 1 !important;
        min-width: 0px !important;
    }

    /* 3. TOAST E TESTO */
    [data-testid="stToast"] {
        background-color: #2e7d32 !important;
        color: white !important;
    }
    
    .product-name {
        font-size: 16px !important; /* Leggermente ridotto per stare in riga */
        font-weight: 600 !important;
        line-height: 1.2;
        display: block;
    }

    /* 4. TAB E BOTTONI */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { 
        height: 40px; border-radius: 8px; flex-grow: 1; font-size: 12px;
    }
    .stButton>button { 
        padding: 0px 5px !important; 
        height: 35px !important;
        min-width: 35px !important;
    }
</style>
""", unsafe_allow_html=True)
    /* NUOVE REGOLE V1.1: Toast e Font */
    [data-testid="stToast"] {
        background-color: #2e7d32 !important;
        color: white !important;
        width: 100% !important;
    }
    
    .product-name {
        font-size: 18px !important;
        font-weight: 600 !important;
        margin-bottom: 0px;
    }
</style>
""", unsafe_allow_html=True)

# 2. Connessione e Gestione Dati
conn = st.connection("gsheets", type=GSheetsConnection)

# Caricamento iniziale dei dati
if 'df' not in st.session_state:
    # Legge il foglio (assicurati che il tab si chiami "Catalogo")
    raw_df = conn.read(worksheet="Catalogo")
    
    # Pulizia colonne: aggiunge quelle mancanti se il foglio è nuovo
    for col in ['Stato', 'User', 'Tipo', 'URL_Foto']:
        if col not in raw_df.columns:
            raw_df[col] = ""
            
    # Gestione Corsia: trasforma in testo e gestisce i valori vuoti
    raw_df['Corsia'] = raw_df['Corsia'].astype(str).replace(['nan', 'None', ''], '?')
    
    # Salva tutto nello stato dell'app
    st.session_state.df = raw_df

def save():
    # Trasforma i dati in un formato pulito per Google Sheets
    data_to_save = st.session_state.df.copy()
    # Converte eventuali valori nulli in stringhe vuote per evitare errori API
    data_to_save = data_to_save.fillna("")
    # Aggiorna il foglio
    conn.update(worksheet="Catalogo", data=data_to_save)

# 3. Header
col_logo, col_user = st.columns([0.2, 0.8])
with col_logo:
    st.write("🛒") # Sostituisci con st.image se preferisci
with col_user:
    utente = st.selectbox("Utente:", ["Lorenzo", "Maria"], label_visibility="collapsed")

# 4. MENU TABS
tab1, tab2, tab3 = st.tabs(["🏠 LISTA", "🛒 SPESA", "📦 CATALOGO"])

# --- TAB 3: CATALOGO (VERSIONE COMPATTA 1.1) ---
with tab3:
    st.subheader("📦 Catalogo")
    search = st.text_input("Cerca...", placeholder="Pasta...", key="cat_search_v1.1")
    
    df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy().sort_values("Prodotto")
    if search:
        df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False, na=False)]

    st.divider()

  for idx, row in df_cat.iterrows():
        is_in_list = row['Stato'] == "DA COMPRARE"
        
        with st.container():
            # Proporzioni: 70% testo, 15% immagine, 15% bottone
            c_info, c_img, c_btn = st.columns([0.65, 0.17, 0.18])
            
            with c_info:
                color = "#a0a0a0" if is_in_list else "#000000"
                label = " (In Lista)" if is_in_list else ""
                st.markdown(f"<span class='product-name' style='color:{color}'>{row['Prodotto']}{label}</span>", unsafe_allow_html=True)
                st.caption(f"📍 {row['Corsia']}")
            
            with c_img:
                url = row.get('URL_Foto', "")
                if pd.notna(url) and str(url).startswith("http"):
                    st.image(url, width=35) # Immagine più piccola
                else:
                    st.write("📦")
            
            with c_btn:
                if is_in_list:
                    st.button("🛒", key=f"btn_in_{idx}", disabled=True)
                else:
                    if st.button("➕", key=f"btn_add_{idx}"):
                        st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                        st.session_state.df.at[idx, 'User'] = utente
                        save()
                        st.toast(f"✅ {row['Prodotto']} aggiunto!")
                        st.rerun()

# --- TAB 1: LISTA (PIANIFICAZIONE CASA) ---
with tab1:
    st.subheader("📝 Lista della Spesa")
    
    # 1. AGGIUNTA RAPIDA (Prodotto non in catalogo)
    with st.expander("➕ Aggiungi al volo", expanded=False):
        c_n, c_c = st.columns([0.6, 0.4])
        nuovo_p = c_n.text_input("Cosa manca?", key="quick_add_name")
        corsia_p = c_c.selectbox("Corsia", ["?", "1", "2", "3", "4", "5", "FRESCHI", "SURGELATI"], key="quick_add_corsia")
        
        if st.button("Inserisci in lista", use_container_width=True):
            if nuovo_p:
                # Creazione riga per prodotto "extra"
                new_row = pd.DataFrame([{
                    "Prodotto": nuovo_p, 
                    "Corsia": corsia_p, 
                    "Stato": "DA COMPRARE", 
                    "User": utente, 
                    "Tipo": "Manuale", 
                    "URL_Foto": ""
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                save() # <--- Chiamata corretta riga 34
                st.rerun()

    st.divider()

    # 2. VISUALIZZAZIONE E EDIT DELLA LISTA
    # Filtriamo solo i prodotti selezionati
    lista_edit = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"]
    
    if lista_edit.empty:
        st.info("La tua lista è vuota. Aggiungi qualcosa qui sopra o dal Catalogo!")
    else:
        for idx, row in lista_edit.iterrows():
            with st.container(border=True):
                col_info, col_del = st.columns([0.8, 0.2])
                
                with col_info:
                    st.write(f"**{row['Prodotto']}**")
                    st.caption(f"👤 {row['User']} | 📍 Corsia: {row['Corsia']}")
                
                with col_del:
                    # Tasto per rimuovere dalla lista
                    if st.button("❌", key=f"remove_{idx}"):
                        if row.get('Tipo') == "Manuale":
                            # Se è manuale, lo eliminiamo fisicamente dal DF
                            st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
                        else:
                            # Se è da catalogo, resettiamo solo lo stato
                            st.session_state.df.at[idx, 'Stato'] = ""
                        
                        save() # <--- Chiamata corretta riga 34
                        st.rerun()
        
        # 3. AZIONI MASSIVE
        st.write("") # Spaziatore
        if st.button("🗑️ Svuota tutta la lista", type="secondary"):
            # Resetta lo stato di tutti i prodotti
            st.session_state.df['Stato'] = ""
            # Elimina i prodotti manuali per non sporcare il DB a lungo termine
            st.session_state.df = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].reset_index(drop=True)
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
