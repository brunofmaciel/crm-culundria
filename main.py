import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Culundria Confraria", page_icon="🍺", layout="centered")

# --- ESTILO PREMIUM CULUNDRIA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
    [data-testid="stAppViewContainer"] { background-color: #0b0e27; color: #ffffff; font-family: 'Montserrat', sans-serif; }
    [data-testid="stSidebar"] { background-color: #050714; }
    .stMetric, .metric-card { background-color: #161b3d; padding: 1.5rem; border-radius: 10px; border: 1px solid #e68a00; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #e68a00; color: white; font-weight: bold; border: none; padding: 0.6rem; text-transform: uppercase; transition: 0.3s; }
    .stButton>button:hover { background-color: #ff9f00; box-shadow: 0 0 15px #e68a00; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #e68a00, #ffcc33); }
    .stTable { background-color: #161b3d; border-radius: 10px; color: white; }
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

# --- FUNÇÃO DE NÍVEIS DA CONFRARIA ---
def calcular_status_confraria(pontos):
    pontos = float(pontos)
    if pontos <= 500:
        return {"nivel": "Explorador", "desc": "Você está descobrindo novos horizontes. Cada gole é uma nova experiência!", "cor": "#a8dadc", "proximo": f"Faltam {501 - pontos:.0f} pontos para 'Chegado'."}
    elif pontos <= 1000:
        return {"nivel": "Chegado", "desc": "A casa já é sua! Você já conhece o caminho das torneiras.", "cor": "#e68a00", "proximo": f"Faltam {1001 - pontos:.0f} pontos para 'Tarimbado'."}
    elif pontos <= 2000:
        return {"nivel": "Tarimbado", "desc": "Veterano de guerra! Seu paladar já viveu grandes histórias conosco.", "cor": "#d4a017", "proximo": f"Faltam {2001 - pontos:.0f} pontos para 'Patrimônio'."}
    else:
        return {"nivel": "Patrimônio da Culundria", "desc": "Você não é mais cliente, é parte da nossa história. Seu lugar no balcão é sagrado.", "cor": "#ffcc33", "proximo": "Você atingiu o topo! 🍻"}

# --- INICIALIZAÇÃO DA MEMÓRIA (SESSION STATE) ---
if "aba_selecionada" not in st.session_state:
    st.session_state.aba_selecionada = "Meu Painel (Login)"
if "logado" not in st.session_state:
    st.session_state.logado = False
if "dados_usuario" not in st.session_state:
    st.session_state.dados_usuario = None

# --- 3. LÓGICA DE NAVEGAÇÃO ---
opcoes_menu = ["Meu Painel (Login)", "Fazer Parte da Confraria", "Área do Mestre"]
indice_atual = opcoes_menu.index(st.session_state.aba_selecionada)

with st.sidebar:
    try:
        st.image("logoculundria.png", use_container_width=True)
    except:
        st.warning("Logo não encontrada.")
    st.markdown("<h2 style='text-align: center;'>Culundria Cervejaria</h2>", unsafe_allow_html=True)
    st.write("📍 Cruzília, MG")
    st.markdown("---")
    aba = st.sidebar.radio("Ir para:", opcoes_menu, index=indice_atual)
    st.session_state.aba_selecionada = aba
    
    if st.session_state.logado:
        if st.sidebar.button("SAIR / DESLOGAR"):
            st.session_state.logado = False
            st.session_state.dados_usuario = None
            st.rerun()

# ==========================================
# ABA 1: MEU PAINEL (LOGIN E DASHBOARD)
# ==========================================
if aba == "Meu Painel (Login)":
    if not st.session_state.logado:
        st.title("🍺 Culundria Confraria")
        st.write("Entre para ver seus Goles de Vantagem.")
        
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            cpf_input = st.text_input("CPF (apenas números):", key="login_cpf")
        with col_l2:
            senha_input = st.text_input("Senha:", type="password", key="login_senha")

        if st.button("ENTRAR NO PAINEL"):
            if cpf_input and senha_input:
                try:
                    sheet = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                    df = pd.DataFrame(sheet.get_all_records())
                    df['ID_Cliente'] = df['ID_Cliente'].astype(str).str.strip()
                    cliente = df[df['ID_Cliente'] == cpf_input.strip()]

                    if not cliente.empty:
                        c = cliente.iloc[0]
                        if str(senha_input).strip() == str(c['Senha']).strip():
                            st.session_state.logado = True
                            st.session_state.dados_usuario = c.to_dict()
                            st.rerun()
                        else:
                            st.error("Senha incorreta!")
                    else:
                        st.warning("CPF não cadastrado.")
                except Exception as e:
                    st.error(f"Erro ao carregar dados: {e}")
            else:
                st.error("Preencha todos os campos.")
        
        st.markdown("---")
        if st.button("✨ Ainda não faz parte? Cadastre-se aqui"):
            st.session_state.aba_selecionada = "Fazer Parte da Confraria"
            st.rerun()

    else:
        # PAINEL DO USUÁRIO LOGADO
        c = st.session_state.dados_usuario
        resumo = calcular_status_confraria(c['Pontos_Totais'])
        
        st.title(f"Olá, {c['Nome_Completo'].split()[0].upper()}! 🍻")
        
        # Card de Status
        st.markdown(f"""
            <div style='background-color: #161b3d; padding: 25px; border-radius: 15px; border-left: 8px solid {resumo['cor']};'>
                <h2 style='margin:0; color: {resumo['cor']}; font-size: 1.2em;'>STATUS: {resumo['nivel'].upper()}</h2>
                <p style='color: #ffffff; font-size: 1.1em; margin-top: 10px;'>"{resumo['desc']}"</p>
                <hr style='border: 0.1px solid #333;'>
                <p style='color: #aaa; font-size: 0.85em; font-style: italic;'>{resumo['proximo']}</p>
            </div>
        "", unsafe_allow_html=True)

        st.write("")
        st.metric("MEUS GOLES DE VANTAGEM", f"{c['Pontos_Totais']} PTS")

        # Histórico
        st.markdown("### 📜 MEU HISTÓRICO")
        try:
            sheet_v = client.open(NOME_PLANILHA).worksheet("VENDAS")
            df_v = pd.DataFrame(sheet_v.get_all_records())
            df_v['ID_Cliente'] = df_v['ID_Cliente'].astype(str)
            minhas_v = df_v[df_v['ID_Cliente'] == str(c['ID_Cliente'])]
            if not minhas_v.empty:
                st.table(minhas_v[['Data_Venda', 'Litragem_Total', 'Total Pontos']])
            else:
                st.info("Nenhum barril registrado ainda. Que tal o próximo?")
        except:
            st.info("Buscando barris no histórico...")

# ==========================================
# ABA 2: CADASTRO
# ==========================================
elif aba == "Fazer Parte da Confraria":
    st.title("🧪 Entre para a Confraria")
    st.write("Cadastre-se para começar sua jornada.")

    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        cpf_novo = st.text_input("CPF (apenas números)")
        whatsapp = st.text_input("WhatsApp (com DDD)")
        email = st.text_input("E-mail")
        senha_n = st.text_input("Crie uma Senha", type="password")
        
        if st.form_submit_button("CRIAR MINHA CONTA"):
            if nome and cpf_novo and whatsapp and email and senha_n:
                try:
                    sheet_cli = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                    df_check = pd.DataFrame(sheet_cli.get_all_records())
                    if str(cpf_novo).strip() in df_check['ID_Cliente'].astype(str).values:
                        st.warning("CPF já cadastrado!")
                    else:
                        data_h = pd.Timestamp.now().strftime("%d/%m/%Y")
                        # A=CPF, B=Nome, C=WhatsApp, D=Email, E=Status, F=Pontos, G=Progresso, H=Data, I=Senha
                        nova_linha = [str(cpf_novo).strip(), nome.strip().upper(), whatsapp.strip(), email.strip().lower(), "Explorador", 0, 0, data_h, senha_n.strip()]
                        sheet_cli.append_row(nova_linha)
                        st.success("Cadastro realizado! Volte ao painel e faça login.")
                        st.balloons()
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("Preencha todos os campos.")

# ==========================================
# ABA 3: ÁREA DO MESTRE
# ==========================================
elif aba == "Área do Mestre":
    st.title("🏰 Área do Mestre")
    senha_adm = st.sidebar.text_input("Senha Admin:", type="password", key="adm_senha")
    if senha_adm == st.secrets["admin_password"]:
        st.success("Grimório de dados aberto!")
        # Sua lógica de admin aqui
    elif senha_adm:
        st.error("Senha incorreta.")
