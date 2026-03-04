import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Culundria Confraria", page_icon="🍺", layout="centered")

# --- ESTILO PREMIUM CULUNDRIA (ANTI-AZUL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
    [data-testid="stAppViewContainer"] { background-color: #0b0e27; color: #ffffff; font-family: 'Montserrat', sans-serif; }
    [data-testid="stSidebar"] { background-color: #050714; }
    .stMetric { background-color: #161b3d; padding: 1.5rem; border-radius: 10px; border: 1px solid #e68a00; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #e68a00; color: white; font-weight: bold; border: none; padding: 0.6rem; }
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
    st.error(f"Erro na conexão: {e}")
    st.stop()

NOME_PLANILHA = "crm-culundria" 

# --- FUNÇÃO DE NÍVEIS ---
def calcular_status_confraria(pontos):
    try: p = float(pontos)
    except: p = 0.0
    if p <= 500:
        return {"nivel": "Explorador", "desc": "Descobrindo novos horizontes.", "cor": "#a8dadc", "proximo_pts": 500, "msg": "Falta pouco para ser 'Chegado'."}
    elif p <= 1000:
        return {"nivel": "Chegado", "desc": "A casa já é sua!", "cor": "#e68a00", "proximo_pts": 1000, "msg": "Continue para ser 'Tarimbado'."}
    elif p <= 2000:
        return {"nivel": "Tarimbado", "desc": "Veterano de guerra!", "cor": "#d4a017", "proximo_pts": 2000, "msg": "Quase um Patrimônio!"}
    else:
        return {"nivel": "Patrimônio", "desc": "Você é uma lenda sagrada.", "cor": "#ffcc33", "proximo_pts": p, "msg": "Obrigado, lenda! 🍻"}

# --- 3. CONFIGURAÇÃO DE SESSÃO E NAVEGAÇÃO ---
if "logado" not in st.session_state: st.session_state.logado = False
if "dados_usuario" not in st.session_state: st.session_state.dados_usuario = None
if "aba_selecionada" not in st.session_state: st.session_state.aba_selecionada = "Meu Painel (Login)"

opcoes_menu = ["Meu Painel (Login)", "Loja de Souvenirs", "Fazer Parte da Confraria", "Área do Mestre"]

with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>Culundria</h2>", unsafe_allow_html=True)
    aba = st.radio("Navegação:", opcoes_menu, index=opcoes_menu.index(st.session_state.aba_selecionada))
    st.session_state.aba_selecionada = aba
    if st.session_state.logado:
        if st.button("SAIR DA CONFRARIA"):
            st.session_state.logado = False
            st.rerun()

# ==========================================
# ABA 1: MEU PAINEL (LOGIN E STATUS)
# ==========================================
if aba == "Meu Painel (Login)":
    if not st.session_state.logado:
        st.title("🍺 Goles de Vantagem")
        c1, c2 = st.columns(2)
        with c1: cpf_input = st.text_input("CPF (apenas números):")
        with c2: senha_input = st.text_input("Senha:", type="password")

        if st.button("ENTRAR NA CONFRARIA"):
            try:
                sh = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                df = pd.DataFrame(sh.get_all_records())
                df['ID_Cliente'] = df['ID_Cliente'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(11)
                cpf_digitado = "".join(filter(str.isdigit, str(cpf_input))).strip().zfill(11)
                
                cliente = df[df['ID_Cliente'] == cpf_digitado]
                if not cliente.empty and str(senha_input).strip() == str(cliente.iloc[0]['Senha']).strip():
                    st.session_state.logado = True
                    st.session_state.dados_usuario = cliente.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Dados incorretos.")
            except Exception as e: st.error(f"Erro: {e}")
    else:
        u = st.session_state.dados_usuario
        pts_t = float(u.get('Pontos_Totais', 0))
        saldo = float(u.get('Saldo_Atual', pts_t))
        res = calcular_status_confraria(pts_t)
        
        st.title(f"OLÁ, {str(u['Nome_Completo']).split()[0].upper()}! 🍻")
        
        col1, col2 = st.columns(2)
        col1.metric("PONTOS TOTAIS", f"{int(pts_t)} PTS")
        col2.metric("SALDO LOJA", f"{int(saldo)} PTS")

        st.markdown(f"<div style='background-color: #161b3d; padding: 20px; border-radius: 15px; border-left: 8px solid {res['cor']};'><h3>STATUS: {res['nivel'].upper()}</h3><p>{res['desc']}</p></div>", unsafe_allow_html=True)
        st.write("")
        st.progress(min(pts_t / res['proximo_pts'], 1.0) if res['proximo_pts'] > 0 else 1.0)

# ==========================================
# ABA 2: LOJA DE SOUVENIRS
# ==========================================
elif aba == "Loja de Souvenirs":
    st.title("🛍️ Loja de Souvenirs")
    if not st.session_state.logado:
        st.warning("Faça login para ver seu saldo!")
    else:
        u = st.session_state.dados_usuario
        saldo = float(u.get('Saldo_Atual', u.get('Pontos_Totais', 0)))
        st.subheader(f"Saldo Disponível: {int(saldo)} Goles")
        
        produtos = [
            {"nome": "1 Pint (500ml)", "pts": 150, "icon": "🍺"},
            {"nome": "Growler Pet 1L", "pts": 250, "icon": "🧴"},
            {"nome": "Boné Culundria", "pts": 800, "icon": "🧢"},
            {"nome": "Camiseta Confraria", "pts": 1200, "icon": "👕"}
        ]
        
        cols = st.columns(2)
        for i, p in enumerate(produtos):
            with cols[i % 2]:
                st.markdown(f"<div style='background-color: #161b3d; padding: 15px; border-radius: 10px; border: 1px solid #e68a00;'><h4>{p['icon']} {p['nome']}</h4><p>{p['pts']} Goles</p></div>", unsafe_allow_html=True)
                if saldo >= p['pts']:
                    if st.button(f"Resgatar {p['nome']}", key=f"btn_{i}"):
                        try:
                            client.open(NOME_PLANILHA).worksheet("INDICAÇÕES").append_row([u['ID_Cliente'], f"RESGATE: {p['nome']}", p['pts'], "Pendente"])
                            st.success("Pedido enviado!")
                            st.balloons()
                        except: st.error("Erro no resgate.")
                else: st.button("Saldo Insuficiente", key=f"btn_{i}", disabled=True)

# ==========================================
# ABA 3: CADASTRO
# ==========================================
elif aba == "Fazer Parte da Confraria":
    st.title("🧪 Cadastro")
    with st.form("cad"):
        nome = st.text_input("Nome")
        cpf_c = st.text_input("CPF")
        sen_c = st.text_input("Senha", type="password")
        if st.form_submit_button("CADASTRAR"):
            if nome and cpf_c:
                try:
                    sh = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                    sh.append_row([str(cpf_c).strip().zfill(11), nome.upper(), "", "", "Explorador", 0, 0, pd.Timestamp.now().strftime("%d/%m/%Y"), sen_c])
                    st.success("Cadastrado! Faça login.")
                except Exception as e: st.error(f"Erro: {e}")

# ==========================================
# ABA 4: ÁREA DO MESTRE
# ==========================================
# ==========================================
# ABA 4: ÁREA DO MESTRE (VERSÃO ANTI-ERRO)
# ==========================================
elif aba == "Área do Mestre":
    st.title("🏰 Área do Mestre")
    pwd = st.text_input("Senha:", type="password", key="m_pwd")
    if pwd == st.secrets["admin_password"]:
        try:
            # Lendo a aba VENDAS com proteção contra vazios
            sh_v = client.open(NOME_PLANILHA).worksheet("VENDAS")
            data_v = sh_v.get_all_values()
            df_v = pd.DataFrame(data_v[1:], columns=data_v[0])
            df_v = df_v.loc[:, df_v.columns != ''] # Mata colunas fantasmas
            
            # Converte litragem para número
            df_v['Litragem_Total'] = pd.to_numeric(df_v['Litragem_Total'], errors='coerce').fillna(0)
            
            st.metric("Litragem Total", f"{df_v['Litragem_Total'].sum():.1f} L")
            
            if 'Estilo Chopp' in df_v.columns:
                st.subheader("🍺 Estilos mais pedidos")
                vendas_estilo = df_v.groupby('Estilo Chopp')['Litragem_Total'].sum()
                st.bar_chart(vendas_estilo)
                
        except Exception as e: 
            st.error(f"Erro ao processar a planilha: {e}")
