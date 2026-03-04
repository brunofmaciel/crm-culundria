import streamlit as st
import gspread
import random
import string
import pandas as pd
import urllib.parse
from google.oauth2.service_account import Credentials

# 1. CONFIGURAÇÃO DA PÁGINA (APENAS UMA VEZ E NO TOPO!)
st.set_page_config(page_title="Culundria Confraria", page_icon="🍺", layout="centered")

# 2. CAPTURA DO VOUCHER (Agora o Streamlit já está configurado)
query_params = st.query_params
voucher_detectado = query_params.get("voucher", None)

# --- FUNÇÃO PARA GERAR CÓDIGO ÚNICO ---
def gerar_codigo():
    return 'V-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

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

# --- 3. CONFIGURAÇÃO DE SESSÃO E NAVEGAÇÃO DINÂMICA ---
if "logado" not in st.session_state: st.session_state.logado = False
if "dados_usuario" not in st.session_state: st.session_state.dados_usuario = None

# Captura o voucher da URL se existir
query_params = st.query_params
voucher_detectado = query_params.get("voucher", None)

opcoes_menu = ["Meu Painel", "Loja de Souvenirs", "Fazer Parte da Confraria", "Área do Mestre"]

# Define qual aba abrir primeiro (se houver voucher, pula para Área do Mestre)
if voucher_detectado:
    indice_inicial = 3
else:
    indice_inicial = 0

with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>Culundria</h2>", unsafe_allow_html=True)
    
    # O index=indice_inicial faz a mágica do redirecionamento
    aba = st.radio("Navegação:", opcoes_menu, index=indice_inicial)
    
    if st.session_state.logado:
        st.write(f"Logado como: {st.session_state.dados_usuario['Nome_Completo'].split()[0]}")
        if st.button("SAIR DA CONFRARIA"):
            st.session_state.logado = False
            st.session_state.dados_usuario = None
            st.rerun()

# ==========================================
# ABA 1: MEU PAINEL (LOGIN E STATUS)
# ==========================================
if aba == "Meu Painel":
    if not st.session_state.get('logado', False):
        st.title("🍺 Acesso à Confraria")
        
        with st.form("login_form"):
            cpf_login = st.text_input("Digite seu CPF (apenas números)")
            senha_login = st.text_input("Sua Senha", type="password")
            btn_entrar = st.form_submit_button("ENTRAR NA CONFRARIA")
            
            if btn_entrar:
                try:
                    sh_c = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                    df_c = pd.DataFrame(sh_c.get_all_records())
                    
                    # Filtro garantindo que tudo seja Texto
                    user = df_c[(df_c['ID_Cliente'].astype(str) == str(cpf_login)) & 
                                (df_c['Senha'].astype(str) == str(senha_login))]
                    
                    if not user.empty:
                        # GRAVAÇÃO SEGURA NA SESSÃO
                        st.session_state.logado = True
                        st.session_state.dados_usuario = user.iloc[0].to_dict()
                        st.success("Login realizado! Abrindo seu barril...")
                        st.rerun()
                    else:
                        st.error("CPF ou Senha não encontrados.")
                except Exception as e:
                    st.error(f"Erro de conexão com a planilha: {e}")
    
    else:
        # --- O PAINEL QUE ESTAVA SUMINDO ---
        u = st.session_state.get('dados_usuario')
        
        if u:
            st.title(f"🍻 Painel do Confrade")
            st.subheader(f"Bem-vindo, {u.get('Nome_Completo', 'Amigo').split()[0]}!")
            
            # 1. MÉTRICAS BÁSICAS
            saldo = u.get('Saldo_Atual', 0)
            status = calcular_status_confraria(saldo)
            
            c1, c2 = st.columns(2)
            c1.metric("Saldo de Goles", f"{int(saldo)} 🍺")
            c2.metric("Seu Nível", status['nivel'])
            
            # 2. BARRA DE PROGRESSO
            st.write(f"**Status:** {status['desc']}")
            limite = status['proximo_pts'] if status['proximo_pts'] > 0 else 1
            progresso = min(float(saldo) / limite, 1.0)
            st.progress(progresso)
            st.caption(f"💡 {status['msg']}")
            
            # 3. HISTÓRICO DE BARRIS (BUSCA DIRETA)
            st.write("---")
            st.subheader("🛢️ Histórico de Consumo")
            try:
                sh_v = client.open(NOME_PLANILHA).worksheet("VENDAS")
                df_v = pd.DataFrame(sh_v.get_all_records())
                # Filtra pelo CPF logado
                meu_hist = df_v[df_v['ID_Cliente'].astype(str) == str(u['ID_Cliente'])]
                
                if not meu_hist.empty:
                    # Exibe apenas colunas principais
                    exibir = meu_hist[['Data_Venda', 'Estilo Chopp', 'Litragem_Total', 'Total Pontos']]
                    st.table(exibir.sort_index(ascending=False))
                else:
                    st.info("Você ainda não registrou barris. Peça o seu primeiro!")
            except:
                st.caption("Histórico de barris em atualização...")

            # 4. BOTÃO DE SAIR
            if st.button("🚪 SAIR DA CONFRARIA"):
                st.session_state.logado = False
                st.session_state.dados_usuario = None
                st.rerun()
        else:
            st.warning("Ops! Não encontramos seus dados. Por favor, saia e entre novamente.")
            if st.button("RELOGAR"):
                st.session_state.logado = False
                st.rerun()

