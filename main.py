import streamlit as st
import os
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

#  3. CONFIGURAÇÃO DO LOGO NA SIDEBAR ---
with st.sidebar:
    # Verifica se o arquivo existe na pasta raiz
    if os.path.exists("logoculundria.png"):
        # Criamos colunas para centralizar o logo
        col_logo_1, col_logo_2, col_logo_3 = st.columns([0.1, 5, 0.1])
        with col_logo_2:
            st.image("logoculundria.png", use_container_width=True)
    else:
        st.error("⚠️ Arquivo 'logoculundria.png' não encontrado na pasta do App.")
    
    st.markdown("<h3 style='text-align: center;'>Confraria Culundria</h3>", unsafe_allow_html=True)
    st.write("---")
# --- FUNÇÃO PARA GERAR CÓDIGO ÚNICO ---
def gerar_codigo():
    return 'V-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
# --- FUNÇÃO ROBUSTA PARA LER PLANILHA (EVITA ERRO DE COLUNA VAZIA) ---

def ler_aba_segura(aba):
    dados = aba.get_all_values()
    if not dados: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    return df.loc[:, df.columns != ''] # Remove colunas sem nome

# --- FUNÇÃO PARA PAGAR O PADRINHO (DEVE FICAR NO TOPO) ---
def validar_e_pagar_indicacao(nome_cliente, whats_cliente):
    try:
        sh = client.open(NOME_PLANILHA)
        aba_ind = sh.worksheet("INDICAÇÕES")
        aba_cli = sh.worksheet("CLIENTES")
        df_ind = ler_aba_segura(aba_ind)
        
        # Filtra indicação pendente por nome ou whats
        filtro = (df_ind['Venda_Concluída'] == "NÃO") & \
                 ((df_ind['Telefone_Amigo'].astype(str) == str(whats_cliente).strip()) | 
                  (df_ind['ID_Cliente'] == str(nome_cliente).upper().strip()))
        
        idx = df_ind[filtro].index
        if not idx.empty:
            linha_f = idx[0] + 2 
            id_padrinho = str(df_ind.iloc[idx[0]]['ID_Padrinho']).strip()
            aba_ind.update_cell(linha_f, 4, "SIM") # Coluna D
            
            cel_p = aba_cli.find(id_padrinho)
            if cel_p:
                val_saldo = float(aba_cli.cell(cel_p.row, 11).value or 0)
                val_total = float(aba_cli.cell(cel_p.row, 6).value or 0)
                aba_cli.update_cell(cel_p.row, 11, val_saldo + 50)
                aba_cli.update_cell(cel_p.row, 6, val_total + 50)
                st.toast("🎁 Bônus de Indicação creditado ao Padrinho!")
    except: pass

# --- FUNÇÃO PARA LER QUALQUER ABA SEM ERROS DE COLUNA VAZIA ---
def ler_planilha_sem_erro(aba):
    try:
        dados = aba.get_all_values()
        if not dados:
            return pd.DataFrame()
        # Transforma em DataFrame usando a primeira linha como cabeçalho
        df = pd.DataFrame(dados[1:], columns=dados[0])
        # REMOVE colunas que não têm nome (as que causam o erro [''])
        df = df.loc[:, df.columns != '']
        return df
    except Exception as e:
        st.error(f"Erro ao processar dados da aba: {e}")
        return pd.DataFrame()

