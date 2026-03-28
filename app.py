import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione Pagina
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="wide")

# CSS Migliorato per Mobile
# 1. Configurazione Pagina (Righe 9-20 aggiornate)
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
    
    /* NUOVE REGOLE V1.1 */
    .stToast {
        background-color: #2e7d32 !important;
        color: white !important;
    }
    [data-testid="stToast"] {
        width: 100% !important; /* Su mobile 150% potrebbe uscire dallo schermo, 100% è più sicuro */
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

# --- TAB 3: CATALOGO (VERSIONE 1.1) ---
with tab3:
    st.subheader("📦 Catalogo Prodotti")
    
    search = st.text_input("Cerca nel database...", placeholder="Es: Pasta...", key="catalog_search_v1")
    
    # 1. Preparazione dati: Alfabetico e solo prodotti Catalogo
    df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy()
    df_cat = df_cat.sort_values(by="Prodotto")
    
    if search:
        df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False, na=False)]

    st.divider()

    # 2. Visualizzazione a lista continua
    for idx, row in df_cat.iterrows():
        # Verifichiamo se il prodotto è già stato selezionato
        is_in_list = row['Stato'] == "DA COMPRARE"
        
        # Container con stile condizionale (grigetto se già in lista)
        with st.container():
            c_info, c_img, c_btn = st.columns([0.65, 0.15, 0.2])
            
            with c_info:
                if is_in_list:
                    # Testo grigio e sbarrato/opaco per indicare che c'è già
                    st.markdown(f"<p style='color: #a0a0a0; font-size: 18px;'>{row['Prodotto']} (In Lista)</p>", unsafe_allow_html=True)
                else:
                    # Testo standard grande
                    st.markdown(f"<p class='product-name'>{row['Prodotto']}</p>", unsafe_allow_html=True)
                st.caption(f"📍 Corsia {row['Corsia']}")
            
            with c_img:
                url = row.get('URL_Foto', "")
                if pd.notna(url) and str(url).startswith("http"):
                    st.image(url, width=50)
                else:
                    st.write("📦")
            
            with c_btn:
                if is_in_list:
                    # Icona carrello a destra (disabilitata)
                    st.button("🛒", key=f"btn_in_{idx}", disabled=True)
                else:
                    # Bottone attivo per aggiungere
                    if st.button("➕", key=f"btn_add_{idx}"):
                        st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                        st.session_state.df.at[idx, 'User'] = utente
                        save()
                        st.toast(f"✅ AGGIUNTO: {row['Prodotto']}")
                        st.rerun() # Ricarica per aggiornare l'aspetto (grigetto)

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