# ==========================================
# ABA 2: LOJA DE SOUVENIRS (DINÂMICA)
# ==========================================
elif aba == "Loja de Souvenirs":
    st.title("🛍️ Loja de Souvenirs")
    
    if not st.session_state.logado:
        st.warning("Faça login no 'Meu Painel' para acessar a loja!")
    else:
        # 1. BUSCA PRODUTOS DA PLANILHA EM TEMPO REAL
        try:
            sh = client.open(NOME_PLANILHA)
            aba_p = sh.worksheet("PRODUTOS")
            df_p = pd.DataFrame(aba_p.get_all_records())
            # Filtra apenas ATIVO = SIM
            produtos = df_p[df_p['Ativo'] == "SIM"].to_dict('records')
        except Exception as e:
            st.error(f"Erro ao carregar catálogo: {e}")
            st.stop()

        # 2. SINCRONIZAÇÃO DE SALDO REAL
        try:
            aba_c = sh.worksheet("CLIENTES")
            c = st.session_state.dados_usuario
            cpf_logado = str(c['ID_Cliente'])
            celula_usuario = aba_c.find(cpf_logado)
            # Saldo na Coluna K (11)
            saldo_real = float(aba_c.cell(celula_usuario.row, 11).value)
            st.subheader(f"Seu Saldo: {int(saldo_real)} Goles")
        except:
            st.error("Erro ao sincronizar saldo.")
            st.stop()

        # 3. EXIBIÇÃO DOS PRODUTOS
        cols = st.columns(2)
        for i, p in enumerate(produtos):
            with cols[i % 2]:
                st.markdown(f"""
                    <div style='background-color: #161b3d; padding: 15px; border-radius: 10px 10px 0 0; border: 1px solid #e68a00; border-bottom: none; text-align: center;'>
                        <h3 style='margin:0; color: #e68a00;'>{p['Emoji']} {p['Nome']}</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                if p['URL_Imagem']:
                    st.image(p['URL_Imagem'], use_container_width=True)
                else:
                    st.info("Foto em breve!")

                st.markdown(f"""
                    <div style='background-color: #161b3d; padding: 10px; border-radius: 0 0 10px 10px; border: 1px solid #e68a00; border-top: none; margin-bottom: 20px; text-align: center;'>
                        <p style='color: #ffffff; font-size: 1.2em; font-weight: bold;'>{p['Pontos']} GOLES</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # 4. BOTÃO DE RESGATE SEGURO
                if saldo_real >= float(p['Pontos']):
                    if st.button(f"RESGATAR {p['Nome'].upper()}", key=f"btn_res_{i}"):
                        with st.spinner("Processando resgate..."):
                            try:
                                voucher = gerar_codigo()
                                novo_saldo = saldo_real - float(p['Pontos'])
                                
                                # Débito na planilha
                                aba_c.update_cell(celula_usuario.row, 11, novo_saldo)
                                
                                # Registro do Resgate
                                aba_r = sh.worksheet("RESGATES")
                                aba_r.append_row([
                                    voucher, cpf_logado, p['Nome'], p['Pontos'], 
                                    pd.Timestamp.now().strftime("%d/%m/%Y"), "Pendente"
                                ])
                                
                                # QR Code
                                url_base = "https://golesdevantagemculundria.streamlit.app" 
                                link_resgate = f"{url_base}?voucher={voucher}"
                                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(link_resgate)}"
                                
                                st.success(f"Confirmado! -{p['Pontos']} Goles.")
                                st.markdown(f"""
                                    <div style='text-align: center; background-color: #ffffff; padding: 20px; border-radius: 15px; border: 5px solid #e68a00;'>
                                        <p style='color: #0b0e27; font-weight: bold;'>MOSTRE NO BALCÃO:</p>
                                        <img src='{qr_url}' style='width: 180px;'>
                                        <h1 style='color: #0b0e27; margin: 0;'>{voucher}</h1>
                                    </div>
                                """, unsafe_allow_html=True)
                                st.balloons()
                                st.session_state.dados_usuario['Saldo_Atual'] = novo_saldo
                            except Exception as e:
                                st.error(f"Erro: {e}")
                else:
                    st.button("Saldo Insuficiente", key=f"btn_off_{i}", disabled=True)