# --- ESTILO PREMIUM CULUNDRIA (ANTI-AZUL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
    [data-testid="stAppViewContainer"] { background-color: #0b0e27; color: #ffffff; font-family: 'Montserrat', sans-serif; }
    [data-testid="stSidebar"] { background-color: #050714; }
    .stMetric { background-color: #161b3d; padding: 0.7rem; border-radius: 10px; border: 1px solid #e68a00; }
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
def calcular_status_confraria(pontos_historicos):
    try: 
        p = float(pontos_historicos)
    except: 
        p = 0.0
    
    if p <= 500:
        return {
            "nivel": "Explorador", 
            "desc": "Descobrindo novos horizontes.", 
            "cor": "#a8dadc", 
            "proximo_pts": 501, 
            "msg": f"Faltam {int(501 - p)} goles para ser 'Chegado'."
        }
    elif p <= 1000:
        return {
            "nivel": "Chegado", 
            "desc": "A casa já é sua!", 
            "cor": "#e68a00", 
            "proximo_pts": 1001, 
            "msg": f"Faltam {int(1001 - p)} goles para ser 'Tarimbado'."
        }
    elif p <= 2000:
        return {
            "nivel": "Tarimbado", 
            "desc": "Veterano de guerra!", 
            "cor": "#d4a017", 
            "proximo_pts": 2001, 
            "msg": f"Faltam {int(2001 - p)} goles para se tornar um 'Patrimônio'!"
        }
    else:
        return {
            "nivel": "Patrimônio", 
            "desc": "Você é uma lenda sagrada.", 
            "cor": "#ffcc33", 
            "proximo_pts": p, 
            "msg": "Obrigado, lenda! 🍻"
        }
        
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
    # --- CAPTURA DE INDICAÇÃO (Rastreamento) ---
    query_params = st.query_params
    quem_indicou = query_params.get("ref", None)

    if not st.session_state.get('logado', False):
        st.title("🍺 Acesso à Confraria")
        
        # Alerta se ele veio por indicação
        if quem_indicou:
            st.toast(f"🔗 Link de indicação detectado! Finalize seu cadastro para ativar o bônus.")

        with st.form("login_form"):
            cpf_login = st.text_input("Digite seu CPF (apenas números)")
            senha_login = st.text_input("Sua Senha", type="password")
            btn_entrar = st.form_submit_button("ENTRAR NA CONFRARIA")
            
            if btn_entrar:
                try:
                    sh_c = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                    df_c = ler_planilha_sem_erro(sh_c)
                    
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

              
                        # --- 1. PROCESSAMENTO DE DADOS (INATIVIDADE E HISTÓRICO) ---
            dias_inatividade = 0
            meu_hist = pd.DataFrame()
            
            try:
                sh_v = client.open(NOME_PLANILHA).worksheet("VENDAS")
                # Usamos a função segura que remove colunas vazias
                df_v = ler_aba_segura(sh_v) 
                
                if not df_v.empty:
                    # NORMALIZAÇÃO: Remove espaços e garante que tudo seja STRING para comparar
                    df_v['ID_Cliente'] = df_v['ID_Cliente'].astype(str).str.strip()
                    cpf_logado = str(u['ID_Cliente']).strip()
                    
                    # FILTRAGEM
                    meu_hist = df_v[df_v['ID_Cliente'] == cpf_logado].copy()
                    
                    if not meu_hist.empty:
                        # Converte data para cálculo de inatividade
                        meu_hist['Data_Venda'] = pd.to_datetime(meu_hist['Data_Venda'], dayfirst=True, errors='coerce')
                        ultima_compra = meu_hist['Data_Venda'].max()
                        if pd.notnull(ultima_compra):
                            dias_inatividade = (pd.Timestamp.now() - ultima_compra).days
            except Exception as e:
                st.error(f"Erro ao carregar histórico: {e}")
            # --- 2. MÉTRICAS (LÓGICA CORRIGIDA) ---
            # Pegamos os valores garantindo que sejam numéricos
            try:
                saldo_disponivel = float(u.get('Saldo_Atual', 0))
                pontos_vida_toda = float(u.get('Pontos_Totais', 0))
            except:
                saldo_disponivel = 0.0
                pontos_vida_toda = 0.0

            # O STATUS agora é calculado obrigatoriamente pelos PONTOS TOTAIS
            status = calcular_status_confraria(pontos_vida_toda)

            c1, c2, c3 = st.columns([1, 1, 1])

            with c1:
                st.markdown(f"""
                    <div style="background-color: #161b3d; padding: 15px; border-radius: 5px; border-bottom: 4px solid #e68a00; height: 100px;">
                        <p style="margin:0; font-size: 0.7rem; color: #aaa; font-weight: bold; text-transform: uppercase;">SALDO DISPONÍVEL</p>
                        <h2 style="margin:0; font-size: 1.6rem; color: #ffffff; font-weight: 700;">{int(saldo_disponivel)} GOLES</h2>
                    </div>
                """, unsafe_allow_html=True)

            with c2:
                st.markdown(f"""
                    <div style="background-color: #161b3d; padding: 15px; border-radius: 5px; border-bottom: 4px solid #e68a00; height: 100px;">
                        <p style="margin:0; font-size: 0.7rem; color: #aaa; font-weight: bold; text-transform: uppercase;">STATUS</p>
                        <h2 style="margin:0; font-size: 1.6rem; color: #ffffff; font-weight: 700;">{status['nivel'].upper()}</h2>
                    </div>
                """, unsafe_allow_html=True)

            with c3:
                cor_inat = "#ff4b4b" if dias_inatividade > 60 else "#aaa"
                st.markdown(f"""
                    <div style="background-color: #161b3d; padding: 15px; border-radius: 5px; border-bottom: 4px solid {cor_inat}; height: 100px;">
                        <p style="margin:0; font-size: 0.7rem; color: #aaa; font-weight: bold; text-transform: uppercase;">INATIVIDADE</p>
                        <h2 style="margin:0; font-size: 1.6rem; color: #ffffff; font-weight: 700;">{dias_inatividade} DIAS</h2>
                    </div>
                """, unsafe_allow_html=True)
    
            st.write("") 
            st.write(f"**Nível Atual:** {status['nivel']}")
            st.write(f"*{status['desc']}*")
            
            # Lógica da Mensagem de Progresso
            if pontos_vida_toda > 2000:
                st.success("👑 Você é um Patrimônio da Culundria!")
            else:
                faltam = int(status['proximo_pts'] - pontos_vida_toda)
                st.info(f"🍻 Faltam **{faltam} goles** para o próximo nível!")

            # Ajuste da Barra de Progresso
            limite = status['proximo_pts']
            progresso = min(float(pontos_vida_toda) / limite, 1.0) if limite > 0 else 0
            st.progress(progresso)
            

# --- 3. BLOCO DE INDICAÇÃO (NOVIDADE) ---
            st.write("---")
            st.subheader("📢 Convide um Amigo")
            
            # Gerador de Link
            url_app = "https://golesdevantagemculundria.streamlit.app" # Verifique se a URL está correta
            link_ref = f"{url_app}/?ref={u['ID_Cliente']}"
            
            st.info("Ganhe **50 Goles** por cada amigo que se cadastrar pelo seu link e efetuar a primeira compra!")
            st.code(link_ref, language="text")
            
            # Botão de WhatsApp
            msg_wa = urllib.parse.quote(f"Bora tomar uma Culundria? Se cadastra pelo meu link e a gente ganha bônus: {link_ref}")
            st.markdown(f"""
                <a href="https://wa.me/?text={msg_wa}" target="_blank">
                    <button style="width:100%; border-radius:5px; background-color:#25d366; color:white; font-weight:bold; border:none; padding:10px; cursor:pointer;">
                        📲 COMPARTILHAR NO WHATSAPP
                    </button>
                </a>
            """, unsafe_allow_html=True)

            # --- 4. HISTÓRICO DE BARRIS ---
            st.write("---")
            st.subheader("🛢️ Histórico de Consumo")
            
            if not meu_hist.empty:
                # Limpa nomes de colunas para exibição
                meu_hist.columns = [str(c).strip() for c in meu_hist.columns]
                
                # Lista de colunas que você quer mostrar (ajuste conforme os nomes exatos na sua planilha)
                col_des = ['Data_Venda', 'Estilo_Chopp', 'Litragem_Total', 'Total_Pontos'] 
                
                # Verifica quais dessas colunas realmente existem na aba VENDAS
                col_exis = [c for c in col_des if c in meu_hist.columns]
                
                if col_exis:
                    exibir = meu_hist[col_exis].copy()
                    # Formata a data para ficar bonita (Dia/Mês/Ano)
                    exibir['Data_Venda'] = exibir['Data_Venda'].dt.strftime('%d/%m/%Y')
                    st.dataframe(exibir, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum consumo registrado ainda. Que tal uma Culundria hoje? 🍺")
                                
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
        # 1. CONEXÃO E BUSCA DE PRODUTOS
        try:
            sh = client.open(NOME_PLANILHA) # Abre a planilha mestre
            
            # Define a aba de produtos
            aba_p = sh.worksheet("PRODUTOS")
            df_p = ler_planilha_sem_erro(aba_p) # Usa a função blindada que criamos
            
            # Filtra apenas ATIVO = SIM
            produtos = df_p[df_p['Ativo'] == "SIM"].to_dict('records')
            
            # --- CORREÇÃO DO ERRO AQUI ---
            # Define a aba de clientes (sh_c) para poder buscar o saldo real
            sh_c = sh.worksheet("CLIENTES") 
            
            c = st.session_state.dados_usuario
            cpf_logado = str(c['ID_Cliente']).strip()
            
            # Busca a linha do usuário para ter o saldo mais atualizado possível
            celula_usuario = sh_c.find(cpf_logado)
            
            # Saldo na Coluna K (11)
            saldo_real = float(sh_c.cell(celula_usuario.row, 11).value or 0)
            st.subheader(f"Seu Saldo: {int(saldo_real)} Goles")
            
        except Exception as e:
            st.error(f"Erro ao carregar catálogo: {e}")
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
                    try:
                        st.image(p['URL_Imagem'], use_container_width=True)
                    except:
                        st.warning(f"Erro ao carregar imagem: {p['nome']}")                    
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
    
    # 1. Captura o padrinho da URL de forma persistente
    # Usamos o st.query_params para ler ?ref=CPF
    params = st.query_params
    padrinho_id = params.get("ref", None)

    if padrinho_id:
        st.success(f"✨ **Indicação Detectada!** Você ganhará bônus ao entrar.")

    # 2. Início do Formulário (Tudo deve estar indentado dentro do 'with')
    with st.form("form_cadastro_culundria", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        cpf_cad = st.text_input("CPF (apenas 11 números)")
        whats = st.text_input("WhatsApp (com DDD)")
        email = st.text_input("E-mail")
        senha_cad = st.text_input("Crie uma Senha", type="password")
        
        enviar = st.form_submit_button("CRIAR MINHA CONTA")
        
        if enviar:
            # Limpeza básica do CPF
            cpf_limpo = "".join(filter(str.isdigit, str(cpf_cad))).strip()
            
            if nome and len(cpf_limpo) == 11 and senha_cad:
                try:
                    sh = client.open(NOME_PLANILHA)
                    sh_c = sh.worksheet("CLIENTES")
                    
                    # Verifica se já existe
                    cpfs_existentes = sh_c.col_values(1)
                    
                    if cpf_limpo in cpfs_existentes:
                        st.error("🚫 Este CPF já é de um Confrade!")
                    else:
                        data_hoje = pd.Timestamp.now().strftime("%d/%m/%Y")
                        
                        # 3. CRIA O NOVO CLIENTE (11 colunas conforme seu padrão A-K)
                        nova_linha = [
                            cpf_limpo, 
                            nome.strip().upper(), 
                            whats.strip(), 
                            email.strip().lower(), 
                            "Explorador", 
                            100, # Boas-vindas
                            0, 
                            data_hoje, 
                            str(senha_cad).strip(), 
                            0, 
                            100 # Saldo inicial
                        ]
                        sh_c.append_row(nova_linha)

                        # 4. REGISTRO NA ABA INDICAÇÕES (Se houver padrinho)
                        if padrinho_id:
                            try:
                                sh_ind = sh.worksheet("INDICAÇÕES")
                                # Colunas: Nome_Amigo, Telefone_Amigo, Data_Indicação, Venda_Concluída, Pontos_Gerados, ID_Padrinho
                                nova_indicao = [
                                    cpf_limpo, #adiciona o cpf na coluna 1 da planilha Indicações
                                    nome.strip().upper(),
                                    whats.strip(),
                                    data_hoje,
                                    "NÃO", 
                                    50,
                                    str(padrinho_id),
                                ]
                                sh_ind.append_row(nova_indicao)
                            except Exception as e_ind:
                                # Erro na indicação não deve travar o cadastro principal
                                st.warning("Cadastro realizado, mas bônus não registrado.")

                        st.success(f"✅ Bem-vindo, {nome.split()[0]}! Sua conta foi criada.")
                        st.balloons()
                        
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("⚠️ Preencha Nome, CPF (11 dígitos) e Senha corretamente.")
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
            # --- CONEXÃO COM AS ABAS (IMPORTANTE!) ---
            sh = client.open(NOME_PLANILHA)
            sh_v = sh.worksheet("VENDAS")
            sh_c = sh.worksheet("CLIENTES") # <--- ISSO RESOLVE O ERRO 'sh_c not defined'
            
            # Carregamento de Dados usando a função blindada
            df_v = ler_planilha_sem_erro(sh_v)
            df_c = ler_planilha_sem_erro(sh_c)
            
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
                # Garante que as colunas existem antes de ordenar
                col_pontos = 'Pontos_Totais' if 'Pontos_Totais' in df_c.columns else 'Saldo_Atual'
                
                if not df_c.empty and col_pontos in df_c.columns:
                    # Converte para número para não ordenar errado
                    df_c[col_pontos] = pd.to_numeric(df_c[col_pontos], errors='coerce').fillna(0)
                    top_10 = df_c.nlargest(10, col_pontos)[['Nome_Completo', col_pontos]]
                    st.table(top_10)
                else:
                    st.info("Ainda não há dados para o ranking.")

        except Exception as e:
            st.error(f"Erro ao carregar dados do Mestre: {e}")
            #with tab_ranking:
             #   st.subheader("🏆 Top Confrades")
              #  col_pontos = 'Pontos_Totais' if 'Pontos_Totais' in df_c.columns else 'Saldo_Atual'
               # if col_pontos in df_c.columns:
                #    top_10 = df_c.nlargest(10, col_pontos)[['Nome_Completo', col_pontos]]
                 #   st.table(top_10)
                    
        #except Exception as e:
         #   st.error(f"Erro ao carregar dados: {e}")
