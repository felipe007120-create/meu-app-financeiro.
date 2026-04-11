import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import plotly.express as px

# 1. Configurações Visuais de Nível Profissional (Inspirado no App)
st.set_page_config(page_title="Meus Ganhos Pro", page_icon="💰", layout="wide")

# Estilização CSS para imitar o visual do app
st.markdown("""
    <style>
    /* Cor de fundo e textos */
    [data-testid="stSidebar"] {background-color: #f0f2f6;}
    [data-testid="stAppViewContainer"] {background-color: #FFFFFF;}
    
    /* Configuração dos Cartões de Métrica */
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; color: #1E90FF; }
    [data-testid="stMetricLabel"] { font-size: 16px; color: #555555; }
    
    /* Customização do cabeçalho */
    h1 { color: #333333; }
    
    /* Borda e fundo arredondado para o formulário */
    .stForm {
        border-radius: 20px;
        padding: 20px;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Inicialização do histórico
if 'dados' not in st.session_state:
    st.session_state.dados = []

# --- TÍTULO DO PAINEL (DASHBOARD) ---
st.title("💰 Gestor de Ganhos")

# Se houver dados, mostramos os gráficos (Vimos que isso estava travando antes)
if st.session_state.dados:
    df_dashboard = pd.DataFrame(st.session_state.dados)
    
    # --- ÁREA DAS MÉTRICAS (Igual aos cartões do app) ---
    col_metric1, col_metric2, col_metric3 = st.columns(3)
    
    with col_metric1:
        total_ganho_acumulado = df_dashboard['Total Final (R$)'].sum()
        st.metric("Total Acumulado", f"R$ {total_ganho_acumulado:.0f}")
        
    with col_metric2:
        media_ganho = df_dashboard['Total Final (R$)'].mean()
        st.metric("Média por Acionamento", f"R$ {media_ganho:.0f}")
        
    with col_metric3:
        # Mostra o ganho mais alto
        melhor_ganho = df_dashboard['Total Final (R$)'].max()
        st.metric("Melhor Ganho", f"R$ {melhor_ganho:.0f}")

    st.divider()

    # --- ÁREA DOS GRÁFICOS (Inspirado na imagem) ---
    st.subheader("📊 Análise de Desempenho")
    col_graph1, col_graph2 = st.columns([1, 1.5]) # Gráfico menor e maior

    with col_graph1:
        # Gráfico 1: Anel de Horas vs KM (Inspirado no anel colorido)
        df_pizza = df_dashboard.groupby('Data')[['Horas Líquidas', 'KM Base']].sum().reset_index()
        # Preparamos os dados para uma pizza
        df_pizza_long = df_pizza.melt(id_vars='Data', value_vars=['Horas Líquidas', 'KM Base'], 
                                    var_name='Tipo', value_name='Valor')
        
        # Cores iguais às do app (Verde, Vermelho, Amarelo)
        fig_donut = px.pie(df_pizza_long, values='Valor', names='Tipo', hole=.5,
                          title="Fator de Ganhos",
                          color_discrete_sequence=['#28a745', '#dc3545', '#ffc107'])
        
        # Ajustes de visual
        fig_donut.update_traces(textposition='inside', textinfo='percent+label')
        fig_donut.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_graph2:
        # Gráfico 2: Evolução dos Ganhos no Tempo (Inspirado nas barras/linhas)
        fig_evolucao = px.bar(df_dashboard, x='Data', y='Total Final (R$)',
                             title="Evolução do Faturamento (Por Serviço)",
                             color='Total Final (R$)',
                             color_continuous_scale=px.colors.sequential.Teal)
        
        fig_evolucao.update_layout(margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_evolucao, use_container_width=True)

    st.divider()

# --- ÁREA DE LANÇAMENTO (Ficou limpo e arredondado) ---
st.subheader("📝 Adicionar Novo Serviço")
with st.form("registro_form_moderno", clear_on_submit=True):
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        st.markdown("### 📅 Período")
        data_inicio = st.date_input("Data de Início")
        hora_inicio = st.time_input("Hora de Início", value=datetime.strptime("08:00", "%H:%M").time())
    with col_input2:
        st.markdown("### 🕒 Horários")
        data_fim = st.date_input("Data de Término")
        hora_fim = st.time_input("Hora de Término", value=datetime.strptime("17:00", "%H:%M").time())
    
    st.divider()
    
    col_km1, col_km2 = st.columns(2)
    with col_km1:
        st.markdown("### 🚗 Quilometragem")
        km_inicial = st.number_input("KM Inicial (Painel)", min_value=0, step=1)
    with col_km2:
        st.markdown("### ") # Espaço para alinhar
        km_final = st.number_input("KM Término (Painel)", min_value=0, step=1)
        
    # Botão Verde e Centralizado como no app
    submit_central = st.columns([1, 1, 1])
    with submit_central[1]: # Coluna do meio
        submit = st.form_submit_button("✅ SALVAR REGISTRO")

# --- LÓGICA DE CÁLCULO (Isso travou na linha 77 antes, mas agora está limpo) ---
if submit:
    if hora_inicio is None or hora_fim is None:
        st.error("Por favor, preencha o horário de início e término.")
    else:
        # Lógica de Tempo (Regra: (Total - 3h) * R$30)
        inicio_dt = datetime.combine(data_inicio, hora_inicio)
        # Lógica para virada de dia/noite
        data_fim_ajustada = data_inicio if hora_fim > hora_inicio else data_inicio + timedelta(days=1)
        fim_dt = datetime.combine(data_fim_ajustada, hora_fim)
        
        if fim_dt <= inicio_dt:
            st.error("Erro: A data de término deve ser posterior à de início.")
        else:
            # Regra KM: (Inicial + Final) - 50, multiplicado por 1.10
            soma_km = km_inicial + km_final
            km_calculado = max(0, soma_km - 50)
            cost_km = km_calculado * 1.10
            
            # Regra Tempo: Total - 3 horas
            segundos_totais = (fim_dt - inicio_dt).total_seconds()
            horas_brutas = segundos_totais / 3600
            horas_liquidas = max(0.0, horas_brutas - 3.0)
            cost_tempo = horas_liquidas * 30.0 # R$30 fixo

            # Total Final (Acionamento de R$220 + Tempo + KM)
            total_ganho = 220.0 + cost_tempo + cost_km

            # Criar o registro
            novo_item = {
                'Data': data_inicio.strftime('%d/%m/%Y'),
                'Horas Totais': round(horas_brutas, 2),
                'Horas Líquidas': round(horas_liquidas, 2),
                'Soma KM': soma_km,
                'KM Base Cálculo': km_calculado,
                'Total Final (R$)': int(total_ganho)
            }
            
            # Salvar no histórico
            st.session_state.dados.append(novo_item)
            st.success(f"Registro adicionado! Total: R$ {int(total_ganho)}")
            st.rerun() # Atualiza a página para mostrar os gráficos

# --- EXIBIÇÃO DA TABELA ---
if st.session_state.dados:
    st.divider()
    st.subheader("📑 Histórico Completo")
    df_tabela = pd.DataFrame(st.session_state.dados)
    
    # Exibe a tabela de forma limpa, sem o índice
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    # Botão de Exportação para Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_tabela.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Baixar Excel",
        data=output.getvalue(),
        file_name=f"Relatorio_{datetime.now().strftime('%d_%m')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
