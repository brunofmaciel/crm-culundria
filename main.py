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

# ==========================================
# 2. CONEXÃO COM GOOGLE SHEETS
# ==========================================
def conectar_google_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        # Puxa os dados do painel "Secrets" do Streamlit
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro na conexão com o Google: {e}")
        st.stop()

# Agora sim, inicializamos o cliente usando a função acima
client = conectar_google_sheets()
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
        return {"nivel": "Tarimbado", "desc": "Veterano de guerra!", "cor": "#d4a017", "proximo_pts": 2000, "msg": "Se torne um Patrimônio! Faça um novo pedido e supere os 2000 goles"}
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
                        st.session_state.logado = True
                        st.session_state.dados_usuario = user.iloc[0].to_dict()
                        st.success("Login realizado! Abrindo seu barril...")
                        st.rerun()
                    else:
                        st.error("CPF ou Senha não encontrados.")
                except Exception as e:
                    st.error(f"Erro de conexão com a planilha: {e}")
    
    else:
        u = st.session_state.get('dados_usuario')
        
        if u:
            st.title(f"🍻 Painel do Confrade")
            st.subheader(f"Bem-vindo, {u.get('Nome_Completo', 'Amigo').split()[0]}!")
            
            # --- 1. PROCESSAMENTO DE DADOS (INATIVIDADE) ---
            dias_inatividade = 0
            meu_hist = pd.DataFrame()
            
            try:
                sh_v = client.open(NOME_PLANILHA).worksheet("VENDAS")
                df_v = pd.DataFrame(sh_v.get_all_records())
                
                # Filtra pelo CPF e limpa espaços
                df_v['ID_Cliente'] = df_v['ID_Cliente'].astype(str).str.strip()
                meu_hist = df_v[df_v['ID_Cliente'] == str(u['ID_Cliente']).strip()].copy()
                
                if not meu_hist.empty:
                    # Converte a coluna Data_Venda para data real
                    meu_hist['Data_Venda'] = pd.to_datetime(meu_hist['Data_Venda'], dayfirst=True, errors='coerce')
                    meu_hist = meu_hist.dropna(subset=['Data_Venda']) # Remove erros de data
                    
                    if not meu_hist.empty:
                        ultima_compra = meu_hist['Data_Venda'].max()
                        dias_inatividade = (pd.Timestamp.now() - ultima_compra).days
            except:
                pass

            
            # --- 2. MÉTRICAS COM FONTES REDUZIDAS ---
            saldo = u.get('Saldo_Atual', 0)
            status = calcular_status_confraria(saldo)
        
            # Criamos as colunas
            c1, c2, c3 = st.columns(3)
        
            # Usamos HTML/CSS dentro de cada coluna para controlar o tamanho exato da fonte
            with c1:
                st.markdown(f"""
                    <div style="background-color: #161b3d; padding: 10px; border-radius: 5px; border-bottom: 3px solid #e68a00;">
                        <p style="margin:0; font-size: 0.75rem; color: #aaa; font-weight: bold;">SALDO</p>
                        <h2 style="margin:0; font-size: 2.0rem; color: #e68a00;">{int(saldo)} Goles</h2>
                    </div>
                """, unsafe_allow_html=True)
            
            with c2:
                st.markdown(f"""
                    <div style="background-color: #161b3d; padding: 10px; border-radius: 5px; border-bottom: 3px solid #00d4ff;">
                        <p style="margin:0; font-size: 0.75rem; color: #aaa; font-weight: bold;">STATUS</p>
                        <h2 style="margin:0; font-size: 1.5.0rem; color: #ffffff;">{status['nivel']}</h2>
                    </div>
                """, unsafe_allow_html=True)
            
            with c3:
                st.markdown(f"""
                    <div style="background-color: #161b3d; padding: 10px; border-radius: 5px; border-bottom: 3px solid #ff4b4b;">
                        <p style="margin:0; font-size: 0.75rem; color: #aaa; font-weight: bold;">INATIVIDADE</p>
                        <h2 style="margin:0; font-size: 2.0rem; color: #ffffff;">{dias_inatividade} dias</h2>
                    </div>
                """, unsafe_allow_html=True)

            st.write("") # Espaçamento sutil

        
            # --- 3. BARRA DE PROGRESSO E ALERTA DE EXPIRAÇÃO ---
            st.write(f"**Status:** {status['desc']}")
            limite = status['proximo_pts'] if status['proximo_pts'] > 0 else 1
            progresso = min(float(saldo) / limite, 1.0)
            st.progress(progresso)
            
            # Lógica de Expiração (365 dias)
            dias_restantes = 365 - dias_inatividade
            if dias_restantes <= 60:
                st.warning(f"⚠️ Atenção! Seus pontos expiram em {dias_restantes} dias. Peça um novo barril!")
            else:
                st.info(f"💡 {status['msg']} (Seus pontos expiram em {dias_restantes} dias! Faça um novo pedido e renove seu saldo)")

            # --- 4. HISTÓRICO DE BARRIS (TABELA) ---
            st.write("---")
            st.subheader("🛢️ Histórico de Consumo")
            
            if not meu_hist.empty:
                # Formata para exibição
                meu_hist.columns = [str(c).strip() for c in meu_hist.columns]
                colunas_desejadas = ['Data_Venda', 'Estilo_Chopp', 'Goles Acumulados', 'Total_Pontos']
                colunas_existentes = [c for c in colunas_desejadas if c in meu_hist.columns]
                if colunas_existentes:
                    exibir = meu_hist[colunas_existentes].copy()
                
                    # Opcional: Renomear para ficar bonito no app
                    exibir.columns = [c.replace('_', ' ') for c in exibir.columns]
        
                    st.dataframe(exibir, use_container_width=True)
                else:
                    st.warning("As colunas de histórico não foram encontradas na planilha.")
            else:
                st.info("Nenhum consumo registrado ainda. Que tal uma Culundria hoje? 🍺")
            
            # --- 5. BOTÃO DE SAIR ---
            if st.button("🚪 SAIR DA CONFRARIA", use_container_width=True):
                st.session_state.logado = False
                st.session_state.dados_usuario = None
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
# ABA 4: AREA DO MESTRE
# ==========================================
elif aba == "Área do Mestre":
    st.title("🧙‍♂️ Grimório da Culundria")
    
    # 1. Defina sua senha aqui
    SENHA_MESTRE = "12345" 

    if "mestre_autenticado" not in st.session_state:
        st.session_state.mestre_autenticado = False

    # 2. TELA DE LOGIN (Se não estiver autenticado)
    if not st.session_state.mestre_autenticado:
        st.info("Acesso restrito aos Mestres Cervejeiros.")
        with st.form("form_login_mestre"):
            senha_digitada = st.text_input("Chave do Grimório", type="password")
            btn = st.form_submit_button("Abrir Relatórios")
            
            if btn:
                if senha_digitada == SENHA_MESTRE:
                    st.session_state.mestre_autenticado = True
                    st.session_state.nome_mestre = "Bruno"
                    st.success("Acesso concedido!")
                    st.rerun()
                else:
                    st.error("Chave incorreta ou mestre não cadastrado.")
    
    # 3. ÁREA AUTORIZADA (Só entra aqui se st.session_state.mestre_autenticado for True)
    else:
        st.success(f"Logado como: Mestre {st.session_state.nome_mestre}")
        
        if st.button("Sair da Área Administrativa"):
            st.session_state.mestre_autenticado = False
            st.rerun()

        # Criação das Abas
        tab_balcao, tab_relatorios, tab_ranking = st.tabs(["🎫 Validar Voucher", "📊 Relatórios", "🏆 Ranking"])
        
        try:
            # Carregamento de Dados
            sh_v = client.open(NOME_PLANILHA).worksheet("VENDAS")
            df_v = pd.DataFrame(sh_v.get_all_records())
            
            sh_c = client.open(NOME_PLANILHA).worksheet("CLIENTES")
            df_c = pd.DataFrame(sh_c.get_all_records())
            
            # Limpeza e Conversão de Segurança
            df_v['Litragem_Total'] = pd.to_numeric(df_v['Litragem_Total'], errors='coerce').fillna(0)
            
            if 'Pontos_Totais' in df_c.columns:
                df_c['Pontos_Totais'] = pd.to_numeric(df_c['Pontos_Totais'], errors='coerce').fillna(0)
            if 'Saldo_Atual' in df_c.columns:
                df_c['Saldo_Atual'] = pd.to_numeric(df_c['Saldo_Atual'], errors='coerce').fillna(0)

            # --- ABA 1: VALIDAÇÃO DE VOUCHER ---
            with tab_balcao:
                st.subheader("🏁 Validação de Resgate")
                # Captura voucher da URL se o mestre clicou no link do QR Code
                v_url = st.query_params.get("voucher", "")
                
                cod_v = st.text_input("Código do Voucher:", value=v_url, placeholder="Ex: V-A1B2").upper().strip()
                
                if st.button("VERIFICAR E DAR BAIXA"):
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
                                st.query_params.clear()
                            else:
                                st.error("❌ Este voucher já foi utilizado!")
                        else:
                            st.error("❓ Código não encontrado.")

            # --- ABA 2: RELATÓRIOS ---
            with tab_relatorios:
                st.subheader("📊 Resumo da Brassagem")
                c1, c2, c3 = st.columns(3)
                c1.metric("Litragem Total", f"{df_v['Litragem_Total'].sum():.1f} L")
                c2.metric("Confrades", len(df_c))
                if 'Saldo_Atual' in df_c.columns:
                    c3.metric("Pontos p/ Troca", int(df_c['Saldo_Atual'].sum()))
                
                col_estilo = 'Estilo Chopp' if 'Estilo Chopp' in df_v.columns else 'Estilo_Chopp'
                if col_estilo in df_v.columns:
                    st.write("---")
                    st.subheader("🍺 Estilos mais pedidos")
                    chart_data = df_v.groupby(col_estilo)['Litragem_Total'].sum()
                    st.bar_chart(chart_data)

            # --- ABA 3: RANKING ---
            with tab_ranking:
                st.subheader("🏆 Top Confrades")
                col_pontos = 'Pontos_Totais' if 'Pontos_Totais' in df_c.columns else 'Saldo_Atual'
                if col_pontos in df_c.columns:
                    top_10 = df_c.nlargest(10, col_pontos)[['Nome_Completo', col_pontos]]
                    st.table(top_10)
                    
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
