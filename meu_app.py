import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import os
import re

# 1. Configurações de Segurança e Interface
st.set_page_config(page_title="Sistema Seguro v4.0", page_icon="🛡️", layout="wide")

# Bloqueio visual de erros internos (mostra apenas o necessário)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# 2. Gerenciamento Seguro de Arquivos
DB_FILE = "dados_protegidos.csv"

def carregar_dados_seguro():
    """Carrega dados tratando possíveis corrupções de arquivo."""
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE).to_dict('records')
        except Exception:
            return []
    return []

def salvar_dados_seguro(dados):
    """Salva dados garantindo que apenas o necessário seja escrito."""
    try:
        df = pd.DataFrame(dados)
        # Sanitização: remove caracteres que podem injetar código em planilhas
        df = df.replace(r'[=+\-@]', '', regex=True)
        df.to_csv(DB_FILE, index=False)
    except Exception as e:
        st.error("Erro interno ao salvar. Contate o administrador.")

# Inicialização
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados_seguro()

# --- INTERFACE ---
st.title("🛡️ Gestão Financeira Protegida")

# Dashboard de Métricas (Apenas Leitura)
if st.session_state.dados:
    df_resumo = pd.DataFrame(st.session_state.dados)
    cols = st.columns(4)
    cols[0].metric("Faturamento", f"R$ {df_resumo['Total Final (R$)'].sum():.0f}")
    cols[1].metric("Saídas", len(df_resumo))
    cols[2].metric("KM Base", f"{df_resumo['KM Base Cálculo'].sum()} km")
    cols[3].metric("Horas Líq.", f"{df_resumo['Horas Líquidas'].sum():.1f}h")

st.divider()

# --- FORMULÁRIO COM VALIDAÇÃO DE ENTRADA (ANTI-HACK) ---
with st.expander("🔐 NOVO LANÇAMENTO SEGURO", expanded=not st.session_state.dados):
    with st.form("form_secure", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            data_ini = st.date_input("Data do Serviço")
            h_ini = st.time_input("Início", value=None)
            h_fim = st.time_input("Término", value=None)
        with c2:
            # Proteção contra números absurdos ou negativos
            km_ini = st.number_input("KM Inicial", min_value=0, max_value=999999)
            km_fim = st.number_input("KM Término", min_value=0, max_value=999999)
        
        btn_salvar = st.form_submit_button("VALIDAR E SALVAR")

if btn_salvar:
    # Validação Robusta de Entradas
    if not h_ini or not h_fim:
        st.warning("Preencha todos os campos de horário.")
    elif km_fim < 0 or km_ini < 0:
        st.error("Valores de KM inválidos detectados.")
    else:
        # Lógica de Cálculo Protegida
        ini = datetime.combine(data_ini, h_ini)
        data_fim_ajustada = data_ini if h_fim > h_ini else data_ini + timedelta(days=1)
        fim = datetime.combine(data_fim_ajustada, h_fim)
        
        # Regra KM: (Ini + Fim) - 50 * 1.10
        soma_km = km_ini + km_fim
        km_calculado = max(0, soma_km - 50)
        
        # Regra Tempo: (Total - 3h) * 30
        horas_brutas = (fim - ini).total_seconds() / 3600
        horas_liq = max(0.0, horas_brutas - 3.0)
        
        # Total Final
        total_f = 220.0 + (horas_liq * 30.0) + (km_calculado * 1.10)
        
        novo_reg = {
            'Data': data_ini.strftime('%Y-%m-%d'),
            'Horas Líquidas': round(horas_liq, 2),
            'KM Base Cálculo': int(km_calculado),
            'Total Final (R$)': int(total_f),
            'Timestamp': datetime.now().strftime('%H:%M:%S') # Auditoria
        }
        
        st.session_state.dados.append(novo_reg)
        salvar_dados_seguro(st.session_state.dados)
        st.success("Registro validado e armazenado com sucesso.")
        st.rerun()

# --- VISUALIZAÇÃO SEGURA ---
if st.session_state.dados:
    df_vis = pd.DataFrame(st.session_state.dados)
    st.subheader("📑 Registros Auditados")
    st.dataframe(df_vis, use_container_width=True, hide_index=True)

    # Exportação Segura
    csv = df_vis.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Backup de Segurança (CSV)",
        data=csv,
        file_name=f"backup_financeiro_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
