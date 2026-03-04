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

# --- 3. LÓGICA DE NAVEGAÇÃO ATUALIZADA ---
opcoes_menu = ["Meu Painel (Login)", "Loja de Souvenirs", "Fazer Parte da Confraria", "Área do Mestre"]

if "aba_selecionada" not in st.session_state:
    st.session_state.aba_selecionada = "Meu Painel (Login)"

aba = st.sidebar.radio("Navegação:", opcoes_menu, index=opcoes_menu.index(st.session_state.aba_selecionada))
st.session_state.aba_selecionada = aba

# ==========================================
# ABA 1: LOGIN E PAINEL (COM SALDO)
# ==========================================
if aba == "Meu Painel (Login)":
    if not st.session_state.logado:
        st.title("🍺 Goles de Vantagem")
        # ... [Seu código de login aqui] ...
        # [Mantenha o código de login que já funciona]
    else:
        c = st.session_state.dados_usuario
        # Puxando os dois tipos de pontos da planilha
        pts_acumulados = float(c.get('Pontos_Totais', 0))
        saldo_disponivel = float(c.get('Saldo_Atual', pts_acumulados)) # Se K estiver vazio, usa o total
        
        res = calcular_status_confraria(pts_acumulados)
        st.title("OLÁ, " + str(c['Nome_Completo']).split()[0].upper() + "! 🍻")
        
        # Dashboard de Goles
        col1, col2 = st.columns(2)
        with col1:
            st.metric("PONTOS TOTAIS (NÍVEL)", f"{int(pts_acumulados)} PTS")
        with col2:
            st.metric("SALDO PARA TROCA", f"{int(saldo_disponivel)} PTS", delta="Disponível na Loja")

        # Card de Status
        html_card = "<div style='background-color: #161b3d; padding: 25px; border-radius: 15px; border-left: 8px solid " + res['cor'] + ";'>"
        html_card += "<h2 style='margin:0; color: " + res['cor'] + "; font-size: 1.2em;'>STATUS: " + res['nivel'].upper() + "</h2>"
        html_card += "<p style='color: #ffffff; font-size: 1.1em; margin-top: 10px;'>\"" + res['desc'] + "\"</p></div>"
        st.markdown(html_card, unsafe_allow_html=True)
        
        # Barra de Progresso
        prog = min(pts_acumulados / res['proximo_pts'], 1.0) if res['proximo_pts'] > 0 else 1.0
        st.write("")
        st.progress(prog)
        st.caption("Faltam " + str(int(res['proximo_pts'] - pts_acumulados)) + " pontos para o próximo nível.")

# ==========================================
# ABA: LOJA DE SOUVENIRS (NOVA!)
# ==========================================
elif aba == "Loja de Souvenirs":
    st.title("🛍️ Loja de Souvenirs")
    
    if not st.session_state.logado:
        st.warning("Faça login para acessar a loja e ver seu saldo de goles!")
    else:
        c = st.session_state.dados_usuario
        saldo = float(c.get('Saldo_Atual', c.get('Pontos_Totais', 0)))
        
        st.subheader("Seu Saldo: " + str(int(saldo)) + " Goles")
        st.write("Troque seus goles acumulados por produtos exclusivos. Seus pontos de **Nível** não diminuem!")
        
        # Definição dos produtos da loja
        produtos = [
            {"nome": "1 Pint (500ml)", "pontos": 150, "img": "🍺", "desc": "Um copo cheio na nossa Taproom."},
            {"nome": "Growler Pet 1L (Cheio)", "pontos": 250, "img": "🧴", "desc": "Escolha seu estilo favorito e leve para casa."},
            {"nome": "Boné Culundria", "pontos": 800, "img": "🧢", "desc": "O acessório oficial do mestre cervejeiro."},
            {"nome": "Camiseta Confraria", "pontos": 1200, "img": "👕", "desc": "Vista a camisa da nossa história."}
        ]
        
        # Exibição em Grid
        cols = st.columns(2)
        for i, p in enumerate(produtos):
            with cols[i % 2]:
                container = "<div style='background-color: #161b3d; padding: 20px; border-radius: 10px; border: 1px solid #e68a00; margin-bottom: 10px;'>"
                container += "<h3 style='margin:0; color: #e68a00;'>" + p['img'] + " " + p['nome'] + "</h3>"
                container += "<p style='font-size: 0.9em; color: #aaa;'>" + p['desc'] + "</p>"
                container += "<h4 style='color: #ffffff;'>" + str(p['pontos']) + " GOLES</h4></div>"
                st.markdown(container, unsafe_allow_html=True)
                
                # Botão de Resgate
                if saldo >= p['pontos']:
                    if st.button(f"Resgatar {p['nome']}", key=f"btn_{i}"):
                        # Aqui enviaremos o pedido para a aba INDICAÇÕES ou uma nova aba RESGATES
                        try:
                            aba_resgate = client.open(NOME_PLANILHA).worksheet("INDICAÇÕES")
                            # Registra o resgate: CPF, Produto, Pontos, Status
                            aba_resgate.append_row([c['ID_Cliente'], "RESGATE: " + p['nome'], p['pontos'], "Pendente"])
                            st.success("Solicitação enviada! Retire seu produto no balcão.")
                            st.balloons()
                        except:
                            st.error("Erro ao processar resgate. Fale com o Mestre.")
                else:
                    st.button("Goles Insuficientes", key=f"btn_{i}", disabled=True)

