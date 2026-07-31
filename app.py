import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np
import altair as alt

# --- 1. Configuração e Carregamento de Recursos ---
# O caminho para a sua pasta 'data' no repositório GitHub
# ATENÇÃO: Este caminho é relativo à raiz do seu repositório no Streamlit Cloud
data_path = 'data'

# Caminho completo para o arquivo do modelo XGBoost
model_path = os.path.join(data_path, 'xgboost_model.pkl')

# Caminho completo para o arquivo de dados processado
input_file_name = 'ruf_consolidado_fe.xlsx'
input_file_path = os.path.join(data_path, input_file_name)

ufpe_exact_name = 'Universidade Federal de Pernambuco'
target_column = 'Ranking'

# --- Mapeamento de Edições para Anos ---
EDITION_YEAR_MAP = {
    1: 2017,
    2: 2018,
    3: 2019,
    4: 2023, # Assumindo que houve um gap e a Edição 4 foi em 2023
    5: 2024,
    6: 2025,
    7: 2026  # Edição simulada
}

# Função auxiliar para obter o ano da edição
def get_year_from_edition(edition_number):
    return EDITION_YEAR_MAP.get(edition_number, f"Ano Desconhecido (Edição {edition_number})")


# --- Funções de Carregamento (com cache para Streamlit) ---

@st.cache_resource # Usa o cache do Streamlit para carregar o modelo apenas uma vez
def load_model(path):
    try:
        model = joblib.load(path)
        return model
    except Exception as e:
        st.error(f"Erro ao carregar o modelo: {e}. Verifique se o arquivo '{os.path.basename(path)}' está na pasta 'data' do seu repositório e se não está corrompido.")
        st.exception(e) # Exibe o traceback completo
        st.stop() # Para a execução do app
        return None

@st.cache_data # Usa o cache do Streamlit para carregar os dados apenas uma vez
def load_data(path):
    try:
        df = pd.read_excel(path)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}. Verifique se o arquivo '{os.path.basename(path)}' está na pasta 'data' do seu repositório e se não está corrompido.")
        st.exception(e) # Exibe o traceback completo
        st.stop() # Para a execução do app
        return pd.DataFrame()

# --- NOVO: Função de Simulação ---
def simulate_full_ranking_avg_trend(df_base_edicao_6, model, ufpe_name, all_universities_average_trends,
                                    pct_change_ensino, pct_change_pesquisa, pct_change_mercado,
                                    pct_change_inovacao, pct_change_internacionalizacao,
                                    apply_other_uni_trends):

    df_simulated_edicao = df_base_edicao_6.copy()

    notas_cols_base_list = ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']

    ufpe_pct_changes = {
        'Nota em Ensino': pct_change_ensino,
        'Nota em Pesquisa': pct_change_pesquisa,
        'Nota em Mercado': pct_change_mercado,
        'Nota em Inovação': pct_change_inovacao,
        'Nota em Internacionalização': pct_change_internacionalizacao
    }

    for uni_idx, uni_row in df_simulated_edicao.iterrows():
        if uni_row['Universidade'] == ufpe_name:
            for col_base, pct_change_val in ufpe_pct_changes.items():
                original_note_ufpe = uni_row[col_base]
                new_note_ufpe = original_note_ufpe * (1 + pct_change_val)
                df_simulated_edicao.loc[uni_idx, col_base] = new_note_ufpe
        else:
            if apply_other_uni_trends:
                for col_base in notas_cols_base_list:
                    col_pct_change_prev = f'{col_base}_pct_change_prev'
                    if uni_row['Universidade'] in all_universities_average_trends.index and col_pct_change_prev in all_universities_average_trends.columns:
                        trend_pct_change = all_universities_average_trends.loc[uni_row['Universidade'], col_pct_change_prev]
                    else:
                        trend_pct_change = 0.0

                    original_note_other = uni_row[col_base]
                    new_note_other = original_note_other * (1 + trend_pct_change)
                    df_simulated_edicao.loc[uni_idx, col_base] = new_note_other

        # Recalcula a Nota Geral para cada universidade após as variações
        # Assumindo que 'Nota' é a soma das notas individuais para fins de simulação
        df_simulated_edicao.loc[uni_idx, 'Nota'] = df_simulated_edicao.loc[uni_idx, notas_cols_base_list].sum()

    # Prepara os dados para o modelo
    features = ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota']

    # Verifica se todas as features existem no DataFrame simulado
    missing_features = [f for f in features if f not in df_simulated_edicao.columns]
    if missing_features:
        st.error(f"Erro: As seguintes colunas de features estão faltando no DataFrame simulado: {', '.join(missing_features)}. Verifique o arquivo de dados e o código de simulação.")
        st.stop()

    X_simulated = df_simulated_edicao[features]

    # Realiza a previsão do ranking
    try:
        predicted_ranking = model.predict(X_simulated)
        df_simulated_edicao['Simulated_Ranking'] = predicted_ranking
    except Exception as e:
        st.error(f"Erro ao realizar a previsão do ranking com o modelo: {e}. Verifique o modelo e os dados de entrada.")
        st.exception(e)
        st.stop()

    # Ordena pelo ranking simulado
    df_simulated_edicao = df_simulated_edicao.sort_values(by='Simulated_Ranking').reset_index(drop=True)
    return df_simulated_edicao


