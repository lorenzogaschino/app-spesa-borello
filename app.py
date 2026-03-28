import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="wide")

# 2. CSS (Separato per non rompere i Tab)
st.markdown("""
<style>
    .stMainBlockContainer { padding: 1rem !important; }
    .cat-name { font-size: 26px !important; font-weight: 800; color: #000; display: block; }
    .cat-cap { font-size: 18px !important; color: #555; display: block; margin-bottom: 10px; }
    .cat-img { width: 100px !important; height: 100px !important; object-fit: cover; border-radius: 12px; }
    
    /* Stile specifico solo per i bottoni nel catalogo */
    div.cat-row div.stButton > button {
        width: 100% !important;
        height: 70px !important;
        font-size: 25px !important;
        font-weight: bold !important;
        border: 2px solid #333 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Dati e Connessione
conn = st.connection("gsheets", type=GSheetsConnection)

def save():
    conn.update(worksheet="Catalogo", data=st.session_state.df)

if 'df' not in st.session_state:
    st.session_state.df = conn.read(worksheet="Catalogo")

utente = "Lorenzo"

# 4. TAB - DEFINIZIONE (TUTTI A INIZIO RIGA)
tab1, tab2, tab3 = st.tabs(["🏠 LISTA", "🛒 SPESA", "📦 CATALOGO"])

with tab1:
    st.markdown("### 🏠 Prodotti da comprare")
    st.write("Contenuto Lista")

with tab2:
    st.markdown("### 🛒 Spesa in corso")
    st.write("Contenuto Spesa")

with tab3:
    st.markdown("### 📦 Catalogo")
    search = st.text_input("Cerca...", key="search_v9")
    
    if 'df' in st.session_state:
        df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy().sort_values("Prodotto")
        if search:
            df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False, na=False)]

        for idx, row in df_cat.iterrows():
            is_in_list = row['Stato'] == "DA COMPRARE"
            with st.container():
                st.markdown('<div class="cat-row">', unsafe_allow_html=True)
                c1, c2 = st.columns([0.7, 0.3])
                with c1:
                    st.markdown(f'<span class="cat-name">{row["Prodotto"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span class="cat-cap">📍 {row["Corsia"]}</span>', unsafe_allow_html=True)
                with c2:
                    url = row.get('URL_Foto', "")
                    if pd.notna(url) and str(url).startswith("http"):
                        st.markdown(f'<img src="{url}" class="cat-img">', unsafe_allow_html=True)
                
                if is_in_list:
                    st.button("🛒 IN LISTA", key=f"in_{idx}", disabled=True)
                else:
                    if st.button("➕ AGGIUNGI", key=f"add_{idx}"):
                        st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                        st.session_state.df.at[idx, 'User'] = utente
                        save()
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()

# --- 4. DEFINIZIONE TAB (Questa riga deve essere a inizio riga, senza spazi) ---
tab1, tab2, tab3 = st.tabs(["🏠 LISTA", "🛒 SPESA", "📦 CATALOGO"])

with tab1:
    st.markdown("### 🏠 Prodotti da comprare")
    # Codice del Tab 1 qui...
    st.info("La tua lista apparirà qui.")

with tab2:
    st.markdown("### 🛒 Spesa in corso")
    # Codice del Tab 2 qui...
    st.info("L'interfaccia di spesa apparirà qui.")

with tab3:
    st.markdown("### 📦 Catalogo Prodotti")
    
    # Ricerca
    search = st.text_input("Cerca prodotto...", placeholder="Es: Pasta...", key="search_cat_final_v8")
    
    if 'df' in st.session_state:
        # Filtriamo per la visualizzazione
        df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy()
        df_cat = df_cat.sort_values("Prodotto")
        
        if search:
            df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False, na=False)]

        for idx, row in df_cat.iterrows():
            is_in_list = row['Stato'] == "DA COMPRARE"
            
            with st.container():
                # Wrapper per lo stile gigante
                st.markdown('<div class="cat-row">', unsafe_allow_html=True)
                
                col_left, col_right = st.columns([0.7, 0.3])
                with col_left:
                    color = "#bbbbbb" if is_in_list else "#000000"
                    st.markdown(f'<span class="cat-name" style="color:{color}">{row["Prodotto"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span class="cat-cap">📍 {row["Corsia"]}</span>', unsafe_allow_html=True)
                
                with col_right:
                    url = row.get('URL_Foto', "")
                    if pd.notna(url) and str(url).startswith("http"):
                        st.markdown(f'<img src="{url}" class="cat-img">', unsafe_allow_html=True)

                if is_in_list:
                    st.button("🛒 IN LISTA", key=f"btn_in_cat_{idx}", disabled=True)
                else:
                    if st.button("➕ AGGIUNGI", key=f"btn_add_cat_{idx}"):
                        st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                        st.session_state.df.at[idx, 'User'] = utente
                        save()
                        st.toast(f"✅ {row['Prodotto']} aggiunto!")
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()
                
# --- TAB 3: CATALOGO ---
with tab3:
    st.markdown("### 📦 Catalogo Prodotti")
    
    # Ricerca
    search = st.text_input("Cerca prodotto...", placeholder="Es: Pasta...", key="search_cat_final_v6")
    
    if 'df' in st.session_state:
        # Filtro e ordinamento
        df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy().sort_values("Prodotto")
        
        if search:
            df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False, na=False)]

        # Rendering prodotti
        for idx, row in df_cat.iterrows():
            is_in_list = row['Stato'] == "DA COMPRARE"
            
            # Container per lo stile gigante
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
                
                # Bottone (Sotto testo e foto)
                if is_in_list:
                    st.button("🛒 IN LISTA", key=f"btn_in_cat_{idx}", disabled=True)
                else:
                    if st.button(f"➕ AGGIUNGI", key=f"btn_add_cat_{idx}"):
                        st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                        st.session_state.df.at[idx, 'User'] = utente
                        save()
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
                # Concateniamo e resettiamo l'indice per evitare duplicati
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                save() 
                st.rerun()

    st.divider()

    # 2. VISUALIZZAZIONE E EDIT DELLA LISTA
    if 'df' in st.session_state:
        # Filtriamo solo i prodotti selezionati (usiamo .index per sicurezza)
        lista_edit = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"]
        
        if lista_edit.empty:
            st.info("La tua lista è vuota. Aggiungi qualcosa qui sopra o dal Catalogo!")
        else:
            for idx, row in lista_edit.iterrows():
                # Usiamo un border per separare bene i prodotti su mobile
                with st.container(border=True):
                    col_info, col_del = st.columns([0.8, 0.2])
                    
                    with col_info:
                        st.write(f"**{row['Prodotto']}**")
                        st.caption(f"👤 {row['User']} | 📍 Corsia: {row['Corsia']}")
                    
                    with col_del:
                        # Tasto per rimuovere dalla lista
                        if st.button("❌", key=f"remove_{idx}"):
                            if row.get('Tipo') == "Manuale":
                                # Se è manuale, lo eliminiamo fisicamente
                                st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
                            else:
                                # Se è da catalogo, resettiamo solo lo stato
                                st.session_state.df.at[idx, 'Stato'] = ""
                            
                            save()
                            st.rerun()
            
            # 3. AZIONI MASSIVE
            st.write("") # Spaziatore
            if st.button("🗑️ Svuota tutta la lista", type="secondary", use_container_width=True):
                # 1. Resetta lo stato di quelli da catalogo
                st.session_state.df.loc[st.session_state.df['Stato'] == "DA COMPRARE", 'Stato'] = ""
                # 2. Elimina i prodotti manuali
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
