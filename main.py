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

# --- MENU DE NAVEGAÇÃO ---
st.sidebar.title("Navegação")
aba = st.sidebar.radio("Ir para:", ["Portal do Cliente", "Painel do Mestre (Admin)"])

# ==========================================
# ABA 1: PORTAL DO CLIENTE (O que já fizemos)
# ==========================================
if aba == "Portal do Cliente":
    st.title("🍺 Portal do Alquimista")
    # [COLE AQUI TODO O CÓDIGO DO CPF E HISTÓRICO QUE JÁ FUNCIONA]
st.set_page_config(page_title="Alquimista Culundria", page_icon="🍺")
st.title("🍺 Portal do Alquimista")
st.sidebar.image("logoculundria.png", use_container_width=True)
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

# ==========================================
# ABA 2: PAINEL DO MESTRE (ADMIN)
# ==========================================
elif aba == "Painel do Mestre (Admin)":
    st.title("🏰 Painel do Mestre Cervejeiro")
    
    senha = st.sidebar.text_input("Digite a senha de acesso:", type="password")
    
    if senha == st.secrets["admin_password"]:
        st.success("Acesso autorizado, Bruno!")
        
        # --- CARREGANDO DADOS PARA O DASHBOARD ---
        df_clientes = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("CLIENTES").get_all_records())
        df_vendas = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("VENDAS").get_all_records())
        
        # --- 1. MÉTRICAS RÁPIDAS (KPIs) ---
        col1, col2, col3 = st.columns(3)
        with col1:
            total_litros = df_vendas['Litragem_Total'].sum()
            st.metric("Total Litros Vendidos", f"{total_litros} L")
        with col2:
            num_clientes = len(df_clientes)
            st.metric("Clientes Cadastrados", num_clientes)
        with col3:
            # Média de litros por cliente
            media = total_litros / num_clientes if num_clientes > 0 else 0
            st.metric("Média por Cliente", f"{media:.1f} L")

        # --- 2. RANKING DE ALQUIMISTAS (TOP 5) ---
        st.markdown("---")
        st.subheader("🏆 Top 5 Maiores Consumidores")
        # Ordena pelos pontos totais
        top_5 = df_clientes.nlargest(5, 'Pontos_Totais')[['Nome_Completo', 'Pontos_Totais', 'Nível_Atual']]
        st.table(top_5)

        # --- 3. GRÁFICO DE VENDAS POR ESTILO ---
        st.markdown("---")
        st.subheader("📊 Estilos mais Pedidos")
        vendas_estilo = df_vendas.groupby('Estilo_Chopp')['Litragem_Total'].sum()
        st.bar_chart(vendas_estilo)

        # --- 4. NOVAS INDICAÇÕES ---
        st.markdown("---")
        st.subheader("🚀 Indicações Pendentes")
        try:
            df_ind = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("INDICAÇÕES").get_all_records())
            st.dataframe(df_ind[df_ind['Status'] == 'Pendente'])
        except:
            st.info("Nenhuma indicação nova no momento.")

    elif senha != "":
        st.error("Senha incorreta. Acesso negado.")


        
# --- BUSCA HISTÓRICO DE VENDAS ---
        st.markdown("---")
        st.write("### 📜 Seu Histórico de Alquimia")
        
        try:
            # Abre a aba de Vendas
            sheet_vendas = client.open(NOME_PLANILHA).worksheet("VENDAS")
            df_vendas = pd.DataFrame(sheet_vendas.get_all_records())

            # --- O CONSERTO PARA O "0" ESTÁ AQUI ---
            # Esta linha substitui qualquer 0 ou valor vazio por um texto limpo
            df_vendas = df_vendas.replace(0, "")
            df_vendas = df_vendas.fillna("")
            
            # Filtra as vendas pelo CPF do cliente logado
            minhas_vendas = df_vendas[df_vendas['ID_Cliente'].astype(str) == cpf_input.strip()]
            
            if not minhas_vendas.empty:
                # Seleciona apenas as colunas importantes para mostrar ao cliente
                exibir_vendas = minhas_vendas[['ID_Pedido','Data_Venda', 'Litragem_Total', "Total Pontos"]]
                st.table(exibir_vendas) # Mostra uma tabela limpa
            else:
                st.info("Ainda não constam barris registrados. Que tal pedir o próximo?")
        except:
            st.warning("Não foi possível carregar o histórico agora.")
          
        st.markdown("---")
        st.write("### 🚀 Indique um Amigo e Ganhe Pontos!")
        
        with st.form("form_indicacao", clear_on_submit=True):
            nome_amigo = st.text_input("Nome do Amigo")
            tel_amigo = st.text_input("WhatsApp do Amigo (com DDD)")
            submit = st.form_submit_button("Enviar Indicação")
            
            if submit:
                if nome_amigo and tel_amigo:
                    # Grava na aba INDICAÇÕES da Planilha
                    sheet_ind = client.open(NOME_PLANILHA).worksheet("INDICAÇÕES")
                    sheet_ind.append_row([cpf_input, nome_amigo, tel_amigo, "Pendente"])
                    st.success(f"Indicação de {nome_amigo} enviada! Assim que ele fizer o 1º pedido, seus pontos caem na conta.")
                else:
                    st.error("Preencha o nome e o telefone do seu amigo.")
      
    else:
        st.warning("CPF não encontrado. Fale com a Culundria no WhatsApp!")
