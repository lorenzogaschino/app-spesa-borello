import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="wide")

# 2. CSS UNIFICATO E SICURO (Menu visibile, bottoni grandi, layout pulito)
st.markdown("""
<style>
    /* Spaziatura corretta per non coprire i tab in alto */
    .block-container { padding-top: 4rem !important; }
    
    /* Stile testo prodotti */
    .prod-name { font-size: 24px !important; font-weight: 800; color: #1E1E1E; display: block; line-height: 1.2; }
    .prod-info { font-size: 16px !important; color: #666; display: block; margin-top: 4px; }
    .prod-user { font-size: 13px !important; color: #007BFF; font-style: italic; }
    
    /* Immagini tonde e fisse */
    .prod-img { width: 90px !important; height: 90px !important; object-fit: cover; border-radius: 15px; border: 1px solid #EEE; }
    
    /* Bottoni Grandi per il pollice */
    div.stButton > button {
        width: 100% !important;
        height: 60px !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: 2px solid #333 !important;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 3. GESTIONE DATI (Connessione e Pulizia)
conn = st.connection("gsheets", type=GSheetsConnection)

def save_data():
    conn.update(worksheet="Catalogo", data=st.session_state.df)

if 'df' not in st.session_state:
    raw_df = conn.read(worksheet="Catalogo")
    # Pulizia: Rimuoviamo righe dove il Prodotto è vuoto o "nan"
    raw_df['Prodotto'] = raw_df['Prodotto'].astype(str).str.strip()
    raw_df = raw_df[raw_df['Prodotto'] != 'nan']
    raw_df = raw_df[raw_df['Prodotto'] != '']
    st.session_state.df = raw_df.reset_index(drop=True)

utente_attuale = "Lorenzo"

# --- 4. STRUTTURA TAB ---
tab_lista, tab_spesa, tab_catalogo = st.tabs(["🏠 LISTA", "🛒 SPESA", "📦 CATALOGO"])

# ==========================================
# TAB 1: LISTA (Cosa dobbiamo comprare)
# ==========================================
with tab_lista:
    st.subheader("📝 Da acquistare")
    
    # Aggiunta manuale
    with st.expander("➕ Aggiungi prodotto non in catalogo", expanded=False):
        c1, c2 = st.columns([0.7, 0.3])
        nome_m = c1.text_input("Nome", key="manual_name")
        corsia_m = c2.selectbox("Corsia", ["?", "1", "2", "3", "4", "5", "FRIGO", "SURGELATI", "ORTOFRUTTA"], key="manual_corsia")
        if st.button("Aggiungi in Lista", key="btn_add_manual"):
            if nome_m:
                new_item = pd.DataFrame([{"Prodotto": nome_m, "Corsia": corsia_m, "Stato": "DA COMPRARE", "User": utente_attuale, "Tipo": "Manuale", "URL_Foto": ""}])
                st.session_state.df = pd.concat([st.session_state.df, new_item], ignore_index=True)
                save_data()
                st.rerun()

    st.divider()
    
    items_in_list = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"]
    
    if items_in_list.empty:
        st.info("La lista è vuota. Vai nel Catalogo per aggiungere prodotti!")
    else:
        for idx, row in items_in_list.iterrows():
            with st.container(border=True):
                col_txt, col_img = st.columns([0.7, 0.3])
                with col_txt:
                    st.markdown(f'<span class="prod-name">{row["Prodotto"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span class="prod-info">📍 Corsia: {row["Corsia"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span class="prod-user">👤 Aggiunto da: {row.get("User", "---")}</span>', unsafe_allow_html=True)
                with col_img:
                    url = row.get('URL_Foto', "")
                    if pd.notna(url) and str(url).startswith("http"):
                        st.markdown(f'<img src="{url}" class="prod-img">', unsafe_allow_html=True)
                
                if st.button("❌ RIMUOVI", key=f"L_remove_{idx}"):
                    if row['Tipo'] == "Manuale":
                        st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
                    else:
                        st.session_state.df.at[idx, 'Stato'] = ""
                    save_data()
                    st.rerun()
# ==========================================
# TAB 2: SPESA (Al supermercato - Layout Identico)
# ==========================================
with tab_spesa:
    st.subheader("🛒 Al Supermercato")
    
    # Filtriamo e ordiniamo per corsia
    df_spesa = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].sort_values("Corsia")
    
    if df_spesa.empty:
        st.success("Tutto preso! Carrello pieno. 🎉")
    else:
        st.info("Tocca 'PRESO' per spostare l'articolo nel carrello.")
        
        for idx, row in df_spesa.iterrows():
            with st.container(border=True):
                # COLONNE IDENTICHE AL TAB 1 E 3
                col_txt, col_img = st.columns([0.7, 0.3])
                
                with col_txt:
                    st.markdown(f'<span class="prod-name">{row["Prodotto"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span class="prod-info">📍 Corsia: {row["Corsia"]}</span>', unsafe_allow_html=True)
                    # Manteniamo l'utente anche qui per coerenza totale
                    st.markdown(f'<span class="prod-user">👤 Richiesto da: {row.get("User", "---")}</span>', unsafe_allow_html=True)
                
                with col_img:
                    url = row.get('URL_Foto', "")
                    if pd.notna(url) and str(url).startswith("http"):
                        st.markdown(f'<img src="{url}" class="prod-img">', unsafe_allow_html=True)
                
                # BOTTONE (Unica differenza è l'azione, ma lo stile è lo stesso)
                if st.button(f"✅ PRESO!", key=f"S_check_{idx}"):
                    st.session_state.df.at[idx, 'Stato'] = "NEL CARRELLO"
                    save_data()
                    st.rerun()

    st.divider()
    # Bottone di chiusura spesa
    if not st.session_state.df[st.session_state.df['Stato'].isin(["DA COMPRARE", "NEL CARRELLO"])].empty:
        if st.button("🏁 FINISCI SPESA E SVUOTA TUTTO", key="finish_all_btn", type="primary"):
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
        is_in_list = row['Stato'] == "DA COMPRARE"
        
        with st.container(border=True):
            col_txt, col_img = st.columns([0.7, 0.3])
            with col_txt:
                color = "#AAA" if is_in_list else "#000"
                st.markdown(f'<span class="prod-name" style="color:{color}">{row["Prodotto"]}</span>', unsafe_allow_html=True)
                st.markdown(f'<span class="prod-info">📍 Corsia: {row["Corsia"]}</span>', unsafe_allow_html=True)
            with col_img:
                url = row.get('URL_Foto', "")
                if pd.notna(url) and str(url).startswith("http"):
                    st.markdown(f'<img src="{url}" class="prod-img">', unsafe_allow_html=True)
            
            if is_in_list:
                st.button("🛒 GIÀ IN LISTA", key=f"C_in_{idx}", disabled=True)
            else:
                if st.button("➕ AGGIUNGI", key=f"C_add_{idx}"):
                    st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                    st.session_state.df.at[idx, 'User'] = utente_attuale
                    save_data()
                    st.rerun()
