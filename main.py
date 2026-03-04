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
    try: p = float(pontos)
    except: p = 0.0
    if p <= 500:
        return {"nivel": "Explorador", "desc": "Descobrindo novos horizontes.", "cor": "#a8dadc", "proximo_pts": 500, "msg": "Falta pouco para ser 'Chegado'."}
    elif p <= 1000:
        return {"nivel": "Chegado", "desc": "A casa já é sua! O balcão te reconhece.", "cor": "#e68a00", "proximo_pts": 1000, "msg": "Continue para ser 'Tarimbado'."}
    elif p <= 2000:
        return {"nivel": "Tarimbado", "desc": "Veterano de guerra! Grandes histórias conosco.", "cor": "#d4a017", "proximo_pts": 2000, "msg": "Quase um Patrimônio!"}
    else:
        return {"nivel": "Patrimônio da Culundria", "desc": "Você é parte da nossa história sagrada.", "cor": "#ffcc33", "proximo_pts": p, "msg": "Obrigado, lenda! 🍻"}

# --- 3. CONFIGURAÇÃO INICIAL E NAVEGAÇÃO ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "dados_usuario" not in st.session_state:
    st.session_state.dados_usuario = None
if "aba_selecionada" not in st.session_state:
    st.session_state.aba_selecionada = "Meu Painel (Login)"

opcoes_menu = ["Meu Painel (Login)", "Loja de Souvenirs", "Fazer Parte da Confraria", "Área do Mestre"]

with st.sidebar:
    try: st.image("logoculundria.png", use_container_width=True)
    except: st.warning("Logo não encontrada.")
    st.markdown("<h2 style='text-align: center;'>Culundria</h2>", unsafe_allow_html=True)
    
    aba = st.radio("Navegação:", opcoes_menu, index=opcoes_menu.index(st.session_state.aba_selecionada))
    st.session_state.aba_selecionada = aba
    
    if st.session_state.logado:
        if st.sidebar.button("SAIR DA CONFRARIA"):
            st.session_state.logado = False
            st.session_state.dados_usuario = None
            st.rerun()

# ==========================================
# ABA 1: LOGIN E PAINEL (RESTURADA!)
# ==========================================
if aba == "Meu Painel (Login)":
    if not st.session_state.logado:
        st.title("🍺 Goles de Vantagem")
        col_l1, col_l2 = st.columns(2)
        with col_l1: cpf_input = st.text_input("CPF (apenas números):")
        with col_l2: senha_input = st.text_input("Senha:", type="password")

        if st.button("ENTRAR NA CONFRARIA"):
            try:
                sheet = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                df = pd.DataFrame(sheet.get_all_records())
                # Normalização do CPF
                df['ID_Cliente'] = df['ID_Cliente'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(11)
                cpf_digitado = "".join(filter(str.isdigit, str(cpf_input))).strip().zfill(11)
                
                cliente = df[df['ID_Cliente'] == cpf_digitado]
                if not cliente.empty:
                    c = cliente.iloc[0]
                    if str(senha_input).strip() == str(c['Senha']).strip():
                        st.session_state.logado = True
                        st.session_state.dados_usuario = c.to_dict()
                        st.rerun()
                    else: st.error("Senha incorreta!")
                else: st.warning(f"CPF {cpf_digitado} não localizado.")
            except Exception as e: st.error(f"Erro no login: {e}")
    else:
        # PAINEL LOGADO
        c = st.session_state.dados_usuario
        pts_acumulados = float(c.get('Pontos_Totais', 0))
        saldo_disponivel = float(c.get('Saldo_Atual', pts_acumulados))
        res = calcular_status_confraria(pts_acumulados)
        
        st.title(f"OLÁ, {str(c['Nome_Completo']).split()[0].upper()}! 🍻")
        
        col1, col2 = st.columns(2)
        col1.metric("PONTOS TOTAIS", f"{int(pts_acumulados)} PTS")
        col2.metric("SALDO TROCA", f"{int(saldo_disponivel)} PTS")

        html_card = f"""
        <div style='background-color: #161b3d; padding: 25px; border-radius: 15px; border-left: 8px solid {res['cor']};'>
            <h2 style='margin:0; color: {res['cor']}; font-size: 1.2em;'>STATUS: {res['nivel'].upper()}</h2>
            <p style='color: #ffffff; font-size: 1.1em; margin-top: 10px;'>"{res['desc']}"</p>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)
        st.progress(min(pts_acumulados / res['proximo_pts'], 1.0) if res['proximo_pts'] > 0 else 1.0)

# ==========================================
# ABA 2: LOJA DE SOUVENIRS
# ==========================================
elif aba == "Loja de Souvenirs":
    st.title("🛍️ Loja de Souvenirs")
    if not st.session_state.logado:
        st.warning("Faça login para acessar a loja!")
    else:
        c = st.session_state.dados_usuario
        saldo = float(c.get('Saldo_Atual', c.get('Pontos_Totais', 0)))
        st.subheader(f"Seu Saldo: {int(saldo)} Goles")
        
        produtos = [
            {"nome": "1 Pint (500ml)", "pontos": 150, "img": "🍺"},
            {"nome": "Growler Pet 1L", "pontos": 250, "img": "🧴"},
            {"nome": "Boné Culundria", "pontos": 800, "img": "🧢"},
            {"nome": "Camiseta Confraria", "pontos": 1200, "img": "👕"}
        ]
        
        cols = st.columns(2)
        for i, p in enumerate(produtos):
            with cols[i % 2]:
                st.markdown(f"<div style='background-color: #161b3d; padding: 20px; border-radius: 10px; border: 1px solid #e68a00;'><h3>{p['img']} {p['nome']}</h3><p>{p['pontos']} Goles</p></div>", unsafe_allow_html=True)
                if saldo >= p['pontos']:
                    if st.button(f"Resgatar {p['nome']}", key=f"shop_{i}"):
                        st.success("Pedido enviado ao Mestre!")
                else:
                    st.button("Saldo Insuficiente", key=f"shop_{i}", disabled=True)

# ==========================================
# ABA 3: CADASTRO
# ==========================================
elif aba == "Fazer Parte da Confraria":
    st.title("🧪 Entre para a Confraria")
    with st.form("f_cad"):
        nome = st.text_input("Nome")
        cpf_c = st.text_input("CPF")
        if st.form_submit_button("CADASTRAR"):
            st.info("Cadastro em manutenção, use o WhatsApp para acelerar!")

# ==========================================
# ABA 4: ÁREA DO MESTRE
# ==========================================
elif aba == "Área do Mestre":
    st.title("🏰 Área do Mestre")
    senha = st.text_input("Senha:", type="password", key="mestre_key")
    if senha == st.secrets["admin_password"]:
        st.success("Dados carregados!")
        # (Aqui entra o seu código de gráficos que já funcionava)
