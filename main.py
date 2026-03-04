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

# Mantenha os nomes IGUAIS aos que usará nos ELIFs abaixo
opcoes_menu = ["Meu Painel", "Loja de Souvenirs", "Fazer Parte da Confraria", "Área do Mestre"]

with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>Culundria</h2>", unsafe_allow_html=True)
    # Criamos o menu
    aba = st.radio("Navegação:", opcoes_menu)
    
    if st.session_state.logado:
        st.write(f"Logado como: {st.session_state.dados_usuario['Nome_Completo'].split()[0]}")
        if st.button("SAIR DA CONFRARIA"):
            st.session_state.logado = False
            st.session_state.dados_usuario = None
            st.rerun()

# ==========================================
# ABA 1: MEU PAINEL (LOGIN E STATUS)
# ==========================================
if aba == "Meu Painel": # <--- Nome batendo exatamente com a lista opcoes_menu
    if not st.session_state.logado:
        st.title("🍺 Acesso à Confraria")
        
        # 1. Definimos as variáveis ANTES do form para evitar NameError
        with st.container():
            cpf_login = st.text_input("Digite seu CPF (apenas números)", key="cpf_input_login")
            senha_login = st.text_input("Sua Senha", type="password", key="senha_input_login")
            
            if st.button("ENTRAR NA CONFRARIA"):
                # --- LÓGICA DE LOGIN ---
                try:
                    sh_c = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                    dados = sh_c.get_all_records()
                    df_c = pd.DataFrame(dados)

                except Exception as e: # <--- ADICIONE ESTAS DUAS LINHAS AQUI
                            st.error(f"Erro ao acessar banco de dados: {e}")
                    
        # --- RECUPERAÇÃO DE SENHA (FORA DO FORMULÁRIO) ---
        st.write("---")
        if st.button("Esqueci minha senha"):
            # O truque: verificamos se o usuário digitou algo no campo acima
            if cpf_login and len(cpf_login) >= 11:
                import urllib.parse
                seu_numero = "5535998732583" # <--- SEU WHATSAPP AQUI
                msg = f"Olá Mestre! Esqueci minha senha da Confraria. Meu CPF é: {cpf_login}"
                link_zap = f"https://wa.me/{seu_numero}?text={urllib.parse.quote(msg)}"
                
                st.info("Clique no botão abaixo para falar com o Mestre:")
                st.link_button("📩 SOLICITAR SENHA VIA WHATSAPP", link_zap)
            else:
                st.warning("⚠️ Digite seu CPF no campo de login acima primeiro para que eu possa te identificar.")