# --- INÍCIO DA EXECUÇÃO DO APP ---

# Carrega o modelo e os dados
loaded_model = load_model(model_path)
df_model = load_data(input_file_path)

# Verifica se o carregamento foi bem-sucedido
if loaded_model is None or df_model.empty:
    st.error("O aplicativo não pode continuar devido a falhas no carregamento do modelo ou dos dados.")
    st.stop()

# --- Cálculo das Tendências Médias para Outras Universidades ---
notas_cols_base = ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota']
trend_pct_change_cols = [f'{col}_pct_change_prev' for col in notas_cols_base]

try:
    # Exclui a UFPE do cálculo das tendências médias
    df_other_universities = df_model[df_model['Universidade'] != ufpe_exact_name].copy()

    # Calcula as variações percentuais para todas as edições e universidades
    for col_base in notas_cols_base:
        if col_base in df_other_universities.columns:
            df_other_universities[f'{col_base}_pct_change_prev'] = df_other_universities.groupby('Universidade')[col_base].pct_change()
        else:
            st.warning(f"Coluna '{col_base}' não encontrada para cálculo de tendência. Será ignorada.")
            df_other_universities[f'{col_base}_pct_change_prev'] = 0.0 # Cria coluna de zeros se não existir

    # Filtra as colunas de tendência que realmente existem no DataFrame
    existing_trend_pct_change_cols = [col for col in trend_pct_change_cols if col in df_other_universities.columns]

    # Calcula a média dessas variações por universidade
    average_trends = df_other_universities.groupby('Universidade')[existing_trend_pct_change_cols].mean()

    # Preenche quaisquer NaNs restantes com 0 (para universidades com histórico incompleto)
    average_trends = average_trends.fillna(0)
except Exception as e:
    st.error(f"Erro ao calcular as tendências médias de outras universidades: {e}.")
    st.exception(e)
    st.stop()


# --- Extrai dados da Edição 6 para a UFPE ---
try:
    if 'Edicao_RUF' not in df_model.columns:
        st.error("Coluna 'Edicao_RUF' não encontrada no arquivo de dados. Verifique o arquivo.")
        st.stop()

    df_edicao_6 = df_model[df_model['Edicao_RUF'] == 6].copy()
    if df_edicao_6.empty:
        st.error("Não foram encontrados dados para a Edição 6 do RUF. Verifique o arquivo de dados.")
        st.stop()

    ufpe_data_edicao_6 = df_edicao_6[df_edicao_6['Universidade'] == ufpe_exact_name]
    if ufpe_data_edicao_6.empty:
        st.error(f"A universidade '{ufpe_exact_name}' não foi encontrada na Edição 6. Verifique o nome ou os dados.")
        st.stop()

    # Extrai a linha da UFPE da Edição 6 para fácil acesso
    original_ufpe_ed6 = ufpe_data_edicao_6.iloc[0]

except Exception as e:
    st.error(f"Erro ao extrair dados da Edição 6 para a UFPE: {e}.")
    st.exception(e)
    st.stop()


# --- Título e Descrição do Aplicativo ---
st.set_page_config(layout="wide")
st.title(f"Simulador de Ranking RUF da UFPE (Edição {get_year_from_edition(7)})")
st.write("Este aplicativo permite simular o impacto de variações nas notas da UFPE nas diferentes dimensões do Ranking Universitário Folha (RUF) para a próxima edição.")

