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

# --- 3. LÓGICA DE NAVEGAÇÃO ---
opcoes_menu = ["Meu Painel (Login)", "Fazer Parte da Confraria", "Área do Mestre"]

if "aba_selecionada" not in st.session_state or st.session_state.aba_selecionada not in opcoes_menu:
    st.session_state.aba_selecionada = "Meu Painel (Login)"
if "logado" not in st.session_state:
    st.session_state.logado = False

indice_atual = opcoes_menu.index(st.session_state.aba_selecionada)

with st.sidebar:
    try: st.image("logoculundria.png", use_container_width=True)
    except: st.warning("Logo não encontrada.")
    st.markdown("<h2 style='text-align: center;'>Culundria</h2>", unsafe_allow_html=True)
    aba = st.sidebar.radio("Navegação:", opcoes_menu, index=indice_atual)
    st.session_state.aba_selecionada = aba
    if st.session_state.logado:
        if st.sidebar.button("SAIR DA CONFRARIA"):
            st.session_state.logado = False
            st.session_state.dados_usuario = None
            st.rerun()

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
                # 1. Abre a planilha e lê os dados
                sheet = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                df = pd.DataFrame(sheet.get_all_records())
                
                # --- AQUI É ONDE A MÁGICA DO ZERO ACONTECE ---
                # Transformamos em texto, tiramos o .0, limpamos espaços e forçamos 11 dígitos (.zfill)
                df['ID_Cliente'] = df['ID_Cliente'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(11)
                
                # Limpamos o CPF que o cliente digitou e também forçamos 11 dígitos
                cpf_digitado = "".join(filter(str.isdigit, str(cpf_input))).strip().zfill(11)
                
                # Fazemos a busca comparando "077..." com "077..."
                cliente = df[df['ID_Cliente'] == cpf_digitado]
                # ----------------------------------------------

                if not cliente.empty:
                    c = cliente.iloc[0]
                    # Confere a senha
                    if str(senha_input).strip() == str(c['Senha']).strip():
                        st.session_state.logado = True
                        st.session_state.dados_usuario = c.to_dict()
                        st.rerun()
                    else:
                        st.error("Senha incorreta!")
                else:
                    st.warning(f"CPF {cpf_digitado} não localizado.")
                    # MODO DEBUG (SÓ PARA O MESTRE VER O QUE ESTÁ NA PLANILHA):
                    with st.expander("Verificar CPFs na base (Ajuda do Mestre)"):
                        st.write("CPFs que o sistema está lendo da sua planilha:")
                        st.write(df['ID_Cliente'].tolist())

            except Exception as e:
                st.error(f"Erro técnico na busca: {e}")
        
        st.write("")
        if st.button("✨ Não tem conta? Cadastre-se aqui"):
            st.session_state.aba_selecionada = "Fazer Parte da Confraria"
            st.rerun()
    else:
        # PAINEL DO CONFRADE LOGADO
        c = st.session_state.dados_usuario
        pontos = float(c.get('Pontos_Totais', 0))
        resumo = calcular_status_confraria(pontos)
      
        st.title(f"OLÁ, {c['Nome_Completo'].split()[0].upper()}! 🍻")
        
        # 2. Definimos o texto do card (ASPAS TRIPLAS LIMPAS)
        html_card = f"""
            <div style='background-color: #161b3d; padding: 25px; border-radius: 15px; border-left: 8px solid {resumo['cor']};'>
                <h2 style='margin:0; color: {resumo['cor']}; font-size: 1.2em;'>STATUS: {resumo['nivel'].upper()}</h2>
                <p style='color: #ffffff; font-size: 1.1em; margin-top: 10px;'>"{resumo['desc']}"</p>
                <hr style='border: 0.1px solid #333;'>
                <p style='color: #aaa; font-size: 0.85em; font-style: italic;'>{resumo['msg']}</p>
            </div>
        ""
        
        st.markdown(html_card, unsafe_allow_html=True)

        # BARRA DE PROGRESSO (RESTAURADA)
        # Cálculo: pontos_atuais / pontos_objetivo
        progresso_val = min(pontos / resumo['proximo_pts'], 1.0) if resumo['proximo_pts'] > 0 else 1.0
        st.write("")
        st.progress(progresso_val)
        st.caption(f"Você já acumulou **{int(pontos)}** de **{int(resumo['proximo_pts'])}** pontos para o próximo nível.")

        st.metric("MEUS GOLES ACUMULADOS", f"{int(pontos)} PTS")

        # Histórico de Pedidos
        st.markdown("### 📜 MEU HISTÓRICO")
        try:
            sheet_v = client.open(NOME_PLANILHA).worksheet("VENDAS")
            df_v = pd.DataFrame(sheet_v.get_all_records())
            df_v['ID_Cliente'] = df_v['ID_Cliente'].astype(str)
            minhas_v = df_v[df_v['ID_Cliente'] == str(c['ID_Cliente'])]
            if not minhas_v.empty:
                st.table(minhas_v[['Data_Venda', 'Litragem_Total', 'Total Pontos']])
            else: st.info("Nenhum barril registrado ainda.")
        except: st.info("Buscando barris no histórico...")

        # Formulário de Indicação
        st.markdown("---")
        st.write("### 🚀 INDIQUE UM CONFRADE")
        with st.form("form_indicacao", clear_on_submit=True):
            n_amigo = st.text_input("Nome do Amigo")
            t_amigo = st.text_input("WhatsApp")
            if st.form_submit_button("ENVIAR INDICAÇÃO"):
                if n_amigo and t_amigo:
                    client.open(NOME_PLANILHA).worksheet("INDICAÇÕES").append_row([c['ID_Cliente'], n_amigo, t_amigo, "Pendente"])
                    st.success("Indicação enviada com sucesso!")

# ==========================================
# ABA 2: CADASTRO
# ==========================================
elif aba == "Fazer Parte da Confraria":
    st.title("🧪 Entre para a Confraria")
    st.write("Crie sua conta e comece a pontuar na Culundria!")
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
                    df_check = pd.DataFrame(sheet_cli.get_all_records())
                    if str(cpf_n).strip() in df_check['ID_Cliente'].astype(str).values:
                        st.warning("CPF já cadastrado!")
                    else:
                        data_h = pd.Timestamp.now().strftime("%d/%m/%Y")
                        # Colunas: A=CPF, B=Nome, C=Whats, D=Mail, E=Status, F=Pts, G=Prog, H=Data, I=Senha
                        nova_linha = [str(cpf_n).strip(), nome.strip().upper(), whats, mail, "Explorador", 0, 0, data_h, str(passw).strip()]
                        sheet_cli.append_row(nova_linha)
                        st.success("Bem-vindo! Agora faça login no 'Meu Painel'.")
                        st.balloons()
                except Exception as e: st.error(f"Erro ao salvar: {e}")
            else: st.error("Preencha Nome, CPF e Senha.")

# ==========================================
# ABA 3: ÁREA DO MESTRE (ADMIN)
# ==========================================
elif aba == "Área do Mestre":
    st.title("🏰 Área do Mestre")
    senha_adm = st.sidebar.text_input("Senha Admin:", type="password")
    if senha_adm == st.secrets["admin_password"]:
        st.success("Grimório de dados aberto!")
        try:
            df_vendas = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("VENDAS").get_all_records())
            df_clientes = pd.DataFrame(client.open(NOME_PLANILHA).worksheet("CLIENTES").get_all_records())
            
            # Limpeza de colunas (Importante!)
            df_vendas.columns = df_vendas.columns.str.strip()
            df_clientes.columns = df_clientes.columns.str.strip()
            
            st.subheader("📊 Resumo da Brassagem")
            c1, c2, c3 = st.columns(3)
            litragem = pd.to_numeric(df_vendas['Litragem_Total'], errors='coerce').sum()
            c1.metric("Litragem Total", f"{litragem:.1f} L")
            c2.metric("Confrades", len(df_clientes))
            c3.metric("Pontos Totais", int(pd.to_numeric(df_clientes['Pontos_Totais'], errors='coerce').sum()))
            
            col_chart, col_top = st.columns([2, 1])
            with col_chart:
                st.subheader("🍺 Estilos mais pedidos")
                if 'Estilo Chopp' in df_vendas.columns:
                    vendas_estilo = df_vendas.groupby('Estilo Chopp')['Litragem_Total'].sum()
                    st.bar_chart(vendas_estilo)
            
            with col_top:
                st.subheader("🏆 Top Confrades")
                top_5 = df_clientes.nlargest(5, 'Pontos_Totais')[['Nome_Completo', 'Pontos_Totais']]
                st.table(top_5)
                
        except Exception as e: st.error(f"Erro ao carregar gráficos: {e}")
    elif senha_adm: st.error("Senha incorreta.")
