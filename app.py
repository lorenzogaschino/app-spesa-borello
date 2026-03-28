import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione Pagina (Inizio file)
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="wide")

# CSS Ultra-Mobile: Forza orizzontale, niente scorrimento, font compatti
st.markdown("""
<style>
    /* A. Gestione Globale Contenitore e Margini */
    .stMainBlockContainer {
        padding-left: 0.5rem !important;  /* Margini minimi ai lati */
        padding-right: 0.5rem !important;
        overflow-x: hidden !important; /* Disabilita lo scroll orizzontale globale */
    }

    /* B. Forza le colonne a stare su una riga - Senza scorrimento */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important; /* Impedisce l'andata a capo */
        gap: 0.2rem !important; /* Spazio piccolissimo tra elementi */
        align-items: center !important;
        width: 100% !important; /* Occupa tutta la larghezza */
        min-width: 0 !important; /* Importante per flex-shrink */
    }

    [data-testid="column"] {
        width: auto !important;
        flex: 1 1 auto !important; /* Permette alle colonne di ridimensionarsi */
        min-width: 0px !important; /* Permette il ridimensionamento sotto la larghezza del contenuto */
        overflow: hidden !important; /* Impedisce al contenuto di forzare la larghezza */
    }

    /* C. Stile Prodotti: Compatto, font più piccoli, ellipses */
    .product-name {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #111111;
        margin-bottom: 0px !important;
        line-height: 1.1;
        /* Gestione nomi troppo lunghi: mette i puntini se non ci sta */
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
    }

    /* Corsia */
    [data-testid="stCaptionContainer"] {
        font-size: 11px !important;
        margin-top: 0px !important;
    }

    /* Immagini */
    [data-testid="stImage"] img {
        max-width: 35px !important; /* Larghezza massima dell'immagine */
        height: auto !important;
    }

    /* D. Tab Compatti (Selezionatore Utente) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        padding-top: 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        border-radius: 8px;
        flex-grow: 1;
        font-size: 12px;
        padding-left: 5px;
        padding-right: 5px;
    }
    .stTabs [aria-selected="true"] { background-color: #4b5320 !important; color: white !important; }

    /* E. Bottoni Quadrati Compatti */
    .stButton>button {
        padding: 0px !important;
        height: 35px !important;
        width: 35px !important;
        min-width: 35px !important;
        border-radius: 10px;
        background-color: transparent;
        border: 1px solid #ccc;
    }
    .stButton>button:disabled { background-color: #f0f0f0; }

    /* F. Toast e Altro */
    [data-testid="stToast"] {
        background-color: #2e7d32 !important;
        color: white !important;
        width: 100% !important;
    }
    .stSelectbox { font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# 2. Connessione e Gestione Dati
conn = st.connection("gsheets", type=GSheetsConnection)

def save():
    try:
        data_to_save = st.session_state.df.copy()
        conn.update(worksheet="Catalogo", data=data_to_save)
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")

if 'df' not in st.session_state:
    try:
        raw_df = conn.read(worksheet="Catalogo")
        for col in ['Stato', 'User', 'Tipo', 'URL_Foto']:
            if col not in raw_df.columns: raw_df[col] = ""
        raw_df['Corsia'] = raw_df['Corsia'].astype(str).replace(['nan', 'None'], '?')
        st.session_state.df = raw_df
    except Exception:
        st.error("Errore caricamento Database")

# 3. Header e Navigazione
utente = st.selectbox("Utente", ["Lorenzo", "Maria"], label_visibility="collapsed")
tab1, tab2, tab3 = st.tabs(["🏠 LISTA", "🛒 SPESA", "📦 CATALOGO"])
# --- TAB 3: CATALOGO (VERSIONE COMPATTA MOBILE DEFINTIVA V1.2) ---
with tab3:
    # Ridotto a st.write per risparmiare altezza
    st.write("📦 **Catalogo**")

    # Ricerca con altezza ridotta (key univoca v1.2)
    search = st.text_input("Cerca nel database...", placeholder="Es: Pasta, Mele...", key="cat_search_v1.2_def")

    # 1. Preparazione Dati: Alfabetico e solo Catalogo
    df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy()
    df_cat = df_cat.sort_values(by="Prodotto")

    if search:
        df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False, na=False)]

    # 2. Visualizzazione prodotti
    for idx, row in df_cat.iterrows():
        is_in_list = row['Stato'] == "DA COMPRARE"

        with st.container():
            # Proporzioni 75/15/10: Priorità al testo, foto piccola, bottone quadrato
            col_txt, col_img, col_btn = st.columns([0.75, 0.15, 0.1])

            with col_txt:
                # Stile condizionale per testo
                color = "#a0a0a0" if is_in_list else "#111111"
                nome_prodotto = f"{row['Prodotto']} (Lista)" if is_in_list else row['Prodotto']

                # L'uso di <span> e .product-name attiva l'ellipsis CSS per nomi lunghi
                st.markdown(f"<span class='product-name' style='color:{color}'>{nome_prodotto}</span>", unsafe_allow_html=True)
                st.caption(f"📍 {row['Corsia']}")

            with col_img:
                url = row.get('URL_Foto', "")
                # Solo se URL valido, mostra immagine con larghezza fissa da CSS
                if pd.notna(url) and str(url).startswith("http"):
                    st.image(url, width=35)
                else:
                    st.write("") # Rimosso emoji pacco per risparmiare spazio e mantenere allineamento

            with col_btn:
                if is_in_list:
                    # Carrello piccolo e grigio disabilitato
                    st.button("🛒", key=f"btn_in_{idx}", disabled=True)
                else:
                    # Più piccolo e univoco
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
