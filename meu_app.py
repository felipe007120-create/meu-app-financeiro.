import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import os

# 1. Configurações Visuais de Nível Profissional
st.set_page_config(page_title="Gestor Financeiro Pro", page_icon="📈", layout="wide")

# Estilo para os cartões de métricas
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 35px; color: #00FF00; }
    [data-testid="stMetricLabel"] { font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Banco de Dados Local (Arquivo CSV)
DB_FILE = "historico_ganhos.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE).to_dict('records')
        except:
            return []
    return []

def salvar_dados(dados):
    pd.DataFrame(dados).to_csv(DB_FILE, index=False)

# Inicialização do estado do sistema
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

# --- CABEÇALHO E DASHBOARD ---
st.title("📊 Gestor de Produtividade e Ganhos")

if st.session_state.dados:
    df_resumo = pd.DataFrame(st.session_state.dados)
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Faturamento Total", f"R$ {df_resumo['Total Final (R$)'].sum():.0f}")
    with col_m2:
        st.metric("Média por Saída", f"R$ {df_resumo['Total Final (R$)'].mean():.0f}")
    with col_m3:
        st.metric("Total KM Base", f"{df_resumo['KM Base Cálculo'].sum()} km")
    with col_m4:
        st.metric("Total Horas Líquidas", f"{df_resumo['Horas Líquidas'].sum():.1f}h")

st.divider()

# --- ÁREA DE LANÇAMENTO ---
with st.expander("➕ REGISTRAR NOVO ACIONAMENTO", expanded=not st.session_state.dados):
    with st.form("form_pro", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("### 🕒 Horários")
            data_ini = st.date_input("Data do Serviço", value=datetime.now())
            h_ini = st.time_input("Hora de Início", value=None)
            h_fim = st.time_input("Hora de Término", value=None)
            
        with col_b:
            st.markdown("### 🛣️ Quilometragem")
            km_ini = st.number_input("KM Inicial (Painel)", min_value=0, step=1)
            km_fim = st.number_input("KM Término (Painel)", min_value=0, step=1)
        
        st.divider()
        btn_salvar = st.form_submit_button("💾 SALVAR E CALCULAR REGISTRO")

if btn_salvar:
    if not h_ini or not h_fim:
        st.error("⚠️ Por favor, preencha todos os horários.")
    elif km_fim < 0: # Caso queira validar se os KMs foram preenchidos
        st.error("⚠️ Preencha os valores de KM.")
    else:
        # Combinando Datas e Horas
        ini = datetime.combine(data_ini, h_ini)
        # Lógica para caso o serviço termine no dia seguinte (meia-noite)
        data_fim_ajustada = data_ini if h_fim > h_ini else data_ini + timedelta(days=1)
        fim = datetime.combine(data_fim_ajustada, h_fim)
        
        # --- CÁLCULO DE KM (REGRA: (INICIAL + FINAL) - 50) * 1.10 ---
        soma_km = km_ini + km_fim
        km_calculado = max(0, soma_km - 50)
        valor_km_total = km_calculado * 1.10
        
        # --- CÁLCULO DE TEMPO (REGRA: (TOTAL - 3H) * 30) ---
        segundos_totais = (fim - ini).total_seconds()
        horas_brutas = segundos_totais / 3600
        horas_liq = max(0.0, horas_brutas - 3.0)
        valor_tempo_total = horas_liq * 30.0
        
        # --- TOTAL FINAL (BASE 220 + TEMPO + KM) ---
        total_final = 220.0 + valor_tempo_total + valor_km_total
        
        # Criando o registro
        novo_registro = {
            'Data': data_ini.strftime('%d/%m/%Y'),
            'Horas Brutas': round(horas_brutas, 2),
            'Horas Líquidas': round(horas_liq, 2),
            'Soma KM': soma_km,
            'KM Base Cálculo': km_calculado,
            'Valor KM (R$)': round(valor_km_total, 2),
            'Total Final (R$)': int(total_final)
        }
        
        st.session_state.dados.append(novo_registro)
        salvar_dados(st.session_state.dados)
        st.success(f"✅ Sucesso! Total de R$ {int(total_final)} adicionado ao dashboard.")
        st.rerun()

# --- TABELA DE HISTÓRICO ---
if st.session_state.dados:
    st.subheader("📑 Detalhamento dos Registros")
    df_visual = pd.DataFrame(st.session_state.dados)
    
    # Exibe a tabela de forma limpa
    st.dataframe(df_visual, use_container_width=True)

    # Botão de Exportação para Excel Profissional
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_visual.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Baixar Relatório para Auditoria",
        data=output.getvalue(),
        file_name=f"Relatorio_Ganhos_{datetime.now().strftime('%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Rodapé profissional
st.markdown("---")
st.caption(f"Sistema Gerencial v3.0 | Atualizado em {datetime.now().strftime('%d/%m/%Y')}")