# ==========================================
# ABA 3: CADASTRO (FAZER PARTE DA CONFRARIA)
# ==========================================

            
# ==========================================
# ABA 2: LOJA DE SOUVENIRS (DINÂMICA)
# ==========================================
elif aba == "Loja de Souvenirs":
    st.title("🛍️ Loja de Souvenirs")
    
    if not st.session_state.logado:
        st.warning("Faça login no 'Meu Painel' para acessar a loja!")
    else:
        # 1. BUSCA PRODUTOS DA PLANILHA EM TEMPO REAL
        try:
            sh = client.open(NOME_PLANILHA)
            aba_p = sh.worksheet("PRODUTOS")
            df_p = pd.DataFrame(aba_p.get_all_records())
            # Filtra apenas ATIVO = SIM
            produtos = df_p[df_p['Ativo'] == "SIM"].to_dict('records')
        except Exception as e:
            st.error(f"Erro ao carregar catálogo: {e}")
            st.stop()

        # 2. SINCRONIZAÇÃO DE SALDO REAL
        try:
            aba_c = sh.worksheet("CLIENTES")
            c = st.session_state.dados_usuario
            cpf_logado = str(c['ID_Cliente'])
            celula_usuario = aba_c.find(cpf_logado)
            # Saldo na Coluna K (11)
            saldo_real = float(aba_c.cell(celula_usuario.row, 11).value)
            st.subheader(f"Seu Saldo: {int(saldo_real)} Goles")
        except:
            st.error("Erro ao sincronizar saldo.")
            st.stop()

        # 3. EXIBIÇÃO DOS PRODUTOS
        cols = st.columns(2)
        for i, p in enumerate(produtos):
            with cols[i % 2]:
                st.markdown(f"""
                    <div style='background-color: #161b3d; padding: 15px; border-radius: 10px 10px 0 0; border: 1px solid #e68a00; border-bottom: none; text-align: center;'>
                        <h3 style='margin:0; color: #e68a00;'>{p['Emoji']} {p['Nome']}</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                if p['URL_Imagem']:
                    st.image(p['URL_Imagem'], use_container_width=True)
                else:
                    st.info("Foto em breve!")

                st.markdown(f"""
                    <div style='background-color: #161b3d; padding: 10px; border-radius: 0 0 10px 10px; border: 1px solid #e68a00; border-top: none; margin-bottom: 20px; text-align: center;'>
                        <p style='color: #ffffff; font-size: 1.2em; font-weight: bold;'>{p['Pontos']} GOLES</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # 4. BOTÃO DE RESGATE SEGURO
                if saldo_real >= float(p['Pontos']):
                    if st.button(f"RESGATAR {p['Nome'].upper()}", key=f"btn_res_{i}"):
                        with st.spinner("Processando resgate..."):
                            try:
                                voucher = gerar_codigo()
                                novo_saldo = saldo_real - float(p['Pontos'])
                                
                                # Débito na planilha
                                aba_c.update_cell(celula_usuario.row, 11, novo_saldo)
                                
                                # Registro do Resgate
                                aba_r = sh.worksheet("RESGATES")
                                aba_r.append_row([
                                    voucher, cpf_logado, p['Nome'], p['Pontos'], 
                                    pd.Timestamp.now().strftime("%d/%m/%Y"), "Pendente"
                                ])
                                
                                # QR Code
                                url_base = "https://golesdevantagemculundria.streamlit.app" 
                                link_resgate = f"{url_base}?voucher={voucher}"
                                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(link_resgate)}"
                                
                                st.success(f"Confirmado! -{p['Pontos']} Goles.")
                                st.markdown(f"""
                                    <div style='text-align: center; background-color: #ffffff; padding: 20px; border-radius: 15px; border: 5px solid #e68a00;'>
                                        <p style='color: #0b0e27; font-weight: bold;'>MOSTRE NO BALCÃO:</p>
                                        <img src='{qr_url}' style='width: 180px;'>
                                        <h1 style='color: #0b0e27; margin: 0;'>{voucher}</h1>
                                    </div>
                                """, unsafe_allow_html=True)
                                st.balloons()
                                st.session_state.dados_usuario['Saldo_Atual'] = novo_saldo
                            except Exception as e:
                                st.error(f"Erro: {e}")
                else:
                    st.button("Saldo Insuficiente", key=f"btn_off_{i}", disabled=True)

