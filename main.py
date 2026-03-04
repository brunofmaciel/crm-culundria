import streamlit as st
import gspread
import random  # <--- ADICIONE ESTE
import string  # <--- ADICIONE ESTE
import pandas as pd
import urllib.parse
from google.oauth2.service_account import Credentials

# --- FUNÇÃO PARA GERAR CÓDIGO ÚNICO ---
def gerar_codigo():
    return 'V-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

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
        st.warning("Faça login para acessar a loja!")
    else:
        import urllib.parse  # Garante que o link do QR Code seja gerado corretamente
        
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
                    if st.button(f"Resgatar {p['nome']}", key=f"btn_loja_{i}"):
                        voucher = gerar_codigo()
                        try:
                            # 1. Tenta salvar na aba RESGATES
                            aba_r = client.open(NOME_PLANILHA).worksheet("RESGATES")
                            aba_r.append_row([
                                voucher, 
                                c['ID_Cliente'], 
                                p['nome'], 
                                p['pontos'], 
                                pd.Timestamp.now().strftime("%d/%m/%Y"), 
                                "Pendente"
                            ])
                            
                            # 2. Gera o Link e o QR Code
                            # ATENÇÃO: Substitua o link abaixo pelo link real do seu app no Streamlit
                            url_app = "https://crm-culundria.streamlit.app/" 
                            link_resgate = f"{url_app}?voucher={voucher}"
                            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(link_resgate)}"
                            
                            # 3. Mostra o comprovante visual com QR Code
                            st.success("Resgate realizado com sucesso!")
                            
                            st.markdown(f"""
                                <div style='text-align: center; background-color: #ffffff; padding: 20px; border-radius: 15px; border: 5px solid #e68a00;'>
                                    <p style='color: #0b0e27; font-weight: bold; margin-bottom: 10px;'>APRESENTE NO BALCÃO</p>
                                    <img src='{qr_url}' style='width: 180px; margin-bottom: 10px;'>
                                    <h1 style='color: #0b0e27; margin: 0; font-size: 2.5em;'>{voucher}</h1>
                                    <p style='color: #444; margin: 0;'>{p['nome']}</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            st.balloons()
                        except Exception as e:
                            st.error(f"Erro ao registrar resgate: {e}")
                else:
                    st.button("Saldo Insuficiente", key=f"btn_loja_{i}", disabled=True)
# ==========================================
# ABA: CADASTRO (COMPLETO)
# ==========================================
elif aba == "Fazer Parte da Confraria":
    st.title("🧪 Entre para a Confraria")
    st.write("Preencha seus dados para começar a acumular goles e conquistar prêmios.")
    
    with st.form("form_cadastro_culundria", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        cpf_cad = st.text_input("CPF (apenas números, 11 dígitos)")
        whats = st.text_input("WhatsApp (com DDD)")
        email = st.text_input("E-mail")
        senha_cad = st.text_input("Crie uma Senha", type="password")
        
        # Botão de submissão
        enviar = st.form_submit_button("CRIAR MINHA CONTA")
        
        if enviar:
            # Limpeza básica do CPF
            cpf_limpo = "".join(filter(str.isdigit, str(cpf_cad))).strip().zfill(11)
            
            if nome and len(cpf_limpo) == 11 and senha_cad:
                try:
                    sh_c = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                    
                    # Ordem das colunas: CPF, Nome, Whats, Email, Nível, Pontos Totais, Saldo Atual, Data, Senha
                    nova_linha = [
                        cpf_limpo, 
                        nome.strip().upper(), 
                        whats.strip(), 
                        email.strip().lower(), 
                        "Explorador", 
                        100, # Pontos iniciais de boas-vindas
                        100, # Saldo inicial disponível
                        pd.Timestamp.now().strftime("%d/%m/%Y"), 
                        str(senha_cad).strip()
                    ]
                    
                    sh_c.append_row(nova_linha)
                    st.success("✅ Cadastro realizado com sucesso! Vá até 'Meu Painel' para entrar.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar no banco de dados: {e}")
            else:
                st.warning("⚠️ Por favor, preencha Nome, CPF válido e Senha.")

# ==========================================
# ABA 4: AREA DO MESTRE#
# ==========================================
elif aba == "Área do Mestre":
    st.title("🏰 Gestão Culundria")
    
    # 1. Autenticação Única
    senha_adm = st.text_input("Chave do Grimório:", type="password", key="mestre_unica_pwd")
    
    if senha_adm == st.secrets["admin_password"]:
        st.success("Acesso autorizado, Mestre!")
        
        # 2. Criação das Abas ANTES de usá-las
        tab_balcao, tab_relatorios, tab_ranking = st.tabs(["🎫 Validar Voucher", "📊 Relatórios", "🏆 Ranking"])
        
        try:
            # 3. Carregamento de Dados (Geral para todas as abas)
            sh_v = client.open(NOME_PLANILHA).worksheet("VENDAS")
            df_v = pd.DataFrame(sh_v.get_all_records())
            
            sh_c = client.open(NOME_PLANILHA).worksheet("CLIENTES")
            df_c = pd.DataFrame(sh_c.get_all_records())
            
            # Limpeza e Conversão
            df_v['Litragem_Total'] = pd.to_numeric(df_v['Litragem_Total'], errors='coerce').fillna(0)
            df_c['Pontos_Totais'] = pd.to_numeric(df_c['Pontos_Totais'], errors='coerce').fillna(0)
            df_c['Saldo_Atual'] = pd.to_numeric(df_c['Saldo_Atual'], errors='coerce').fillna(0)

            # --- ABA 1: VALIDAÇÃO DE VOUCHER (Otimizada para QR Code) ---
            with tab_balcao:
                st.subheader("🏁 Validação de Resgate")
                
                # Captura automática do link do QR Code
                params = st.query_params
                voucher_url = params.get("voucher", "")
                
                cod_v = st.text_input(
                    "Código do Voucher:", 
                    value=voucher_url, 
                    placeholder="Ex: V-A1B2",
                    key="input_voucher_mestre"
                ).upper().strip()
                
                if st.button("VERIFICAR E DAR BAIXA", key="btn_baixa_voucher"):
                    if cod_v:
                        sh_r = client.open(NOME_PLANILHA).worksheet("RESGATES")
                        data_r = sh_r.get_all_values()
                        df_r = pd.DataFrame(data_r[1:], columns=data_r[0])
                        
                        v_linha = df_r[df_r['Cód_Voucher'] == cod_v]
                        
                        if not v_linha.empty:
                            idx = v_linha.index[0] + 2
                            if v_linha.iloc[0]['Status'] == "Pendente":
                                sh_r.update_cell(idx, 6, "Entregue")
                                st.success(f"✅ VOUCHER VÁLIDO! Entregar: **{v_linha.iloc[0]['Produto']}**")
                                st.balloons()
                                st.query_params.clear() # Limpa a URL após sucesso
                            else:
                                st.error("❌ Este voucher já foi utilizado anteriormente!")
                        else:
                            st.error("❓ Código não encontrado ou inválido.")
                    else:
                        st.warning("Insira um código de voucher.")

            # --- ABA 2: RELATÓRIOS ---
            with tab_relatorios:
                st.subheader("📊 Resumo da Brassagem")
                c1, c2, c3 = st.columns(3)
                c1.metric("Litragem Total", f"{df_v['Litragem_Total'].sum():.1f} L")
                c2.metric("Confrades", len(df_c))
                c3.metric("Pontos p/ Troca", int(df_c['Saldo_Atual'].sum()))
                
                if 'Estilo Chopp' in df_v.columns:
                    st.write("---")
                    st.subheader("🍺 Estilos mais pedidos")
                    st.bar_chart(df_v.groupby('Estilo Chopp')['Litragem_Total'].sum())

            # --- ABA 3: RANKING ---
            with tab_ranking:
                st.subheader("🏆 Top Confrades")
                top_10 = df_c.nlargest(10, 'Pontos_Totais')[['Nome_Completo', 'Pontos_Totais']]
                st.table(top_10)
                
        except Exception as e:
            st.error(f"Erro ao carregar o Grimório: {e}")
            
    elif senha_adm != "":
        st.error("Chave incorreta, Confrade.")