# ==========================================
# ABA 2: LOJA DE SOUVENIRS
# ==========================================
elif aba == "Loja de Souvenirs":
    st.title("🛍️ Loja de Souvenirs")
    
    if not st.session_state.logado:
        st.warning("Faça login no 'Meu Painel' para acessar a loja!")
    else:
        import urllib.parse
        c = st.session_state.dados_usuario
        cpf_logado = str(c['ID_Cliente'])
        
        # 1. SINCRONIZAÇÃO DE SALDO REAL (SEGURANÇA)
        try:
            sh = client.open(NOME_PLANILHA)
            aba_c = sh.worksheet("CLIENTES")
            celula_usuario = aba_c.find(cpf_logado)
            # Buscando Saldo Atual na Coluna K (11)
            saldo_real = float(aba_c.cell(celula_usuario.row, 11).value)
            st.subheader(f"Seu Saldo: {int(saldo_real)} Goles")
        except Exception as e:
            st.error(f"Erro ao sincronizar saldo: {e}")
            st.stop()

        # 2. DEFINIÇÃO DOS PRODUTOS COM IMAGENS E DESCRIÇÃO
        elif aba == "Loja de Souvenirs":
    st.title("🛍️ Loja de Souvenirs")
    
    if not st.session_state.logado:
        st.warning("Faça login no 'Meu Painel' para acessar a loja!")
    else:
        # 1. BUSCA PRODUTOS DA PLANILHA EM TEMPO REAL
        try:
            sh = client.open(NOME_PLANILHA)
            # Carrega a aba PRODUTOS
            aba_p = sh.worksheet("PRODUTOS")
            df_p = pd.DataFrame(aba_p.get_all_records())
            
            # Filtra apenas os que estão marcados como ATIVO = SIM
            produtos = df_p[df_p['Ativo'] == "SIM"].to_dict('records')
        except Exception as e:
            st.error(f"Erro ao carregar catálogo: {e}")
            st.stop()

        # 2. SINCRONIZAÇÃO DE SALDO (Mesma lógica de segurança anterior)
        try:
            aba_c = sh.worksheet("CLIENTES")
            c = st.session_state.dados_usuario
            celula_usuario = aba_c.find(str(c['ID_Cliente']))
            saldo_real = float(aba_c.cell(celula_usuario.row, 11).value) # Coluna K
            st.subheader(f"Seu Saldo: {int(saldo_real)} Goles")
        except:
            st.error("Erro ao sincronizar saldo.")
            st.stop()

        # 3. EXIBIÇÃO EM GRID (Agora vindo do Banco de Dados)
        cols = st.columns(2)
        for i, p in enumerate(produtos):
            with cols[i % 2]:
                st.markdown(f"""
                    <div style='background-color: #161b3d; padding: 15px; border-radius: 10px 10px 0 0; border: 1px solid #e68a00; border-bottom: none; text-align: center;'>
                        <h3 style='margin:0; color: #e68a00;'>{p['Emoji']} {p['Nome']}</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                # Exibe imagem da planilha ou aviso se estiver vazio
                if p['URL_Imagem']:
                    st.image(p['URL_Imagem'], use_container_width=True)
                else:
                    st.info("Foto em breve!")

                st.markdown(f"""
                    <div style='background-color: #161b3d; padding: 10px; border-radius: 0 0 10px 10px; border: 1px solid #e68a00; border-top: none; margin-bottom: 20px; text-align: center;'>
                        <p style='color: #ffffff; font-size: 1.2em; font-weight: bold;'>{p['Pontos']} GOLES</p>
                    </div>
                """, unsafe_allow_html=True)
                                
                # 4. LÓGICA DE RESGATE COM DÉBITO REAL
                if saldo_real >= p['pontos']:
                    if st.button(f"RESGATAR {p['nome'].upper()}", key=f"btn_resgate_{i}"):
                        with st.spinner("Processando resgate..."):
                            try:
                                # A. Gera Voucher e calcula novo saldo
                                voucher = gerar_codigo()
                                novo_saldo = saldo_real - p['pontos']
                                
                                # B. GRAVAÇÃO NA PLANILHA (DÉBITO IMEDIATO)
                                # Atualiza saldo na Coluna K (11)
                                aba_c.update_cell(celula_usuario.row, 11, novo_saldo)
                                
                                # Registra na aba RESGATES
                                aba_r = sh.worksheet("RESGATES")
                                aba_r.append_row([
                                    voucher, 
                                    cpf_logado, 
                                    p['nome'], 
                                    p['pontos'], 
                                    pd.Timestamp.now().strftime("%d/%m/%Y"), 
                                    "Pendente"
                                ])
                                
                                # C. GERAÇÃO DO QR CODE
                                # Troque pelo link do seu app real
                                url_app = "https://crm-culundria.streamlit.app/" 
                                link_resgate = f"{url_app}?voucher={voucher}"
                                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(link_resgate)}"
                                
                                st.success(f"Resgate confirmado! -{p['pontos']} Goles.")
                                st.markdown(f"""
                                    <div style='text-align: center; background-color: #ffffff; padding: 20px; border-radius: 15px; border: 5px solid #e68a00;'>
                                        <p style='color: #0b0e27; font-weight: bold; margin-bottom: 10px;'>APRESENTE NO BALCÃO:</p>
                                        <img src='{qr_url}' style='width: 180px; margin-bottom: 10px;'>
                                        <h1 style='color: #0b0e27; margin: 0; font-size: 2.5em;'>{voucher}</h1>
                                        <p style='color: #444; margin: 0;'>{p['nome']}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                                st.balloons()
                                
                                # Força a atualização do saldo exibido na próxima interação
                                st.session_state.dados_usuario['Saldo_Atual'] = novo_saldo
                                
                            except Exception as e:
                                st.error(f"Erro na transação: {e}")
                else:
                    st.button("Saldo Insuficiente", key=f"btn_disabled_{i}", disabled=True)
                    
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
