import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="wide")

# 2. CSS (Rimosso il padding che nascondeva i tab in alto!)
st.markdown("""
<style>
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

# --- 4. DEFINIZIONE TAB ---
tab1, tab2, tab3 = st.tabs(["🏠 LISTA", "🛒 SPESA", "📦 CATALOGO"])

# ==========================================
# --- TAB 1: LISTA (PIANIFICAZIONE CASA) ---
# ==========================================
with tab1:
    st.subheader("📝 Lista della Spesa")
    
    # Sezione aggiunta manuale
    with st.expander("➕ Aggiungi al volo", expanded=False):
        c_n, c_c = st.columns([0.6, 0.4])
        nuovo_p = c_n.text_input("Cosa manca?", key="k_manual_name")
        corsia_p = c_c.selectbox("Corsia", ["?", "1", "2", "3", "4", "5", "FRESCHI", "SURGELATI"], key="k_manual_corsia")
        
        if st.button("Inserisci in lista", key="k_btn_manual_add", use_container_width=True):
            if nuovo_p:
                new_row = pd.DataFrame([{
                    "Prodotto": nuovo_p, 
                    "Corsia": corsia_p, 
                    "Stato": "DA COMPRARE", 
                    "User": utente, 
                    "Tipo": "Manuale", 
                    "URL_Foto": ""
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                save()
                st.rerun()

    st.divider()

    if 'df' in st.session_state:
        # Recuperiamo i prodotti in lista
        lista_edit = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy()
        
        if lista_edit.empty:
            st.info("La tua lista è vuota.")
        else:
            for idx, row in lista_edit.iterrows():
                with st.container():
                    # Usiamo la stessa classe CSS del catalogo
                    st.markdown('<div class="cat-row">', unsafe_allow_html=True)
                    
                    col_info, col_img = st.columns([0.7, 0.3])
                    
                    with col_info:
                        st.markdown(f'<span class="cat-name">{row["Prodotto"]}</span>', unsafe_allow_html=True)
                        st.markdown(f'<span class="cat-cap">📍 Corsia: {row["Corsia"]}</span>', unsafe_allow_html=True)
                        # Dato extra dell'utente
                        st.caption(f"👤 Aggiunto da: {row.get('User', 'Utente')}")
                    
                    with col_img:
                        url = row.get('URL_Foto', "")
                        if pd.notna(url) and str(url).startswith("http"):
                            st.markdown(f'<img src="{url}" class="cat-img">', unsafe_allow_html=True)
                    
                    # Pulsante di rimozione (Coerente con lo stile del catalogo)
                    if st.button("❌ RIMUOVI DALLA LISTA", key=f"L_del_{idx}", use_container_width=True):
                        if row.get('Tipo') == "Manuale":
                            st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
                        else:
                            st.session_state.df.at[idx, 'Stato'] = ""
                        save()
                        st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.divider()

# ==========================================
# --- TAB 2: SPESA (IN NEGOZIO)          ---
# ==========================================
with tab2:
    st.subheader("🛒 Spesa in corso")
    
    if 'df' in st.session_state:
        # Filtriamo i prodotti da prendere e li ordiniamo per Corsia
        df_spesa = st.session_state.df[st.session_state.df['Stato'] == "DA COMPRARE"].copy()
        df_spesa = df_spesa.sort_values("Corsia")

        if df_spesa.empty:
            st.success("Tutto preso! Carrello pieno. 🎉")
        else:
            st.info("Tocca il prodotto per metterlo nel carrello")
            
            for idx, row in df_spesa.iterrows():
                with st.container():
                    # Usiamo la stessa classe CSS 'cat-row' per coerenza
                    st.markdown('<div class="cat-row">', unsafe_allow_html=True)
                    
                    col_info, col_img = st.columns([0.7, 0.3])
                    
                    with col_info:
                        st.markdown(f'<span class="cat-name">{row["Prodotto"]}</span>', unsafe_allow_html=True)
                        st.markdown(f'<span class="cat-cap">📍 Corsia: {row["Corsia"]}</span>', unsafe_allow_html=True)
                        # Mostriamo chi lo ha chiesto anche qui, utile se ci sono dubbi
                        st.caption(f"👤 Per: {row.get('User', 'Casa')}")
                    
                    with col_img:
                        url = row.get('URL_Foto', "")
                        if pd.notna(url) and str(url).startswith("http"):
                            st.markdown(f'<img src="{url}" class="cat-img">', unsafe_allow_html=True)
                    
                    # Tasto di "Spunta" (Sposta nel carrello)
                    if st.button(f"✅ PRESO!", key=f"S_check_{idx}", use_container_width=True):
                        st.session_state.df.at[idx, 'Stato'] = "NEL CARRELLO"
                        save()
                        st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.divider()

        # Bottone finale per svuotare tutto a fine spesa
        if not st.session_state.df[st.session_state.df['Stato'].isin(["DA COMPRARE", "NEL CARRELLO"])].empty:
            st.write("")
            if st.button("🏁 HO FINITO LA SPESA", key="k_reset_spesa", type="primary", use_container_width=True):
                # Reset stati e rimozione manuali
                st.session_state.df.loc[st.session_state.df['Stato'].isin(["DA COMPRARE", "NEL CARRELLO"]), 'Stato'] = ""
                st.session_state.df = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].reset_index(drop=True)
                save()
                st.rerun()

# ==========================================
# --- TAB 3: CATALOGO PRODOTTI           ---
# ==========================================
with tab3:
    st.markdown("### 📦 Catalogo Prodotti")
    
    search = st.text_input("Cerca prodotto...", placeholder="Es: Pasta...", key="search_cat_final_v6")
    
    if 'df' in st.session_state:
        # Filtro e ordinamento
        df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy().sort_values("Prodotto")
        
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
                    if pd.notna(url) and str(url).startswith("http"):
                        st.markdown(f'<img src="{url}" class="cat-img">', unsafe_allow_html=True)
                
                # Chiavi univoche C_ per il catalogo
                if is_in_list:
                    st.button("🛒 IN LISTA", key=f"C_in_cat_{idx}", disabled=True)
                else:
                    if st.button(f"➕ AGGIUNGI", key=f"C_add_cat_{idx}"):
                        st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                        st.session_state.df.at[idx, 'User'] = utente
                        save()
                        st.toast(f"✅ {row['Prodotto']} aggiunto!")
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()
