import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Conexão com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets"]
info = dict(st.secrets["gcp_service_account"])
info["private_key"] = info["private_key"].replace("\\n", "\n") # Corrige quebras de linha
creds = Credentials.from_service_account_info(info, scopes=scope)
client = gspread.authorize(creds)

# CONFIGURAÇÃO: Coloque o nome EXATO da sua planilha aqui
NOME_PLANILHA = "crm culundria" 

try:
    sheet = client.open(NOME_PLANILHA).worksheet("CLIENTES")
except Exception as e:
    st.error(f"Erro: Planilha não encontrada ou sem permissão. {e}")
    st.stop()

# INTERFACE
st.set_page_config(page_title="Alquimista Culundria", page_icon="🍺")
st.title("🍺 Portal do Alquimista")

cpf_input = st.text_input("Digite seu CPF ou CNPJ (só números):")

if cpf_input:
    df = pd.DataFrame(sheet.get_all_records())
    df['ID_Cliente'] = df['ID_Cliente'].astype(str)
    cliente = df[df['ID_Cliente'] == cpf_input.strip()]

    if not cliente.empty:
        c = cliente.iloc[0]
        st.balloons()
        st.header(f"Olá, {c['Nome_Completo']}!")
        st.subheader(f"Nível: {c['Nível_Atual']}")
        
        progresso = float(c['Progresso_Copo']) if c['Progresso_Copo'] != "" else 0.0
        st.write("Seu progresso para o próximo nível:")
        st.progress(progresso)
        st.metric("Saldo de Pontos", f"{c['Pontos_Totais']} pts")
    else:
        st.warning("CPF não encontrado. Fale com a Culundria no WhatsApp!")
