import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Conexão com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

info = dict(st.secrets["gcp_service_account"])
info["private_key"] = info["private_key"].replace("\\n", "\n")
creds = Credentials.from_service_account_info(info, scopes=scope)
client = gspread.authorize(creds)

# CONFIGURAÇÃO: Coloque o nome EXATO da sua planilha aqui
NOME_PLANILHA = "crm-culundria" 

try:
    sheet = client.open(NOME_PLANILHA).worksheet("CLIENTES")
except Exception as e:
    st.error(f"Erro ao abrir a planilha: {e}")
    st.stop()

# INTERFACE
st.set_page_config(page_title="Alquimista Culundria", page_icon="🍺")
st.title("🍺 Portal do Alquimista")
t.sidebar.image("logoculundria.crdownload", use_container_width=True)
st.sidebar.markdown(f"<h2 style='text-align: center;'>Culundria Cervejaria</h2>", unsafe_allow_html=True)
st.sidebar.title("Culundria Cervejaria")
st.sidebar.markdown("---")
st.sidebar.write("📍 Cruzília, MG")

cpf_input = st.text_input("Digite seu CPF (só números):")

if cpf_input:
    df = pd.DataFrame(sheet.get_all_records())
    df['ID_Cliente'] = df['ID_Cliente'].astype(str)
    cliente = df[df['ID_Cliente'] == cpf_input.strip()]

    if not cliente.empty:
        c = cliente.iloc[0]
        st.balloons()
        st.header(f"Olá, {c['Nome_Completo']}!")
        st.subheader(f"Nível: {c['Nível_Atual']}")
        
        # --- Cálculo Seguro do Progresso ---
        try:
            val_bruto = float(c['Progresso_Copo']) if str(c['Progresso_Copo']).strip() != "" else 0.0
            
            # Se o valor for maior que 1 (ex: 80), dividimos por 100 para virar 0.8
            if val_bruto > 1.0:
                val_bruto = val_bruto / 100.0
            
            # Garante que o valor fique entre 0.0 e 1.0 para não dar erro no Streamlit
            progresso = min(max(val_bruto, 0.0), 1.0)
            
        except ValueError:
            progresso = 0.0

        # --- Exibição do Copo de Chopp ---
        st.write("### Seu progresso para o próximo nível:")
        st.progress(progresso)
        
        # Mostra a porcentagem escrita para o cliente (ex: 85%)
        st.caption(f"Você já completou **{int(progresso * 100)}%** do caminho!")
    else:
        st.warning("CPF não encontrado. Fale com a Culundria no WhatsApp!")
