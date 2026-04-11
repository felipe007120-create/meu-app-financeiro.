import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import os

# 1. Configurações de Página e Design Pro
st.set_page_config(page_title="Dashboard Financeiro", page_icon="📈", layout="wide")

# Estilização para deixar os números grandes e profissionais
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 40px; font-weight: bold; color: #007BFF; }
    [data-testid="stMetricLabel"] { font-size: 18px; font-weight: 500; }
    .main { background-color: #fcfcfc; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007BFF; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. Banco de Dados Local
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

# --- HEADER PROFISSIONAL ---
st.title("📈 Gestão de Receita e Produtividade")
st.caption("Acompanhamento em tempo real de acionamentos e quilometragem.")

# --- DASHBOARD DE MÉTRICAS (KPIs) ---
if st.session_state.dados:
    df = pd.DataFrame(st.session_state.dados)
    
    # Linha de cartões no topo
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Receita Total", f"R$ {df['Total Final (R$)'].sum():,}")
    with m2:
        st.metric("Média por Serviço", f"R$ {df['Total Final (R$)'].mean():.0f}")
    with m3:
        st.metric("Distância Base", f"{df['KM Base'].sum()} km")
    with m4:
        st.metric("Total Horas", f"{df['Horas Líquidas'].sum():.1f}h")
    
    st.divider()

# --- ÁREA DE OPERAÇÃO ---
col_form, col_hist = st.columns([1, 2]) # 1 parte para o formulário, 2 para o histórico

with col_form:
    st.subheader("📝 Novo Registro")
    with st.form("registro_pro", clear_on_submit=True):
        st.write("---")
        data_ini = st.date_input("Data do Serviço")
        h_ini = st.time_input("Hora Início", value=None)
        h_fim = st.time_input("Hora Término", value=None)
        
        st.write("---")
        km_ini = st.number_input("KM Inicial", min_value=0)
        km_fim = st.number_input("KM Término", min_value=0)
        
        st.write("---")
        # Barra lateral interna (opcional se quiser mudar taxas na hora)
        valor_h = st.number_input("Taxa/Hora (R$)", value=30.0)
        valor_base = st.number_input("Taxa Base (R$)", value=220.0)
        
        submit = st.form_submit_button("REGISTRAR ATIVIDADE")

with col_hist:
    st.subheader("📑 Histórico Recente")
    if st.session_state.dados:
        df_vis = pd.DataFrame(st.session_state.dados)
        # Exibe a tabela com as colunas mais importantes primeiro
        st.dataframe(
            df_vis[['Data', 'Total Final (R$)', 'Horas Líquidas', 'KM Base']], 
            use_container_width=True, 
            hide_index=True
        )
        
        # Exportação Profissional
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_vis.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 Exportar Relatório Consolidado (Excel)",
            data=output.getvalue(),
            file_name=f"Relatorio_{datetime.now().strftime('%Y_%m')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Nenhum registro encontrado. Utilize o formulário ao lado para começar.")

# --- LÓGICA DE PROCESSAMENTO ---
if submit:
    if h_ini and h_fim:
        # Cálculo de tempo (Dedução de 3h)
        ini_dt = datetime.combine(data_ini, h_ini)
        data_fim_ok = data_ini if h_fim > h_ini else data_ini + timedelta(days=1)
        fim_dt = datetime.combine(data_fim_ok, h_fim)
        
        h_liq = max(0.0, ((fim_dt - ini_dt).total_seconds() / 3600) - 3.0)
        
        # Cálculo KM: (Ini + Fim) - 50
        km_base = max(0, (km_ini + km_fim) - 50)
        
        # Total Final
        total = valor_base + (h_liq * valor_h) + (km_base * 1.10)
        
        novo_registro = {
            'Data': data_ini.strftime('%d/%m/%Y'),
            'Horas Líquidas': round(h_liq, 2),
            'KM Base': km_base,
            'Total Final (R$)': int(total)
        }
        
        st.session_state.dados.append(novo_registro)
        salvar_dados(st.session_state.dados)
        st.toast("Registro salvo com sucesso!", icon="✅")
        st.rerun()