# ==========================================
# ABA 3: CADASTRO (FAZER PARTE DA CONFRARIA)
# ==========================================
elif aba == "Fazer Parte da Confraria":
    st.title("🧪 Entre para a Confraria")
    st.write("Preencha seus dados para começar a acumular goles!")
    
    # Usamos um formulário para organizar os campos
    with st.form("form_cadastro_culundria", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        cpf_cad = st.text_input("CPF (apenas 11 números)")
        whats = st.text_input("WhatsApp (com DDD)")
        email = st.text_input("E-mail")
        senha_cad = st.text_input("Crie uma Senha", type="password")
        
        enviar = st.form_submit_button("CRIAR MINHA CONTA")
        
        if enviar:
            # Limpeza do CPF (remove pontos e traços)
            cpf_limpo = "".join(filter(str.isdigit, str(cpf_cad))).strip()
            
            if nome and len(cpf_limpo) == 11 and senha_cad:
                try:
                    sh_c = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                    
                    # --- TRAVA DE SEGURANÇA: VERIFICA SE CPF JÁ EXISTE ---
                    cpfs_existentes = sh_c.col_values(1) # Coluna A
                    
                    if cpf_limpo in cpfs_existentes:
                        st.error("🚫 Este CPF já é de um Confrade! Tente fazer Login.")
                    else:
                        # Se não existe, monta a linha para a planilha (11 colunas conforme sua aba CLIENTES)
                        # A(ID), B(Nome), C(Telefone), D(Email), E(Nível), F(Pts T), G(Progr), H(Data), I(Senha), J(Gastos), K(Saldo)
                        nova_linha = [
                            cpf_limpo, 
                            nome.strip().upper(), 
                            whats.strip(), 
                            email.strip().lower(), 
                            "Explorador", 
                            100, # Pontos de boas-vindas
                            0,   # Progresso inicial
                            pd.Timestamp.now().strftime("%d/%m/%Y"), 
                            str(senha_cad).strip(),
                            0,   # Pontos Gastos inicial
                            100  # Saldo Atual inicial
                        ]
                        
                        # Localiza a próxima linha vazia real
                        proxima_vazia = len(cpfs_existentes) + 1
                        sh_c.update(f"A{proxima_vazia}:K{proxima_vazia}", [nova_linha])
                        
                        st.success(f"✅ Bem-vindo, {nome.split()[0]}! Sua conta foi criada com 100 Goles de bônus.")
                        st.balloons()
                        
                except Exception as e:
                    st.error(f"Erro ao acessar o banco de dados: {e}")
            else:
                st.warning("⚠️ Por favor, preencha Nome, CPF (11 dígitos) e Senha.")

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