# --- Quadro Resumo da UFPE (Edição 6) ---
st.subheader(f"Situação Atual da UFPE (Edição {get_year_from_edition(6)})")
try:
    summary_df = pd.DataFrame({
        'Métrica': ['Ranking', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota Geral'],
        f'Edição {get_year_from_edition(6)}': [
            original_ufpe_ed6['Ranking'],
            original_ufpe_ed6['Nota em Ensino'],
            original_ufpe_ed6['Nota em Pesquisa'],
            original_ufpe_ed6['Nota em Mercado'],
            original_ufpe_ed6['Nota em Inovação'],
            original_ufpe_ed6['Nota em Internacionalização'],
            original_ufpe_ed6['Nota']
        ]
    })
    st.dataframe(summary_df.set_index('Métrica'), hide_index=False)
except Exception as e:
    st.error(f"Erro ao exibir o quadro resumo da UFPE: {e}. Verifique os dados da Edição 6.")
    st.exception(e)
    st.stop()


# --- Sliders de Variação para a UFPE ---
st.subheader("Defina as Variações Percentuais para a UFPE (Edição 7)")

# Inicializa st.session_state para os sliders se ainda não estiverem definidos
if "pct_ensino_display" not in st.session_state:
    st.session_state.pct_ensino_display = 0
if "pct_pesquisa_display" not in st.session_state:
    st.session_state.pct_pesquisa_display = 0
if "pct_mercado_display" not in st.session_state:
    st.session_state.pct_mercado_display = 0
if "pct_inovacao_display" not in st.session_state:
    st.session_state.pct_inovacao_display = 0
if "pct_internacionalizacao_display" not in st.session_state:
    st.session_state.pct_internacionalizacao_display = 0

col1, col2, col3 = st.columns(3)
with col1:
    pct_ensino_display = st.slider("Variação % em Ensino", -20, 20, st.session_state.pct_ensino_display, 1, format="%.0f%%", key="ensino_slider")
    pct_pesquisa_display = st.slider("Variação % em Pesquisa", -20, 20, st.session_state.pct_pesquisa_display, 1, format="%.0f%%", key="pesquisa_slider")
with col2:
    pct_mercado_display = st.slider("Variação % em Mercado", -20, 20, st.session_state.pct_mercado_display, 1, format="%.0f%%", key="mercado_slider")
    pct_inovacao_display = st.slider("Variação % em Inovação", -20, 20, st.session_state.pct_inovacao_display, 1, format="%.0f%%", key="inovacao_slider")
with col3:
    pct_internacionalizacao_display = st.slider("Variação % em Internacionalização", -20, 20, st.session_state.pct_internacionalizacao_display, 1, format="%.0f%%", key="internacionalizacao_slider")

# Converte as variações percentuais para fator (ex: 5% -> 0.05)
pct_change_ensino = pct_ensino_display / 100
pct_change_pesquisa = pct_pesquisa_display / 100
pct_change_mercado = pct_mercado_display / 100
pct_change_inovacao = pct_inovacao_display / 100
pct_change_internacionalizacao = pct_internacionalizacao_display / 100

# --- Botão para resetar os sliders ---
def reset_sliders():
    st.session_state.pct_ensino_display = 0
    st.session_state.pct_pesquisa_display = 0
    st.session_state.pct_mercado_display = 0
    st.session_state.pct_inovacao_display = 0
    st.session_state.pct_internacionalizacao_display = 0

st.button("Resetar Variações", on_click=reset_sliders)

# --- Checkbox para considerar tendências de outras universidades ---
apply_other_uni_trends = st.checkbox("Considerar tendências históricas de outras universidades", value=True, help="Se marcado, as notas das outras universidades serão ajustadas com base em suas tendências históricas. Caso contrário, suas notas permanecerão as mesmas da Edição 6.")

# --- Execução da Simulação ---
st.markdown("---")
if st.button("Executar Simulação"):
    st.subheader(f"Resultados da Simulação (Edição {get_year_from_edition(7)})")

    try:
        with st.spinner("Executando simulação..."):
            simulated_df = simulate_full_ranking_avg_trend(
                df_edicao_6, loaded_model, ufpe_exact_name, average_trends,
                pct_change_ensino, pct_change_pesquisa, pct_change_mercado,
                pct_change_inovacao, pct_change_internacionalizacao,
                apply_other_uni_trends
            )

        # Extrai os dados da UFPE simulados
        simulated_ufpe_ed7 = simulated_df[simulated_df['Universidade'] == ufpe_exact_name].iloc[0]

        # Exibe o ranking simulado da UFPE
        st.metric(label=f"Ranking Simulada da UFPE (Edição {get_year_from_edition(7)})", value=f"#{int(simulated_ufpe_ed7['Simulated_Ranking'])}")

        # Tabela comparativa
        st.subheader("Comparativo UFPE: Edição 6 (Original) vs. Edição 7 (Simulada)")
        comparison_df = pd.DataFrame({
            'Métrica': ['Ranking', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota Geral'],
            f'Edição {get_year_from_edition(6)} (Original)': [
                original_ufpe_ed6['Ranking'],
                original_ufpe_ed6['Nota em Ensino'],
                original_ufpe_ed6['Nota em Pesquisa'],
                original_ufpe_ed6['Nota em Mercado'],
                original_ufpe_ed6['Nota em Inovação'],
                original_ufpe_ed6['Nota em Internacionalização'],
                original_ufpe_ed6['Nota']
            ],
            f'Edição {get_year_from_edition(7)} (Simulada)': [
                simulated_ufpe_ed7['Simulated_Ranking'],
                simulated_ufpe_ed7['Nota em Ensino'],
                simulated_ufpe_ed7['Nota em Pesquisa'],
                simulated_ufpe_ed7['Nota em Mercado'],
                simulated_ufpe_ed7['Nota em Inovação'],
                simulated_ufpe_ed7['Nota em Internacionalização'],
                simulated_ufpe_ed7['Nota']
            ]
        })

        # Adiciona a coluna de Diferença
        comparison_df['Diferença'] = comparison_df[f'Edição {get_year_from_edition(7)} (Simulada)'] - comparison_df[f'Edição {get_year_from_edition(6)} (Original)']
        ranking_diff_idx = comparison_df[comparison_df['Métrica'] == 'Ranking'].index
        if not ranking_diff_idx.empty:
            comparison_df.loc[ranking_diff_idx, 'Diferença'] = -comparison_df.loc[ranking_diff_idx, 'Diferença']

        st.dataframe(comparison_df.set_index('Métrica'), hide_index=False)

        # Gráfico de Barras para Comparativo de Notas
        st.markdown("---")
        st.subheader("Comparativo Gráfico de Notas (Edição 6 vs. Edição 7 Simulada)")

        chart_data = pd.DataFrame({
            'Métrica': ['Ensino', 'Pesquisa', 'Mercado', 'Inovação', 'Internacionalização', 'Geral'],
            f'Edição {get_year_from_edition(6)}': [
                original_ufpe_ed6['Nota em Ensino'],
                original_ufpe_ed6['Nota em Pesquisa'],
                original_ufpe_ed6['Nota em Mercado'],
                original_ufpe_ed6['Nota em Inovação'],
                original_ufpe_ed6['Nota em Internacionalização'],
                original_ufpe_ed6['Nota']
            ],
            f'Edição {get_year_from_edition(7)} (Simulada)': [
                simulated_ufpe_ed7['Nota em Ensino'],
                simulated_ufpe_ed7['Nota em Pesquisa'],
                simulated_ufpe_ed7['Nota em Mercado'],
                simulated_ufpe_ed7['Nota em Inovação'],
                simulated_ufpe_ed7['Nota em Internacionalização'],
                simulated_ufpe_ed7['Nota']
            ]
        })

        chart_data_melted = chart_data.melt('Métrica', var_name='Edição', value_name='Nota')

        chart = alt.Chart(chart_data_melted).mark_bar().encode(
            x=alt.X('Métrica', axis=alt.Axis(title='Dimensão da Nota')),
            y=alt.Y('Nota', axis=alt.Axis(title='Valor da Nota')),
            color=alt.Color('Edição', title='Edição RUF'),
            tooltip=['Métrica', 'Edição', 'Nota']
        ).properties(
            title='Notas da UFPE por Dimensão'
        ).interactive()

        st.altair_chart(chart, use_container_width=True)

    except Exception as e:
        st.error(f"Ocorreu um erro durante a execução da simulação: {e}.")
        st.exception(e)
        st.stop()

st.markdown("---")
st.info("Este simulador utiliza um modelo de Machine Learning treinado com dados históricos do RUF para prever o ranking. As previsões são estimativas e não garantem resultados futuros.")
