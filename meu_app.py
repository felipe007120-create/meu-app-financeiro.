import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import os
import plotly.express as px

# 1. Configurações Visuais Estilo Mobills
st.set_page_config(page_title="Gestor Financeiro Pro", page_icon="💰", layout="wide")

# CSS para interface Dark Mode e cartões arredondados
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 30px; font-weight: bold; color: #1E90FF; }
    [data-testid="stMetricLabel"] { font-size: 14px; color: #888888; }
    .stForm {
        border-radius: 15px;
        padding: 25px;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Banco de Dados Local (Arquivo CSV)
DB_FILE = "dados_financeiros.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE).to_dict('records')
        except:
            return []
    return []

def salvar_dados(dados):
    try:
        pd.DataFrame(dados).to_csv(DB_FILE, index=False)
    except:
        st.error("Erro de segurança ao gravar arquivo.")

# Inicialização do sistema
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

# --- CABEÇALHO ---
st.title("💰 Registro de Ganhos")

# --- DASHBOARD DE MÉTRICAS ---
if st.session_state.dados:
    df_dash = pd.DataFrame(st.session_state.dados)
    
    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1:
        st.metric("Total Acumulado", f"R$ {df_dash['Total Final (R$)'].sum():.0f}")
    with c_m2:
        st.metric("Média/Serviço", f"R$ {df_dash['Total Final (R$)'].mean():.0f}")
    with c_m3:
        st.metric("KM Base Total", f"{df_dash['KM Base'].sum()} km")
    with c_m4:
        st.metric("Horas Líquidas", f"{df_dash['Horas Líquidas'].sum():.1f}h")

    st.divider()

    # --- GRÁFICOS ---
    col_g1, col_g2 = st.columns([1, 2])
    
    with col_g1:
        # Gráfico de Anel (Fator de Ganhos)
        dados_rosca = {
            'Categoria': ['Horas Líquidas', 'KM Base'],
            'Valores': [df_dash['Horas Líquidas'].sum(), df_dash['KM Base'].sum()]
        }
        fig_rosca = px.pie(dados_rosca, values='Valores', names='Categoria', hole=.5,
                          color_discrete_sequence=['#2ecc71', '#3498db'])
        fig_rosca.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_rosca, use_container_width=True)

    with col_g2:
        # Gráfico de Evolução
        fig_evol = px.area(df_dash, x='Data', y='Total Final (R$)', title="Evolução do Faturamento")
        fig_evol.update_layout(height=250, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_evol, use_container_width=True)

# --- CONFIGURAÇÕES NA BARRA LATERAL ---
st.sidebar.header("⚙️ Configurações")
VALOR_HORA = st.sidebar.number_input("Valor por Hora (R$)", value=30.0)
VALOR_ACIONAMENTO = st.sidebar.number_input("Valor Acionamento (R$)", value=220.0)
VALOR_KM_FIXO = 1.10

# --- FORMULÁRIO DE LANÇAMENTO ---
with st.form("registro_form", clear_on_submit=True):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        data_ini = st.date_input("Data de Início")
        h_ini = st.time_input("Hora de Início", value=None)
        km_ini = st.number_input("KM Inicial", min_value=0)
    with col_f2:
        data_fim = st.date_input("Data de Término")
        h_fim = st.time_input("Hora de Término", value=None)
        km_fim = st.number_input("KM Término", min_value=0)
    
    st.divider()
    submit = st.form_submit_button("✅ SALVAR REGISTRO")

if submit:
    if h_ini is None or h_fim is None:
        st.error("Por favor, preencha os horários.")
    else:
        # Lógica de Tempo (Dedução de 3h)
        ini_dt = datetime.combine(data_ini, h_ini)
        data_fim_ok = data_ini if h_fim > h_ini else data_ini + timedelta(days=1)
        fim_dt = datetime.combine(data_fim_ok, h_fim)
        
        # 1. CÁLCULO KM: (Inicial + Final) - 50 * 1.10
        soma_km = km_ini + km_fim
        km_base = max(0, soma_km - 50)
        custo_km = km_base * VALOR_KM_FIXO
        
        # 2. CÁLCULO TEMPO: (Total - 3h) * Valor Hora
        h_brutas = (fim_dt - ini_dt).total_seconds() / 3600
        h_liq = max(0.0, h_brutas - 3.0)
        custo_tempo = h_liq * VALOR_HORA

        # 3. TOTAL FINAL
        total = VALOR_ACIONAMENTO + custo_tempo + custo_km

        novo_item = {
            'Data': data_ini.strftime('%d/%m/%Y'),
            'Início': h_ini.strftime('%H:%M'),
            'Término': h_fim.strftime('%H:%M'),
            'Horas Líquidas': round(h_liq, 2),
            'KM Base': km_base,
            'Total Final (R$)': int(total)
        }
        
        st.session_state.dados.append(novo_item)
        salvar_dados(st.session_state.dados)
        st.success(f"Adicionado! Total: R$ {int(total)}")
        st.rerun()

# --- TABELA DE RESUMO ---
if st.session_state.dados:
    st.divider()
    df_final = pd.DataFrame(st.session_state.dados)
    st.dataframe(df_final, use_container_width=True, hide_index=True)

    # Exportação
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False)
    st.download_button("📥 Baixar Excel", output.getvalue(), "Relatorio.xlsx")
