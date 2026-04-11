import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# Configuração da página
st.set_page_config(page_title="Sistema Financeiro", page_icon="💰")

# Inicialização do histórico
if 'dados' not in st.session_state:
    st.session_state.dados = []

st.title("💰 Registro de Ganhos")

# Barra Lateral
st.sidebar.header("⚙️ Configurações")
VALOR_HORA = st.sidebar.number_input("Valor por Hora (R$)", value=30.0)
VALOR_ACIONAMENTO = st.sidebar.number_input("Valor Acionamento (R$)", value=220.0)
VALOR_KM = st.sidebar.number_input("Valor por KM (R$)", value=1.20)

# Formulário
with st.form("registro_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data de Início")
        hora_inicio = st.time_input("Hora de Início", value=datetime.strptime("08:00", "%H:%M").time())
    with col2:
        data_fim = st.date_input("Data de Término")
        hora_fim = st.time_input("Hora de Término", value=datetime.strptime("17:00", "%H:%M").time())
    
    km_rodados = st.number_input("🚗 KM rodados", min_value=0.0, step=0.1)
    submit = st.form_submit_button("✅ Adicionar Registro")

if submit:
    inicio_dt = datetime.combine(data_inicio, hora_inicio)
    fim_dt = datetime.combine(data_fim, hora_fim)
    
    if fim_dt <= inicio_dt:
        st.error("Erro: A data de término deve ser posterior à de início.")
    else:
        diferenca_bruta = fim_dt - inicio_dt
        diferenca_final = diferenca_bruta - timedelta(hours=3)
        horas_decimais = max(0.0, diferenca_final.total_seconds() / 3600)

        custo_tempo = horas_decimais * VALOR_HORA
        custo_km = km_rodados * VALOR_KM
        total_ganho = VALOR_ACIONAMENTO + custo_tempo + custo_km

        st.session_state.dados.append({
            'Início': inicio_dt.strftime('%d/%m/%Y %H:%M'),
            'Término': fim_dt.strftime('%d/%m/%Y %H:%M'),
            'Horas Líquidas': round(horas_decimais, 2),
            'KM': km_rodados,
            'Base (R$)': VALOR_ACIONAMENTO,
            'Custo Tempo (R$)': round(custo_tempo, 2),
            'Custo KM (R$)': round(custo_km, 2),
            'Total Final (R$)': round(total_ganho, 2)
        })
        st.success(f"Registro adicionado! Total: R$ {total_ganho:.2f}")

if st.session_state.dados:
    df = pd.DataFrame(st.session_state.dados)
    st.divider()
    st.subheader("📊 Resumo")
    st.dataframe(df, use_container_width=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button(
        label=" Baixar Excel",
        data=output.getvalue(),
        file_name="Relatorio_Financeiro.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