# ... [Mantenha as abas de Cadastro e Área do Mestre abaixo] ...
# ==========================================
# ABA 2: CADASTRO
# ==========================================
elif aba == "Fazer Parte da Confraria":
    st.title("🧪 Entre para a Confraria")
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        cpf_n = st.text_input("CPF (apenas números)")
        whats = st.text_input("WhatsApp")
        mail = st.text_input("E-mail")
        passw = st.text_input("Crie uma Senha", type="password")
        if st.form_submit_button("CRIAR MINHA CONTA"):
            if nome and cpf_n and passw:
                try:
                    sheet_cli = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                    nova_linha = [str(cpf_n).strip().zfill(11), nome.strip().upper(), whats, mail, "Explorador", 0, 0, pd.Timestamp.now().strftime("%d/%m/%Y"), str(passw).strip()]
                    sheet_cli.append_row(nova_linha)
                    st.success("Bem-vindo! Agora faça login no 'Meu Painel'.")
                    st.balloons()
                except Exception as e: st.error(f"Erro ao salvar: {e}")
            else: st.error("Preencha Nome, CPF e Senha.")

# ==========================================
# ABA 3: ÁREA DO MESTRE (ADMIN) - VERSÃO BLINDADA
# ==========================================
elif aba == "Área do Mestre":
    st.title("🏰 Área do Mestre")
    
    senha_adm = st.text_input("Chave do Grimório (Senha):", type="password", key="senha_admin_mestre")
    
    if senha_adm == st.secrets["admin_password"]:
        st.success("Grimório de dados aberto!")
        try:
            # 1. Carrega os dados
            df_vendas = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("VENDAS").get_all_records())
            df_clientes = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("CLIENTES").get_all_records())
            
            # 2. Limpeza de colunas e Conversão de Tipos (AQUI ESTÁ A SOLUÇÃO)
            df_vendas.columns = df_vendas.columns.str.strip()
            
            # Forçamos a conversão para número. O que não for número vira 0.
            df_vendas['Litragem_Total'] = pd.to_numeric(df_vendas['Litragem_Total'], errors='coerce').fillna(0)
            df_clientes['Pontos_Totais'] = pd.to_numeric(df_clientes['Pontos_Totais'], errors='coerce').fillna(0)
            
            st.subheader("📊 Resumo da Brassagem")
            c1, c2, c3 = st.columns(3)
            
            litragem_acumulada = df_vendas['Litragem_Total'].sum()
            c1.metric("Litragem Total", f"{litragem_acumulada:.1f} L")
            c2.metric("Confrades", len(df_clientes))
            c3.metric("Pontos Totais", int(df_clientes['Pontos_Totais'].sum()))
            
            # 3. Gráficos e Tabelas
            col_chart, col_top = st.columns([2, 1])
            
            with col_chart:
                st.subheader("🍺 Estilos mais pedidos")
                if 'Estilo Chopp' in df_vendas.columns:
                    # Agrupamos e somamos a litragem limpa
                    vendas_estilo = df_vendas.groupby('Estilo Chopp')['Litragem_Total'].sum()
                    st.bar_chart(vendas_estilo)
                else:
                    st.warning("Coluna 'Estilo Chopp' não encontrada na aba VENDAS.")
            
            with col_top:
                st.subheader("🏆 Top Confrades")
                top_5 = df_clientes.nlargest(5, 'Pontos_Totais')[['Nome_Completo', 'Pontos_Totais']]
                st.table(top_5)
                
        except Exception as e: 
            st.error(f"Erro ao processar os dados: {e}")
            
    elif senha_adm != "":
        st.error("A chave está incorreta, Confrade.")
