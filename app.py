import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configurazione Pagina (Inizio file)
st.set_page_config(page_title="Borello Smart", page_icon="🛒", layout="wide")
# --- 1. CONFIGURAZIONE E CSS (Sostituisce righe 8-97) ---
# --- 1. CONFIGURAZIONE E CSS AGGIORNATO ---
st.markdown("""
<style>
    .stMainBlockContainer { padding: 1rem !important; }

    /* Nome Prodotto: Dimensioni raddoppiate */
    .product-name-large {
        font-size: 28px !important;  /* Font molto grande */
        font-weight: 800 !important;
        line-height: 1.2;
        color: #111111;
        display: block;
    }
    
    /* Info Corsia */
    .product-cap-large { 
        font-size: 18px !important; 
        color: #666666; 
        margin-bottom: 5px;
    }

    /* Immagine: Raddoppiata */
    .cat-img-large {
        width: 80px !important; 
        height: 80px !important;
        object-fit: cover;
        border-radius: 12px;
        border: 1px solid #ddd;
    }

    /* Bottone + : Grande e facile da cliccare */
    .stButton>button {
        width: 100% !important; /* Occupa tutta la larghezza per essere cliccato bene */
        height: 60px !important;
        font-size: 25px !important;
        border-radius: 15px !important;
        background-color: #f8f9fa !important;
        border: 2px solid #eee !important;
        margin-top: 5px;
        margin-bottom: 20px;
    }

    /* Divisore tra prodotti più marcato */
    hr { margin: 15px 0 !important; border-top: 2px solid #eee !important; }
</style>
""", unsafe_allow_html=True)

# --- TAB 3: CATALOGO ---
with tab3:
    st.write("### 📦 Catalogo")
    search = st.text_input("Cerca...", placeholder="Es: Pasta...", key="search_cat")
    
    df_cat = st.session_state.df[st.session_state.df['Tipo'] != "Manuale"].copy().sort_values("Prodotto")
    if search:
        df_cat = df_cat[df_cat['Prodotto'].str.contains(search, case=False, na=False)]

    for idx, row in df_cat.iterrows():
        is_in_list = row['Stato'] == "DA COMPRARE"
        
        # Creiamo la riga con HTML per testo e foto, e una colonna piccola solo per il bottone
        col_main, col_btn = st.columns([0.83, 0.17])
        
        with col_main:
            color = "#a0a0a0" if is_in_list else "#111111"
            txt = f"{row['Prodotto']} (In Lista)" if is_in_list else row['Prodotto']
            url = row.get('URL_Foto', "")
            
            # HTML per allineare Testo e Foto sulla stessa riga "blindata"
            img_html = f'<img src="{url}" class="cat-img">' if (pd.notna(url) and str(url).startswith("http")) else '<div style="width:35px"></div>'
            
            st.markdown(f"""
                <table class="cat-table">
                    <tr>
                        <td class="cat-td-txt">
                            <span class="product-name" style="color:{color}">{txt}</span>
                            <span class="product-cap">📍 {row['Corsia']}</span>
                        </td>
                        <td class="cat-td-img">{img_html}</td>
                    </tr>
                </table>
            """, unsafe_allow_html=True)
        
        with col_btn:
            if is_in_list:
                st.button("🛒", key=f"in_{idx}", disabled=True)
            else:
                if st.button("➕", key=f"add_{idx}"):
                    st.session_state.df.at[idx, 'Stato'] = "DA COMPRARE"
                    st.session_state.df.at[idx, 'User'] = utente
                    save()
                    st.toast(f"✅ Aggiunto!")
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
