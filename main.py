import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. Configuração de Acesso ao Google Sheets via Secrets
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# SUBSTITUA PELO NOME EXATO DA SUA PLANILHA
URL_PLANILHA = "PROGRAMA FIDELIDADE" 
sheet = client.open(URL_PLANILHA).worksheet("CLIENTES")

# 2. Interface do Alquimista
st.set_page_config(page_title="Portal do Alquimista Culundria", page_icon="🍺")

st.title("🍺 Portal do Alquimista Culundria")
st.markdown("---")

# 3. Sistema de Login
cpf_input = st.text_input("Digite seu CPF ou CNPJ para acessar:", placeholder="Apenas números")

if cpf_input:
    # Lendo os dados da aba CLIENTES
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Garantindo que o ID_Cliente seja tratado como string para comparação
    df['ID_Cliente'] = df['ID_Cliente'].astype(str)
    
    # Busca o cliente
    cliente = df[df['ID_Cliente'] == cpf_input.strip()]
    
    if not cliente.empty:
        c = cliente.iloc[0]
        nome = c['Nome_Completo']
        pontos = c['Pontos_Totais']
        nivel = c['Nível_Atual']
        progresso = float(c['Progresso_Copo']) if c['Progresso_Copo'] != "" else 0.0
        
        st.header(f"Olá, {nome.split()[0]}! 👋")
        st.subheader(f"Você é um Alquimista **{nivel}**")
        
        # 4. A Gamificação: O Copo de Chopp
        st.write("### Seu progresso para o próximo nível:")
        
        # Barra de progresso customizada (cor de cerveja)
        st.progress(progresso)
        st.caption(f"Você tem atualmente **{pontos} pontos** acumulados.")
        
        # 5. Seção de Troféus e Mimos
        st.markdown("---")
        st.write("### 🏆 Seus Benefícios")
        col1, col2 = st.columns(2)
        
        with col1:
            if pontos >= 500:
                st.success("✅ 2 Copos de Vidro")
            else:
                st.info("🔒 2 Copos de Vidro (500 pts)")
                
            if pontos >= 1000:
                st.success("✅ Copo Térmico + Tábua")
            else:
                st.info("🔒 Copo Térmico + Tábua (1000 pts)")

        with col2:
            st.write("**Serviços Ativos:**")
            if nivel in ["Bronze", "Prata", "Ouro"]:
                st.write("✨ Higienização Simples na Entrega")
            if nivel == "Ouro":
                st.write("🛠️ Higienização Completa Anual")
        
        # 6. Botão de Indicação
        st.markdown("---")
        msg_whats = f"Fala! Estou te indicando a Culundria. Se você pedir seu 1º barril, eu ganho pontos e você ganha 100 de bônus! CPF do Indicador: {cpf_input}"
        link_whats = f"https://wa.me/55035998732583?text={msg_whats}"
        
        st.link_button("🚀 Indicar um Amigo no WhatsApp", link_whats)

    else:
        st.error("Ops! Não encontramos esse CPF. Verifique se digitou corretamente ou fale com a gente no WhatsApp.")

st.sidebar.image("https://via.placeholder.com/150", caption="Culundria Cervejaria") # Substitua pela sua Logo
st.sidebar.write("Dúvidas? Entre em contato pelo WhatsApp comercial.")
