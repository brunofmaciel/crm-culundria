import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Alquimista Culundria", page_icon="🍺", layout="centered")

# --- ESTILO LIMPO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stButton>button { border-radius: 4px; background-color: #262730; color: white; border: None; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

try:
    info = dict(st.secrets["gcp_service_account"])
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(info, scopes=scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"Erro na conexão com Google: {e}")
    st.stop()

NOME_PLANILHA = "crm-culundria" 

# 3. BARRA LATERAL
with st.sidebar:
    try:
        st.image("logoculundria.png", use_container_width=True)
    except:
        st.warning("Logo não encontrada.")
    
    st.markdown("<h2 style='text-align: center;'>Culundria Cervejaria</h2>", unsafe_allow_html=True)
    st.write("📍 Cruzília, MG")
    st.markdown("---")
    aba = st.sidebar.radio("Ir para:", ["Portal do Cliente", "Painel do Mestre (Admin)"])

# ==========================================
# ABA 1: PORTAL DO CLIENTE
# ==========================================
if aba == "Portal do Cliente":
    st.title("🍺 Portal do Alquimista")
    cpf_input = st.text_input("Digite seu CPF (apenas números):")

    if cpf_input:
        try:
            sheet = client.open(NOME_PLANILHA).worksheet("CLIENTES")
            df = pd.DataFrame(sheet.get_all_records())
            df['ID_Cliente'] = df['ID_Cliente'].astype(str)
            cliente = df[df['ID_Cliente'] == cpf_input.strip()]

            if not cliente.empty:
                c = cliente.iloc[0]
                st.balloons()

                # Cálculo do Progresso
                try:
                    val_bruto = float(c['Progresso_Copo']) if str(c['Progresso_Copo']).strip() != "" else 0.0
                    if val_bruto > 1.0: val_bruto = val_bruto / 100.0
                    progresso = min(max(val_bruto, 0.0), 1.0)
                except:
                    progresso = 0.0

                # Layout Principal
                with st.container():
                    st.header(f"Olá, {c['Nome_Completo']}!")
                    st.write("---")
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.subheader(f"Nível: {c['Nível_Atual']}")
                        st.progress(progresso)
                        st.caption(f"Você completou **{int(progresso * 100)}%** do caminho!")
                    with col2:
                        st.metric("Pontos Atuais", f"{c['Pontos_Totais']} pts")

                # Histórico de Vendas
                st.markdown("---")
                st.write("### 📜 Seu Histórico de Alquimia")
                try:
                    sheet_vendas = client.open(NOME_PLANILHA).worksheet("VENDAS")
                    df_vendas = pd.DataFrame(sheet_vendas.get_all_records())
                    df_vendas = df_vendas.replace(0, "").fillna("")
                    minhas_vendas = df_vendas[df_vendas['ID_Cliente'].astype(str) == cpf_input.strip()]
                    
                    if not minhas_vendas.empty:
                        colunas_exibir = ['ID_Pedido', 'Data_Venda', 'Litragem_Total', 'Total Pontos']
                        st.table(minhas_vendas[colunas_exibir])
                    else:
                        st.info("Nenhum registro encontrado.")
                except:
                    st.warning("Erro ao carregar histórico.")

                # Formulário de Indicação
                st.markdown("---")
                st.write("### 🚀 Indique um Amigo")
                with st.form("form_indicacao", clear_on_submit=True):
                    nome_amigo = st.text_input("Nome do Amigo")
                    tel_amigo = st.text_input("WhatsApp")
                    if st.form_submit_button("Enviar"):
                        if nome_amigo and tel_amigo:
                            client.open(NOME_PLANILHA).worksheet("INDICAÇÕES").append_row([cpf_input, nome_amigo, tel_amigo, "Pendente"])
                            st.success("Indicação enviada!")
                        else:
                            st.error("Preencha os campos.")
            else:
                st.warning("CPF não cadastrado.")
        except Exception as e:
            st.error(f"Erro: {e}")

# ==========================================
# ABA 2: PAINEL DO MESTRE (ADMIN)
# ==========================================
elif aba == "Painel do Mestre (Admin)":
    st.title("🏰 Painel do Mestre")
    senha = st.sidebar.text_input("Senha:", type="password")
    
    if senha == st.secrets["admin_password"]:
        st.success("Acesso autorizado!")
        try:
            df_clientes = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("CLIENTES").get_all_records())
            df_vendas = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("VENDAS").get_all_records())
            
            def limpar_num(v):
                if isinstance(v, str): v = v.replace('.', '').replace(',', '.')
                return pd.to_numeric(v, errors='coerce')

            df_vendas['Litragem_Total'] = df_vendas['Litragem_Total'].apply(limpar_num).fillna(0)
            
            st.subheader("📊 Resumo")
            c1, c2, c3 = st.columns(3)
            total = df_vendas['Litragem_Total'].sum()
            c1.metric("Total Vendido", f"{total:,.1f} L".replace(".", ","))
            c2.metric("Clientes", len(df_clientes))
            c3.metric("Média/Cli", f"{(total/len(df_clientes)):.1f} L" if len(df_clientes)>0 else "0")

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🏆 Top 5")
                st.table(df_clientes.nlargest(5, 'Pontos_Totais')[['Nome_Completo', 'Pontos_Totais']])
            with col_b:
                st.subheader("🍺 Estilos")
                st.bar_chart(df_vendas.groupby('Estilo Chopp')['Litragem_Total'].sum())
        except Exception as e:
            st.error(f"Erro no Admin: {e}")
    elif senha != "":
        st.error("Senha incorreta.")
