import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione Pagina
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="wide")

# 2. CSS Mirato per Mobile (Isolamento Tab 3)
st.markdown("""
<style>
    .stMainBlockContainer { padding: 1rem !important; }

    /* Stili testo Catalogo */
    .cat-name {
        font-size: 26px !important; 
        font-weight: 800 !important;
        line-height: 1.1;
        color: #000000 !important;
        display: block;
    }
    
    .cat-cap { 
        font-size: 18px !important; 
        color: #555555 !important; 
        display: block;
        margin-bottom: 10px;
    }

    /* Immagini Catalogo */
    .cat-img {
        width: 100px !important; 
        height: 100px !important;
        object-fit: cover;
        border-radius: 12px;
        border: 1px solid #eee;
    }

    /* BOTTONI GIGANTI: Solo dentro .cat-row */
    div.cat-row div.stButton > button {
        width: 100% !important;
        height: 75px !important;
        font-size: 28px !important;
        font-weight: bold !important;
        border-radius: 18px !important;
        background-color: #ffffff !important;
        border: 2px solid #333 !important;
        margin-top: 10px !important;
    }

    /* Reset bottoni per Tab 1 e 2 */
    div.stButton > button {
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Connessione e Funzioni Core
conn = st.connection("gsheets", type=GSheetsConnection)

def save_data():
    try:
        # Usiamo un dataframe pulito per l'update
        df_to_save = st.session_state.df.copy()
        conn.update(worksheet="Catalogo", data=df_to_save)
    except Exception as e:
        st.error(f"Errore durante il salvataggio: {e}")

# Inizializzazione dati (solo una volta)
if 'df' not in st.session_state:
    try:
        st.session_state.df = conn.read(worksheet="Catalogo")
    except Exception as e:
        st.error(f"Errore connessione: {e}")
        st.stop()

# Selezione Utente (Globale)
utente = st.sidebar.selectbox("Chi sei?", ["Lorenzo", "Maria"])

# 4. Definizione TAB
tab1, tab2, tab3 = st.tabs(["🏠 LISTA", "🛒 SPESA", "📦 CATALOGO"])

# --- TAB 1 e 2: Inserire qui il tuo codice per la lista ---

# --- TAB 3: CATALOGO ---
with tab3:
    st.write("## 📦 Catalogo")
    search = st.text_input("Cerca prodotto...", placeholder="Pasta, latte...", key="search_cat_v4")
    
    if isinstance(st.session_state.df, pd.DataFrame):
        # Filtriamo per la visualizzazione senza alterare l'indice originale
        df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy()
        df_cat = df_cat.sort_values("Prodotto")
        
        if search:
            df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False, na=False)]

        for idx, row in df_cat.iterrows():
            is_in_list = row['Stato'] == "DA COMPRARE"
            
            with st.container():
                st.markdown('<div class="cat-row">', unsafe_allow_html=True)
                
                col_left, col_right = st.columns([0.7, 0.3])
                
                with col_left:
                    color = "#bbbbbb" if is_in_list else "#000000"
                    st.markdown(f'<span class="cat-name" style="color:{color}">{row["Prodotto"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span class="cat-cap">📍 {row["Corsia"]}</span>', unsafe_allow_html=True)
                
                with col_right:
                    url = row.get('URL_Foto', "")
                    if url and str(url).startswith("http"):
                        st.markdown(f'<img src="{url}" class="cat-img">', unsafe_allow_html=True)
                    else:
                        st.write("")

                if is_in_list:
                    st.button("🛒 IN LISTA", key=f"btn_in_{idx}", disabled=True)
                else:
                    if st.button(f"➕ AGGIUNGI", key=f"btn_add_{idx}"):
                        # Modifica diretta sul session_state usando l'indice originale
                        st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                        st.session_state.df.at[idx, 'User'] = utente
                        save_data()
                        st.toast(f"✅ {row['Prodotto']} aggiunto!")
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()
                    
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
