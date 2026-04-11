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

# Barra Lateral - Valores que você pode ajustar conforme o contrato
st.sidebar.header("⚙️ Configurações de Taxas")
VALOR_HORA = st.sidebar.number_input("Valor por Hora (R$)", value=30.0)
VALOR_ACIONAMENTO = st.sidebar.number_input("Valor Acionamento (R$)", value=220.0)
VALOR_KM = st.sidebar.number_input("Valor por KM (R$)", value=1.20)

# Formulário de Entrada
with st.form("registro_form", clear_on_submit=True):
    st.subheader("📝 Novo Lançamento")
    
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
        km_inicial = st.number_input("🚗 KM Inicial", min_value=0, step=1)
    with col_km2:
        km_final = st.number_input("🏁 KM Final", min_value=0, step=1)
        
    submit = st.form_submit_button("✅ Calcular e Salvar Registro")

if submit:
    if hora_inicio is None or hora_fim is None:
        st.error("⚠️ Por favor, preencha os horários de início e término.")
    else:
        # Combinar data e hora para lidar com viradas de dia (trabalho noturno)
        inicio_dt = datetime.combine(data_inicio, hora_inicio)
        fim_dt = datetime.combine(data_fim, hora_fim)
        
        if fim_dt <= inicio_dt:
            st.error("❌ Erro: O término deve ser depois do início.")
        elif km_final < km_inicial:
            st.error("❌ Erro: O KM final não pode ser menor que o inicial.")
        else:
            # 1. Cálculo de KM (Número Inteiro)
            km_total = int(km_final - km_inicial)
            
            # 2. Cálculo de Tempo Bruto
            diferenca_bruta = fim_dt - inicio_dt
            
            # 3. Regra de Subtrair 3 horas (Dedução solicitada)
            diferenca_com_deducao = diferenca_bruta - timedelta(hours=3)
            
            # Garante que as horas não fiquem negativas se trabalhar menos de 3h
            horas_liquidas = max(0.0, diferenca_com_deducao.total_seconds() / 3600)

            # 4. Cálculos Financeiros
            custo_tempo = horas_liquidas * VALOR_HORA
            custo_km = km_total * VALOR_KM
            total_ganho = VALOR_ACIONAMENTO + custo_tempo + custo_km

            # Adicionar ao histórico na memória do navegador
            st.session_state.dados.append({
                'Data': inicio_dt.strftime('%d/%m/%Y'),
                'Início': inicio_dt.strftime('%H:%M'),
                'Término': fim_dt.strftime('%H:%M'),
                'Horas Totais': round(diferenca_bruta.total_seconds() / 3600, 2),
                'Horas Líquidas (-3h)': round(horas_liquidas, 2),
                'KM': km_total,
                'Total Final (R$)': int(total_ganho) # Salva como número inteiro
            })
            
            st.balloons()
            st.success(f"Registro Adicionado! Total: R$ {int(total_ganho)}")

# Exibição dos Resultados
if st.session_state.dados:
    df = pd.DataFrame(st.session_state.dados)
    st.divider()
    st.subheader("📊 Resumo dos Ganhos")
    
    # Mostra a tabela
    st.dataframe(df, use_container_width=True)

    # Lógica para exportar para Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Baixar Relatório em Excel",
        data=output.getvalue(),
        file_name=f"Relatorio_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
