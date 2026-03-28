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
    
    with st.expander("➕ Aggiungi al volo", expanded=False):
        c_n, c_c = st.columns([0.6, 0.4])
        nuovo_p = c_n.text_input("Cosa manca?", key="k_manual_name")
        corsia_p = c_c.selectbox("Corsia", ["?", "1", "2", "3", "4", "5", "FRESCHI", "SURGELATI"], key="k_manual_corsia")
        
        if st.button("Inserisci in lista", key="k_btn_manual_add", use_container_width=True):
            if nuovo_p:
                new_row = pd.DataFrame([{"Prodotto": nuovo_p, "Corsia": corsia_p, "Stato": "DA COMPRARE", "User": utente, "Tipo": "Manuale", "URL_Foto": ""}])
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                save()
                st.rerun()

    st.divider()

    if 'df' in st.session_state:
        # Filtriamo i prodotti "DA COMPRARE"
        lista_edit = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy()
        
        if lista_edit.empty:
            st.info("La tua lista è vuota.")
        else:
            for idx, row in lista_edit.iterrows():
                with st.container(border=True):
                    col_info, col_del = st.columns([0.8, 0.2])
                    with col_info:
                        st.write(f"**{row['Prodotto']}**")
                        st.caption(f"👤 {row['User']} | 📍 {row['Corsia']}")
                    with col_del:
                        # Chiave univoca 'L_' per Tab 1
                        if st.button("❌", key=f"L_del_{idx}"):
                            if row['Tipo'] == "Manuale":
                                st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
                            else:
                                st.session_state.df.at[idx, 'Stato'] = ""
                            save()
                            st.rerun()
                
# --- TAB 2: SPESA (MODIFICHE PUNTUALI) ---
with tab2:
    st.subheader("🛒 Al Supermercato")
    
    if 'df' in st.session_state:
        # Mostriamo i prodotti da prendere, ordinati per CORSIA per farti fare meno strada
        df_spesa = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy()
        df_spesa = df_spesa.sort_values("Corsia")

        if df_spesa.empty:
            st.success("Tutto preso! Carrello pieno. 🎉")
        else:
            st.info("Clicca sul prodotto quando lo metti nel carrello.")
            for idx, row in df_spesa.iterrows():
                # Bottoni grandi per essere cliccati facilmente col pollice
                if st.button(f"{row['Corsia']} - {row['Prodotto']}", key=f"S_check_{idx}", use_container_width=True):
                    st.session_state.df.at[idx, 'Stato'] = "NEL CARRELLO"
                    save()
                    st.rerun()
        
        st.divider()
        if st.button("🏁 Ho finito la spesa (Svuota tutto)", key="k_empty_all", type="primary", use_container_width=True):
            # Resetta tutto lo stato per la prossima volta
            st.session_state.df.loc[st.session_state.df['Stato'] == "DA COMPRARE", 'Stato'] = ""
            st.session_state.df.loc[st.session_state.df['Stato'] == "NEL CARRELLO", 'Stato'] = ""
            # Rimuove i manuali
            st.session_state.df = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].reset_index(drop=True)
            save()
            st.rerun()
