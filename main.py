import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Alquimista Culundria", page_icon="🍺", layout="centered")

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

# 3. LÓGICA DE NAVEGAÇÃO ÚNICA
if "menu_radio" not in st.session_state:
    st.session_state.menu_radio = "Portal do Cliente"

with st.sidebar:
    try:
        st.image("logoculundria.png", use_container_width=True)
    except:
        st.warning("Logo não encontrada.")
    
    st.markdown("<h2 style='text-align: center;'>Culundria Cervejaria</h2>", unsafe_allow_html=True)
    st.write("📍 Cruzília, MG")
    st.markdown("---")
    
    # Criamos o rádio vinculado diretamente à chave 'menu_radio'
    aba = st.sidebar.radio(
        "Ir para:", 
        ["Portal do Cliente", "Quero ser Alquimista (Cadastro)", "Painel do Mestre (Admin)"],
        key="menu_radio"
    )

# ==========================================
# ABA 1: PORTAL DO CLIENTE
# ==========================================
if aba == "Portal do Cliente":
    st.title("🍺 Portal do Alquimista")
    cpf_input = st.text_input("Digite seu CPF (apenas números):")

    # --- O BOTÃO QUE MUDA A ABA ---
    st.write("") 
    if st.button("✨ Ainda não é um Alquimista? Cadastre-se aqui"):
        st.session_state.menu_radio = "Quero ser Alquimista (Cadastro)"
        st.rerun()

    if cpf_input:
        try:
            sheet = client.open(NOME_PLANILHA).worksheet("CLIENTES")
            df = pd.DataFrame(sheet.get_all_records())
            df['ID_Cliente'] = df['ID_Cliente'].astype(str)
            cliente = df[df['ID_Cliente'] == cpf_input.strip()]

            if not cliente.empty:
                c = cliente.iloc[0]
                
                try:
                    val_bruto = float(c['Progresso_Copo']) if str(c['Progresso_Copo']).strip() != "" else 0.0
                    if val_bruto > 1.0: val_bruto = val_bruto / 100.0
                    progresso = min(max(val_bruto, 0.0), 1.0)
                except:
                    progresso = 0.0

                st.markdown(f"## BEM-VINDO, ALQUIMISTA {c['Nome_Completo'].split()[0].upper()}!")
                st.write("---")

                col_status, col_pontos = st.columns([2, 1])
                with col_status:
                    st.markdown(f"""
                        <div style='background-color: #161b3d; padding: 20px; border-radius: 10px; border-left: 5px solid #e68a00;'>
                            <h4 style='margin:0; color: white;'>NÍVEL: {c['Nível_Atual']}</h4>
                            <p style='color: #aaa; font-size: 0.9em; margin:0;'>Sua jornada artesanal continua!</p>
                        </div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    st.progress(progresso)
                    st.caption(f"Você já completou **{int(progresso * 100)}%** do caminho.")

                with col_pontos:
                    st.metric("ESSÊNCIA ACUMULADA", f"{c['Pontos_Totais']} PTS")

                st.markdown("### 📜 GRIMÓRIO DE PEDIDOS")
                try:
                    sheet_vendas = client.open(NOME_PLANILHA).worksheet("VENDAS")
                    df_vendas = pd.DataFrame(sheet_vendas.get_all_records())
                    df_vendas.columns = df_vendas.columns.str.strip()
                    minhas_vendas = df_vendas[df_vendas['ID_Cliente'].astype(str) == cpf_input.strip()]
                    
                    if not minhas_vendas.empty:
                        colunas_venda = ['ID_Pedido', 'Data_Venda', 'Litragem_Total', 'Total Pontos']
                        st.table(minhas_vendas[colunas_venda])
                    else:
                        st.info("Ainda não constam barris registrados.")
                except:
                    st.warning("Erro ao carregar histórico.")

                st.markdown("---")
                st.write("### 🚀 INDIQUE UM AMIGO")
                with st.form("form_indicacao", clear_on_submit=True):
                    n_amigo = st.text_input("Nome do Amigo")
                    t_amigo = st.text_input("WhatsApp (com DDD)")
                    if st.form_submit_button("ENVIAR INDICAÇÃO"):
                        if n_amigo and t_amigo:
                            client.open(NOME_PLANILHA).worksheet("INDICAÇÕES").append_row([cpf_input, n_amigo, t_amigo, "Pendente"])
                            st.success("Indicação enviada!")
            else:
                st.warning("CPF não encontrado.")
        except Exception as e:
            st.error(f"Erro ao acessar dados: {e}")

# ==========================================
# ABA 2: CADASTRO
# ==========================================
elif aba == "Quero ser Alquimista (Cadastro)":
    st.title("🧪 Inicie sua Jornada Alquímica")
    st.write("Preencha os dados abaixo para começar a acumular pontos na Culundria!")

    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        cpf_novo = st.text_input("Seu CPF (apenas números)")
        whatsapp = st.text_input("WhatsApp (com DDD)")
        email = st.text_input("E-mail")
        submit_cad = st.form_submit_button("CRIAR MINHA CONTA")

        if submit_cad:
            if nome and cpf_novo and whatsapp and email:
                try:
                    # TENTA FAZER O CADASTRO
                    sheet_cli = client.open(NOME_PLANILHA).worksheet("CLIENTES")
                    df_check = pd.DataFrame(sheet_cli.get_all_records())
                    
                    if str(cpf_novo).strip() in df_check['ID_Cliente'].astype(str).values:
                        st.warning("CPF já cadastrado! Vá ao Portal do Cliente.")
                    else:
                        data_hoje = pd.Timestamp.now().strftime("%d/%m/%Y")
                        
                        # Lista completa e fechada corretamente
                        nova_linha = [
                            str(cpf_novo).strip(), 
                            nome.strip().upper(), 
                            whatsapp.strip(), 
                            email.strip().lower(), 
                            "Alquimista Aprendiz", 
                            0, 
                            0, 
                            data_hoje
                        ]
                        
                        sheet_cli.append_row(nova_linha)
                        st.success(f"Bem-vindo, {nome.split()[0]}! Sua jornada começou.")
                        st.balloons()
                
                except Exception as e:
                    # SE DER ERRO ACIMA, EXECUTA ISSO (O que estava faltando!)
                    st.error(f"Erro ao salvar no grimório: {e}")
            
            else:
                st.error("Preencha todos os campos!")
