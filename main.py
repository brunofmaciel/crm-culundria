import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando Streamlit)
st.set_page_config(page_title="Alquimista Culundria", page_icon="🍺", layout="centered")

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

# Nome EXATO da sua planilha no Google Drive
NOME_PLANILHA = "crm-culundria" 

# 3. BARRA LATERAL (LOGO E NAVEGAÇÃO)
with st.sidebar:
    try:
        st.image("logoculundria.png", use_container_width=True)
    except:
        st.warning("Arquivo 'logoculundria.png' não encontrado no GitHub.")
    
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
                st.header(f"Olá, {c['Nome_Completo']}!")
                
                # Nível e Progresso
                st.subheader(f"Nível Atual: {c['Nível_Atual']}")
                
                try:
                    val_bruto = float(c['Progresso_Copo']) if str(c['Progresso_Copo']).strip() != "" else 0.0
                    if val_bruto > 1.0: val_bruto = val_bruto / 100.0
                    progresso = min(max(val_bruto, 0.0), 1.0)
                except:
                    progresso = 0.0

                st.write("### Seu progresso para o próximo nível:")
                st.progress(progresso)
                st.caption(f"Você já completou **{int(progresso * 100)}%** do caminho!")
                st.metric("Saldo de Pontos", f"{c['Pontos_Totais']} pts")

                # --- HISTÓRICO DE VENDAS ---
                st.markdown("---")
                st.write("### 📜 Seu Histórico de Alquimia")
                try:
                    sheet_vendas = client.open(NOME_PLANILHA).worksheet("VENDAS")
                    df_vendas = pd.DataFrame(sheet_vendas.get_all_records())
                    df_vendas = df_vendas.replace(0, "").fillna("")
                    
                    minhas_vendas = df_vendas[df_vendas['ID_Cliente'].astype(str) == cpf_input.strip()]
                    
                    if not minhas_vendas.empty:
                        # Ajuste as colunas abaixo conforme sua planilha real
                        colunas_venda = ['ID_Pedido','Data_Venda', 'Litragem_Total', 'Total Pontos']
                        st.table(minhas_vendas[colunas_venda])
                    else:
                        st.info("Ainda não constam barris registrados.")
                except Exception as e:
                    st.warning(f"Não foi possível carregar o histórico: {e}")

                # --- FORMULÁRIO DE INDICAÇÃO ---
                st.markdown("---")
                st.write("### 🚀 Indique um Amigo e Ganhe Pontos!")
                with st.form("form_indicacao", clear_on_submit=True):
                    nome_amigo = st.text_input("Nome do Amigo")
                    tel_amigo = st.text_input("WhatsApp do Amigo (com DDD)")
                    submit = st.form_submit_button("Enviar Indicação")
                    
                    if submit:
                        if nome_amigo and tel_amigo:
                            sheet_ind = client.open(NOME_PLANILHA).worksheet("INDICAÇÕES")
                            sheet_ind.append_row([cpf_input, nome_amigo, tel_amigo, "Pendente"])
                            st.success(f"Indicação de {nome_amigo} enviada!")
                        else:
                            st.error("Preencha todos os campos.")
            else:
                st.warning("CPF não encontrado. Fale com o mestre cervejeiro!")
        except Exception as e:
            st.error(f"Erro ao acessar dados: {e}")

# ==========================================
# ABA 2: PAINEL DO MESTRE (ADMIN)
# ==========================================
        # ==========================================
# ABA 2: PAINEL DO MESTRE (ADMIN)
# ==========================================
elif aba == "Painel do Mestre (Admin)":
    st.title("🏰 Painel do Mestre Cervejeiro")
    
    # 1. Definição da Senha
    senha = st.sidebar.text_input("Senha de Acesso:", type="password")
    
    if senha == st.secrets["admin_password"]:
        st.success("Acesso autorizado, Bruno!")
        
        try:
            # 2. Carregamento dos Dados
            df_clientes = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("CLIENTES").get_all_records())
            df_vendas = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("VENDAS").get_all_records())
            
            # 3. Limpeza de Dados (Anti-5000 litros)
            def limpar_numero(valor):
                if isinstance(valor, str):
                    valor = valor.replace('.', '').replace(',', '.')
                return pd.to_numeric(valor, errors='coerce')

            df_vendas['Litragem_Total'] = df_vendas['Litragem_Total'].apply(limpar_numero).fillna(0)
            df_clientes['Pontos_Totais'] = df_clientes['Pontos_Totais'].apply(limpar_numero).fillna(0)

            # --- 4. EXIBIÇÃO DAS MÉTRICAS (KPIs) ---
            st.subheader("📊 Resumo de Operação")
            c1, c2, c3 = st.columns(3)
            
            total_litros = df_vendas['Litragem_Total'].sum()
            num_clientes = len(df_clientes)
            
            with c1:
                st.metric("Total Vendido", f"{total_litros:,.1f} L".replace(".", ","))
            with c2:
                st.metric("Alquimistas", num_clientes)
            with c3:
                media = total_litros / num_clientes if num_clientes > 0 else 0
                st.metric("Média/Cli", f"{media:.1f} L".replace(".", ","))

            # --- 5. GRÁFICOS E RANKING ---
            st.markdown("---")
            col_esq, col_dir = st.columns(2)
            
            with col_esq:
                st.subheader("🏆 Top 5 Alquimistas")
                if 'Pontos_Totais' in df_clientes.columns:
                    top_5 = df_clientes.nlargest(5, 'Pontos_Totais')[['Nome_Completo', 'Pontos_Totais']]
                    st.table(top_5)
            
            with col_dir:
                st.subheader("🍺 Estilos mais Pedidos")
                if 'Estilo_Chopp' in df_vendas.columns:
                    vendas_estilo = df_vendas.groupby('Estilo_Chopp')['Litragem_Total'].sum()
                    st.bar_chart(vendas_estilo)

        except Exception as e:
            st.error(f"Erro ao processar dados da planilha: {e}")

    elif senha != "":
        st.error("Senha incorreta. Verifique os Secrets do Streamlit.")

# --- FIM DO ARQUIVO ---
