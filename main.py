import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Culundria Confraria", page_icon="🍺", layout="centered")

# --- ESTILO CSS (Isolado para não bugar o editor) ---
estilo_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
    [data-testid="stAppViewContainer"] { background-color: #0b0e27; color: #ffffff; font-family: 'Montserrat', sans-serif; }
    [data-testid="stSidebar"] { background-color: #050714; }
    .stMetric { background-color: #161b3d; padding: 1.5rem; border-radius: 10px; border: 1px solid #e68a00; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #e68a00; color: white; font-weight: bold; border: none; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #e68a00, #ffcc33); }
    .stTable { background-color: #161b3d; border-radius: 10px; color: white; }
</style>
"""
st.markdown(estilo_css, unsafe_allow_html=True)

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

# --- FUNÇÃO DE NÍVEIS ---
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

# --- 3. LÓGICA DE NAVEGAÇÃO ---
opcoes_menu = ["Meu Painel (Login)", "Fazer Parte da Confraria", "Área do Mestre"]

if "aba_selecionada" not in st.session_state:
    st.session_state.aba_selecionada = "Meu Painel (Login)"
if "logado" not in st.session_state:
    st.session_state.logado = False

aba = st.sidebar.radio("Navegação:", opcoes_menu, index=opcoes_menu.index(st.session_state.aba_selecionada))
st.session_state.aba_selecionada = aba

# ==========================================
# ABA 1: LOGIN E PAINEL DO CLIENTE
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
            except Exception as e: st.error(f"Erro: {e}")
    else:
        c = st.session_state.dados_usuario
        pts = float(c.get('Pontos_Totais', 0))
        res = calcular_status_confraria(pts)
        st.title(f"OLÁ, {c['Nome_Completo'].split()[0].upper()}! 🍻")
        
        # Card de Status (Variável isolada para evitar azul no editor)
       Criando o HTML linha por linha (O editor nunca fica azul assim)
card = "<div style='background-color: #161b3d; padding: 25px; border-radius: 15px; border-left: 8px solid " + resumo['cor'] + ";'>"
card += "<h2 style='margin:0; color: " + resumo['cor'] + "; font-size: 1.2em;'>STATUS: " + resumo['nivel'].upper() + "</h2>"
card += "<p style='color: #ffffff; font-size: 1.1em; margin-top: 10px;'>\"" + resumo['desc'] + "\"</p>"
card += "<hr style='border: 0.1px solid #333;'>"
card += "<p style='color: #aaa; font-size: 0.85em; font-style: italic;'>" + resumo['msg'] + "</p>"
card += "</div>"

st.markdown(card, unsafe_allow_html=True)
        
        progresso = min(pts / res['proximo_pts'], 1.0) if res['proximo_pts'] > 0 else 1.0
        st.write("")
        st.progress(progresso)
        st.metric("MEUS GOLES ACUMULADOS", f"{int(pts)} PTS")

# ==========================================
# ABA 2: CADASTRO
# ==========================================
elif aba == "Fazer Parte da Confraria":
    st.title("🧪 Entre para a Confraria")
    with st.form("form_cadastro"):
        nome = st.text_input("Nome Completo")
        cpf_n = st.text_input("CPF (apenas números)")
        passw = st.text_input("Crie uma Senha", type="password")
        if st.form_submit_button("CRIAR MINHA CONTA"):
            if nome and cpf_n and passw:
                try:
                    sheet_cli = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                    nova_linha = [str(cpf_n).strip().zfill(11), nome.strip().upper(), "", "", "Explorador", 0, 0, pd.Timestamp.now().strftime("%d/%m/%Y"), str(passw).strip()]
                    sheet_cli.append_row(nova_linha)
                    st.success("Cadastro realizado!")
                    st.balloons()
                except Exception as e: st.error(f"Erro: {e}")

# ==========================================
# ABA 3: ÁREA DO MESTRE (ADMIN)
# ==========================================
elif aba == "Área do Mestre":
    st.title("🏰 Área do Mestre")
    senha_adm = st.text_input("Senha Admin:", type="password", key="adm_pwd")
    if senha_adm == st.secrets["admin_password"]:
        try:
            df_v = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("VENDAS").get_all_records())
            df_c = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("CLIENTES").get_all_records())
            
            # Limpeza e conversão blindada
            df_v['Litragem_Total'] = pd.to_numeric(df_v['Litragem_Total'], errors='coerce').fillna(0)
            df_c['Pontos_Totais'] = pd.to_numeric(df_c['Pontos_Totais'], errors='coerce').fillna(0)
            
            st.subheader("📊 Resumo da Brassagem")
            c1, c2 = st.columns(2)
            c1.metric("Litragem Total", f"{df_v['Litragem_Total'].sum():.1f} L")
            c2.metric("Confrades", len(df_c))
            
            st.write("---")
            if 'Estilo Chopp' in df_v.columns:
                st.subheader("🍺 Estilos mais pedidos")
                vendas_estilo = df_v.groupby('Estilo Chopp')['Litragem_Total'].sum()
                st.bar_chart(vendas_estilo)
        except Exception as e: st.error(f"Erro nos dados: {e}")
