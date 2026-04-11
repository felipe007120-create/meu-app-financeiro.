import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import os

# 1. Configurações de Página
st.set_page_config(page_title="Gestor de Ganhos", page_icon="💰", layout="wide")

# Link da sua nova Logo (Opção 1)
LOGO_URL = "https://felipe-financas.s3.amazonaws.com/logo_gestor_ganhos.png" # Exemplo de link

# Interface Profissional
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 35px; font-weight: bold; color: #1E90FF; }
    [data-testid="stSidebar"] { padding-top: 0rem; }
    .main { background-color: #fcfcfc; }
    </style>
    """, unsafe_allow_html=True)

# 2. Banco de Dados
DB_FILE = "dados_financeiros.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        try: return pd.read_csv(DB_FILE).to_dict('records')
        except: return []
    return []

def salvar_dados(dados):
    pd.DataFrame(dados).to_csv(DB_FILE, index=False)

if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

# --- BARRA LATERAL COM LOGO ---
with st.sidebar:
    # Aqui adicionamos a logo no topo da barra lateral
    st.image("https://i.imgur.com/your_image_link.png", use_container_width=True, caption="Monitoramento Inteligente")
    st.divider()
    st.header("⚙️ Configurações")
    VALOR_HORA = st.number_input("Valor por Hora (R$)", value=30.0)
    VALOR_ACIONAMENTO = st.number_input("Valor Acionamento (R$)", value=220.0)

# --- CABEÇALHO PRINCIPAL ---
st.title("Gestor de Ganhos")
st.caption("Sistema de monitoramento de produtividade e faturamento.")

# --- DASHBOARD DE MÉTRICAS ---
if st.session_state.dados:
    df = pd.DataFrame(st.session_state.dados)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Receita Total", f"R$ {df['Total Final (R$)'].sum():,}")
    with m2: st.metric("Média/Serviço", f"R$ {df['Total Final (R$)'].mean():.0f}")
    with m3: st.metric("KM Base Total", f"{df['KM Base'].sum()} km")
    with m4: st.metric("Horas Líquidas", f"{df['Horas Líquidas'].sum():.1f}h")
    st.divider()

# --- FORMULÁRIO E HISTÓRICO ---
col_form, col_hist = st.columns([1, 2])

with col_form:
    st.subheader("📝 Novo Registro")
    with st.form("registro_form", clear_on_submit=True):
        data_ini = st.date_input("Data do Serviço")
        h_ini = st.time_input("Hora Início", value=None)
        h_fim = st.time_input("Hora Término", value=None)
        km_ini = st.number_input("KM Inicial", min_value=0)
        km_fim = st.number_input("KM Término", min_value=0)
        submit = st.form_submit_button("SALVAR ATIVIDADE")

if submit:
    if h_ini and h_fim:
        ini_dt = datetime.combine(data_ini, h_ini)
        data_fim_ok = data_ini if h_fim > h_ini else data_ini + timedelta(days=1)
        fim_dt = datetime.combine(data_fim_ok, h_fim)
        
        # Regra KM e Tempo (Com Trava de Mínimo de 1h)
        km_base = max(0, (km_ini + km_fim) - 50)
        h_brutas = (fim_dt - ini_dt).total_seconds() / 3600
        h_calc = h_brutas - 3.0
        
        # Trava de Segurança: Se trabalhou > 3h, garante pelo menos 1h paga.
        h_liq = max(1.0, h_calc) if h_brutas > 3.0 else 0.0
        
        total = VALOR_ACIONAMENTO + (h_liq * VALOR_HORA) + (km_base * 1.10)
        
        novo = {
            'Data': data_ini.strftime('%d/%m/%Y'),
            'Horas Líquidas': round(h_liq, 2),
            'KM Base': km_base,
            'Total Final (R$)': int(total)
        }
        st.session_state.dados.append(novo)
        salvar_dados(st.session_state.dados)
        st.toast("Dados registrados com sucesso!")
        st.rerun()

with col_hist:
    st.subheader("📑 Histórico")
    if st.session_state.dados:
        df_vis = pd.DataFrame(st.session_state.dados)
        st.dataframe(df_vis, use_container_width=True, hide_index=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_vis.to_excel(writer, index=False)
        st.download_button("📥 Exportar Relatório", output.getvalue(), "Relatorio.xlsx")
