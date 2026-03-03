import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Alquimista Culundria", page_icon="🍺", layout="centered")

# --- ESTILO PREMIUM CULUNDRIA (Inspirado em Dogma) ---
st.markdown("""
    <style>
    /* Importando fonte moderna */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
    
    /* Fundo Escuro Profundo (Navy do Logo) */
    [data-testid="stAppViewContainer"] {
        background-color: #0b0e27;
        color: #ffffff;
        font-family: 'Montserrat', sans-serif;
    }

    /* Barra Lateral */
    [data-testid="stSidebar"] {
        background-color: #050714;
    }

    /* Cards de Informação (Inspirado nos boxes da Dogma) */
    .stMetric, .metric-card {
        background-color: #161b3d;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e68a00; /* Borda Âmbar */
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    /* Customização dos Títulos */
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Botões Alquimistas (Cor Âmbar do Logo) */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        background-color: #e68a00;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.6rem;
        text-transform: uppercase;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #ff9f00;
        box-shadow: 0 0 15px #e68a00;
    }

    /* Barra de Progresso Estilo Cerveja */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #e68a00, #ffcc33);
    }
    
    /* Tabelas Limpas */
    .stTable {
        background-color: #161b3d;
        border-radius: 10px;
        color: white;
    }
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
            # 1. Busca os dados
            sheet = client.open(NOME_PLANILHA).worksheet("CLIENTES")
            df = pd.DataFrame(sheet.get_all_records())
            df['ID_Cliente'] = df['ID_Cliente'].astype(str)
            cliente = df[df['ID_Cliente'] == cpf_input.strip()]

            if not cliente.empty:
                c = cliente.iloc[0]
                st.balloons()

                # --- 2. CÁLCULO DO PROGRESSO (PRECISA VIR AQUI!) ---
                try:
                    # Converte o valor da planilha para número
                    val_bruto = float(c['Progresso_Copo']) if str(c['Progresso_Copo']).strip() != "" else 0.0
                    # Se na planilha estiver 80, transformamos em 0.8 para o Streamlit entender
                    if val_bruto > 1.0: 
                        val_bruto = val_bruto / 100.0
                    progresso = min(max(val_bruto, 0.0), 1.0)
                except:
                    progresso = 0.0 # Valor padrão caso a célula esteja vazia ou com erro

                # --- 3. LAYOUT PREMIUM (ESTILO DOGMA + CULUNDRIA) ---
                st.markdown(f"## BEM-VINDO, ALQUIMISTA {c['Nome_Completo'].split()[0].upper()}!")
                st.write("---")

                # Cards de Status
                col_status, col_pontos = st.columns([2, 1])
                
                with col_status:
                    # Card de Nível usando o Azul Marinho e Âmbar do logo
                    st.markdown(f"""
                        <div style='background-color: #161b3d; padding: 20px; border-radius: 10px; border-left: 5px solid #e68a00;'>
                            <h4 style='margin:0; color: white;'>NÍVEL: {c['Nível_Atual']}</h4>
                            <p style='color: #aaa; font-size: 0.9em; margin:0;'>Sua jornada artesanal continua!</p>
                        </div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    # Aqui a variável 'progresso' já existe, então não dá mais erro!
                    st.progress(progresso)
                    st.caption(f"Você já completou **{int(progresso * 100)}%** do caminho para o próximo nível.")

                with col_pontos:
                    # Métrica de Pontos com destaque Âmbar
                    st.metric("ESSÊNCIA ACUMULADA", f"{c['Pontos_Totais']} PTS")

                # --- 4. HISTÓRICO DE VENDAS ---
                st.markdown("### 📜 GRIMÓRIO DE PEDIDOS")
                try:
                    sheet_vendas = client.open(NOME_PLANILHA).worksheet("VENDAS")
                    df_vendas = pd.DataFrame(sheet_vendas.get_all_records())
                    df_vendas = df_vendas.replace(0, "").fillna("")
                    minhas_vendas = df_vendas[df_vendas['ID_Cliente'].astype(str) == cpf_input.strip()]
                    
                    if not minhas_vendas.empty:
                        colunas_venda = ['ID_Pedido', 'Data_Venda', 'Litragem_Total', 'Total Pontos']
                        st.table(minhas_vendas[colunas_venda])
                    else:
                        st.info("Ainda não constam barris registrados. Que tal o primeiro?")
                except:
                    st.warning("Não foi possível carregar seu histórico agora.")

                # --- 5. FORMULÁRIO DE INDICAÇÃO ---
                st.markdown("---")
                st.write("### 🚀 INDIQUE UM AMIGO")
                with st.form("form_indicacao", clear_on_submit=True):
                    nome_amigo = st.text_input("Nome do Amigo")
                    tel_amigo = st.text_input("WhatsApp (com DDD)")
                    if st.form_submit_button("ENVIAR INDICAÇÃO"):
                        if nome_amigo and tel_amigo:
                            client.open(NOME_PLANILHA).worksheet("INDICAÇÕES").append_row([cpf_input, nome_amigo, tel_amigo, "Pendente"])
                            st.success("Indicação enviada com sucesso!")
                        else:
                            st.error("Por favor, preencha o nome e o telefone.")

            else:
                st.warning("CPF não encontrado na nossa base de alquimistas.")
        except Exception as e:
            st.error(f"Erro ao acessar dados: {e}")
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
