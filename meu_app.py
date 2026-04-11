import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import os

# Configuração da página
st.set_page_config(page_title="Sistema Financeiro", page_icon="💰")

# Banco de Dados para persistência
DB_FILE = "dados_financeiros.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE).to_dict('records')
        except:
            return []
    return []

def salvar_dados(dados):
    pd.DataFrame(dados).to_csv(DB_FILE, index=False)

# Inicialização do histórico
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

st.title("Registro de Ganhos")

# Barra Lateral
st.sidebar.header("Configurações")
VALOR_HORA = st.sidebar.number_input("Valor por Hora (R$)", value=30.0)
VALOR_ACIONAMENTO = st.sidebar.number_input("Valor Acionamento (R$)", value=220.0)
VALOR_KM_UNITARIO = 1.10

# Formulário (Design Clássico)
with st.form("registro_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data de Início")
        hora_inicio = st.time_input("Hora de Início", value=None)
    with col2:
        data_fim = st.date_input("Data de Término")
        hora_fim = st.time_input("Hora de Término", value=None)
    
    st.divider()
    
    col_km1, col_km2 = st.columns(2)
    with col_km1:
        km_inicial = st.number_input("KM Inicial", min_value=0, step=1)
    with col_km2:
        km_final = st.number_input("KM Término", min_value=0, step=1)
        
    submit = st.form_submit_button("Adicionar Registro")

if submit:
    if hora_inicio is None or hora_fim is None:
        st.error("Por favor, preencha o horário de início e término.")
    else:
        # Lógica de Tempo (Dedução de 3h)
        inicio_dt = datetime.combine(data_inicio, hora_inicio)
        data_fim_ajustada = data_inicio if hora_fim > hora_inicio else data_inicio + timedelta(days=1)
        fim_dt = datetime.combine(data_fim_ajustada, hora_fim)
        
        if fim_dt <= inicio_dt:
            st.error("Erro: A data de término deve ser posterior à de início.")
        else:
            # Regra KM: (Inicial + Final) - 50 * 1.10
            soma_km = km_inicial + km_final
            km_calculado = max(0, soma_km - 50)
            custo_km = km_calculado * VALOR_KM_UNITARIO
            
            # Regra Tempo: Total - 3h * Valor Hora
            diferenca_bruta = (fim_dt - inicio_dt).total_seconds() / 3600
            horas_liquidas = max(0.0, diferenca_bruta - 3.0)
            custo_tempo = horas_liquidas * VALOR_HORA

            # Total Final
            total_ganho = VALOR_ACIONAMENTO + custo_tempo + custo_km

            # Registro dos dados
            novo_item = {
                'Data': data_inicio.strftime('%d/%m/%Y'),
                'Início': hora_inicio.strftime('%H:%M'),
                'Término': hora_fim.strftime('%H:%M'),
                'Horas Líquidas': round(horas_liquidas, 2),
                'Soma KM': soma_km,
                'KM Base': km_calculado,
                'Total Final (R$)': int(total_ganho)
            }
            
            st.session_state.dados.append(novo_item)
            salvar_dados(st.session_state.dados)
            st.success(f"Registro adicionado! Total: R$ {int(total_ganho)}")

# Exibição da Tabela
if st.session_state.dados:
    df = pd.DataFrame(st.session_state.dados)
    st.divider()
    st.subheader("Resumo")
    st.dataframe(df, use_container_width=True)

    # Exportação Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button(
        label="Baixar Excel",
        data=output.getvalue(),
        file_name="Relatorio_Financeiro.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
