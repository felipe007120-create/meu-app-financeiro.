import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import os

# --- CONFIGURAÇÕES DE SEGURANÇA E PÁGINA ---
st.set_page_config(page_title="Sistema Financeiro", page_icon="💰")

# Banco de dados local para prevenir perda de dados
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

# Inicialização do banco de dados na memória
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

st.title("Registro de Ganhos")

# --- BARRA LATERAL (ONDE VOCÊ MUDA OS VALORES) ---
st.sidebar.header("Configurações")

# Aqui você muda os valores padrão (30.0 e 220.0) se quiser que o app já abra diferente
VALOR_HORA = st.sidebar.number_input("Valor por Hora (R$)", value=30.0)
VALOR_ACIONAMENTO = st.sidebar.number_input("Valor Acionamento (R$)", value=220.0)
VALOR_KM_UNITARIO = 1.10

# --- FORMULÁRIO DE ENTRADA (DESIGN CLÁSSICO) ---
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

# --- LÓGICA DE CÁLCULO SEGURA ---
if submit:
    if hora_inicio is None or hora_fim is None:
        st.error("Por favor, preencha o horário de início e término.")
    else:
        # Lógica de Tempo (Dedução de 3h conforme sua regra)
        inicio_dt = datetime.combine(data_inicio, hora_inicio)
        # Ajuste inteligente para trabalho que vira a noite
        data_fim_ajustada = data_inicio if hora_fim > hora_inicio else data_inicio + timedelta(days=1)
        fim_dt = datetime.combine(data_fim_ajustada, hora_fim)
        
        if fim_dt <= inicio_dt:
            st.error("Erro: A data de término deve ser posterior à de início.")
        else:
            # 1. REGRA KM: (Inicial + Término) - 50, multiplicado por 1.10
            soma_km = km_inicial + km_final
            km_calculado = max(0, soma_km - 50)
            custo_km = km_calculado * VALOR_KM_UNITARIO
            
            # 2. REGRA TEMPO: Total de horas menos 3 horas
            segundos_totais = (fim_dt - inicio_dt).total_seconds()
            horas_brutas = segundos_totais / 3600
            horas_liquidas = max(0.0, horas_brutas - 3.0)
            custo_tempo = horas_liquidas * VALOR_HORA

            # 3. TOTAL FINAL (Acionamento + Tempo + KM)
            total_ganho = VALOR_ACIONAMENTO + custo_tempo + custo_km

            # Criar o registro para salvar
            novo_item = {
                'Data': data_inicio.strftime('%d/%m/%Y'),
                'Início': hora_inicio.strftime('%H:%M'),
                'Término': hora_fim.strftime('%H:%M'),
                'Horas Líquidas': round(horas_liquidas, 2),
                'Soma KM': soma_km,
                'KM Base': km_calculado,
                'Total Final (R$)': int(total_ganho)
            }
            
            # Salvar no banco de dados e na memória
            st.session_state.dados.append(novo_item)
            salvar_dados(st.session_state.dados)
            st.success(f"Registro adicionado com sucesso! Total: R$ {int(total_ganho)}")

# --- EXIBIÇÃO DA TABELA ---
if st.session_state.dados:
    df = pd.DataFrame(st.session_state.dados)
    st.divider()
    st.subheader("Resumo")
    
    # Tabela com largura total da tela
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Botão de Exportação para Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button(
        label="Baixar Excel",
        data=output.getvalue(),
        file_name=f"Relatorio_{datetime.now().strftime('%d_%m')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
