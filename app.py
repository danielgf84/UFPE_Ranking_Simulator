# app.py
import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np
import altair as alt

# Importa as funções e variáveis do model_logic.py
# Renomeia as funções para evitar conflitos com os decoradores @st.cache_...
from model_logic import (
    load_model as ml_load_model,
    load_data as ml_load_data,
    simulate_full_ranking_avg_trend,
    calculate_average_trends,
    ufpe_exact_name,
    target_column,
    EDITION_YEAR_MAP,
    get_year_from_edition
)

# --- Configuração da Página Streamlit ---
st.set_page_config(layout="wide", page_title="Simulador de Ranking RUF para a UFPE")

# --- Definir Caminhos do Projeto para o ambiente de execução (GitHub/Streamlit Cloud) ---
# __file__ é o caminho para o arquivo app.py.
# os.path.dirname(__file__) retorna o diretório onde app.py está (a raiz do repositório).
PROJECT_BASE_PATH = os.path.dirname(__file__)

# Assumindo que 'data' e 'models' são subpastas na raiz do repositório
DATA_PATH = os.path.join(PROJECT_BASE_PATH, 'data')
# MODELS_PATH é mantido, mas o modelo xgboost_model.pkl será carregado de DATA_PATH
MODELS_PATH = os.path.join(PROJECT_BASE_PATH, 'models')

# Definir os nomes dos arquivos do modelo e dos dados
model_file_name = 'xgboost_model.pkl'
input_file_name = 'ruf_consolidado_fe.xlsx'

# Construir os caminhos completos para o modelo e os dados
# --- CORREÇÃO AQUI: model_path agora usa DATA_PATH ---
model_path = os.path.join(DATA_PATH, model_file_name)
input_file_path = os.path.join(DATA_PATH, input_file_name)

# --- INÍCIO DO CÓDIGO DE DEPURACAO PARA VERIFICAR CAMINHOS E ARQUIVOS ---
st.write(f"DEBUG: PROJECT_BASE_PATH: {PROJECT_BASE_PATH}")
st.write(f"DEBUG: DATA_PATH: {DATA_PATH}")
st.write(f"DEBUG: MODELS_PATH: {MODELS_PATH}")
st.write(f"DEBUG: model_path (completo): {model_path}")
st.write(f"DEBUG: input_file_path (completo): {input_file_path}")

st.write("DEBUG: Conteúdo de DATA_PATH:")
try:
    if os.path.exists(DATA_PATH):
        for item in os.listdir(DATA_PATH):
            st.write(f"- {item}")
    else:
        st.write(f"DEBUG: Pasta '{DATA_PATH}' não encontrada.")
except Exception as e:
    st.write(f"DEBUG: Erro ao listar '{DATA_PATH}': {e}")

st.write("DEBUG: Conteúdo de MODELS_PATH:")
try:
    if os.path.exists(MODELS_PATH):
        for item in os.listdir(MODELS_PATH):
            st.write(f"- {item}")
    else:
        st.write(f"DEBUG: Pasta '{MODELS_PATH}' não encontrada.")
except Exception as e:
    st.write(f"DEBUG: Erro ao listar '{MODELS_PATH}': {e}")
# --- FIM DO CÓDIGO DE DEPURACAO ---


# --- Funções de Carregamento com Cache para Streamlit ---
# Estas funções agora envolvem as funções de model_logic.py e aplicam o cache do Streamlit
@st.cache_resource
def load_cached_model(path):
    return ml_load_model(path)

@st.cache_data
def load_cached_data(path):
    return ml_load_data(path)

try:
    st.success("DEBUG: 0. App started, imports complete, and model_logic imported successfully.")

    # --- Carregamento Inicial de Dados e Modelo ---
    # Usando as funções com cache
    loaded_model = load_cached_model(model_path)
    df_full = load_cached_data(input_file_path)

    if loaded_model is None or df_full.empty:
        st.error("Erro crítico: Modelo ou dados não puderam ser carregados. Verifique os logs acima.")
        st.stop()

    st.success("DEBUG: 1. Model and data loading functions called.")

    # --- Processamento Inicial de Dados ---
    try:
        latest_edition = df_full['Edicao_RUF'].max()
        df_edicao_6 = df_full[df_full['Edicao_RUF'] == latest_edition].copy()

        if df_edicao_6.empty:
            st.error(f"Erro: Não foram encontrados dados para a edição mais recente ({latest_edition}).")
            st.stop()

        st.success(f"DEBUG: 2. Data for latest edition extracted. {len(df_edicao_6)} universities.")

        # Extrai os dados da UFPE na última edição
        ufpe_data_ed6_row = df_edicao_6[df_edicao_6['Universidade'] == ufpe_exact_name]
        if ufpe_data_ed6_row.empty:
            st.error(f"Erro: Universidade '{ufpe_exact_name}' não encontrada na edição {latest_edition}.")
            st.stop()
        original_ufpe_ed6 = ufpe_data_ed6_row.iloc[0]
        st.success("DEBUG: 3. Dados da UFPE para a Edição 6 extraídos.")

        # Cálculo das Tendências Médias para Outras Universidades
        # AGORA USANDO A FUNÇÃO calculate_average_trends DO model_logic.py
        average_trends = calculate_average_trends(df_full, ufpe_exact_name)
        st.success("DEBUG: 4. Tendências médias para outras universidades calculadas.")

        # Obtém as features esperadas pelo modelo
        if hasattr(loaded_model, 'feature_names_in_'):
            model_expected_features = loaded_model.feature_names_in_
        elif hasattr(loaded_model, 'feature_names'):
            model_expected_features = loaded_model.feature_names
        else:
            st.error("Erro: O modelo carregado não possui 'feature_names_in_' ou 'feature_names'. Não é possível determinar as features esperadas.")
            st.stop()
        st.success("DEBUG: 5. Features esperadas pelo modelo obtidas.")

    except Exception as e:
        st.error(f"Ocorreu um erro durante o processamento inicial dos dados: {e}.")
        st.exception(e)
        st.stop()

    # --- Interface do Streamlit ---
    st.title("Simulador de Ranking RUF para a UFPE")
    st.success("DEBUG: 6. Título do aplicativo definido.")

    # Exibir tabela resumo da UFPE na última edição
    st.subheader(f"Desempenho da UFPE na Edição {get_year_from_edition(latest_edition)} (Original)")
    st.success("DEBUG: 7. Subtítulo da tabela resumo definido.")

    # Prepara os dados da UFPE para exibição na tabela resumo
    try:
        original_ufpe_ed6_display = pd.DataFrame({
            'Métrica': ['Ranking', 'Nota Geral', 'Ensino', 'Pesquisa', 'Mercado', 'Inovação', 'Internacionalização'],
            'Valor': [
                f"#{int(original_ufpe_ed6['Ranking'])}",
                f"{original_ufpe_ed6['Nota']:.2f}",
                f"{original_ufpe_ed6['Nota em Ensino']:.2f}",
                f"{original_ufpe_ed6['Nota em Pesquisa']:.2f}",
                f"{original_ufpe_ed6['Nota em Mercado']:.2f}",
                f"{original_ufpe_ed6['Nota em Inovação']:.2f}",
                f"{original_ufpe_ed6['Nota em Internacionalização']:.2f}"
            ]
        })
        st.dataframe(original_ufpe_ed6_display.set_index('Métrica'), hide_index=False)
        st.success("DEBUG: 8. Tabela resumo da UFPE exibida.")
    except Exception as e:
        st.error(f"Erro ao exibir dados originais da UFPE: {e}")
        st.exception(e)
        st.stop()

    st.markdown("---")
    st.sidebar.header("Configurações da Simulação")

    # Inicializa session_state para sliders
    if 'pct_change_ensino' not in st.session_state:
        st.session_state.pct_change_ensino = 0.0
        st.session_state.pct_change_pesquisa = 0.0
        st.session_state.pct_change_mercado = 0.0
        st.session_state.pct_change_inovacao = 0.0
        st.session_state.pct_change_internacionalizacao = 0.0
        st.session_state.apply_other_uni_trends = True

    pct_change_ensino = st.sidebar.slider("Ensino (%)", -10.0, 10.0, st.session_state.pct_change_ensino, 0.1) / 100
    pct_change_pesquisa = st.sidebar.slider("Pesquisa (%)", -10.0, 10.0, st.session_state.pct_change_pesquisa, 0.1) / 100
    pct_change_mercado = st.sidebar.slider("Mercado (%)", -10.0, 10.0, st.session_state.pct_change_mercado, 0.1) / 100
    pct_change_inovacao = st.sidebar.slider("Inovação (%)", -10.0, 10.0, st.session_state.pct_change_inovacao, 0.1) / 100
    pct_change_internacionalizacao = st.sidebar.slider("Internacionalização (%)", -10.0, 10.0, st.session_state.pct_change_internacionalizacao, 0.1) / 100

    apply_other_uni_trends = st.sidebar.checkbox("Aplicar tendências médias a outras universidades", value=st.session_state.apply_other_uni_trends)

    if st.sidebar.button("Resetar Variações"):
        st.session_state.pct_change_ensino = 0.0
        st.session_state.pct_change_pesquisa = 0.0
        st.session_state.pct_change_mercado = 0.0
        st.session_state.pct_change_inovacao = 0.0
        st.session_state.pct_change_internacionalizacao = 0.0
        st.session_state.apply_other_uni_trends = True
        st.rerun()

    st.success("DEBUG: 9. Sliders e checkbox da sidebar definidos.")

    if st.button("Executar Simulação"):
        st.success("DEBUG: 10. Botão 'Executar Simulação' clicado.")
        try:
            with st.spinner("Executando simulação..."):
                simulated_df = simulate_full_ranking_avg_trend(
                    df_edicao_6, loaded_model, ufpe_exact_name, average_trends,
                    pct_change_ensino, pct_change_pesquisa, pct_change_mercado,
                    pct_change_inovacao, pct_change_internacionalizacao,
                    apply_other_uni_trends, model_expected_features
                )

            simulated_ufpe_ed7 = simulated_df[simulated_df['Universidade'] == ufpe_exact_name].iloc[0]

            st.subheader(f"Resultados da Simulação para a Edição {get_year_from_edition(latest_edition + 1)}")
            st.metric(label=f"Ranking Simulada da UFPE", value=f"#{int(simulated_ufpe_ed7['Simulated_Ranking'])}")

            st.subheader("Comparativo UFPE: Edição Original vs. Edição Simulada")
            comparison_df = pd.DataFrame({
                'Métrica': ['Ranking', 'Nota Geral', 'Ensino', 'Pesquisa', 'Mercado', 'Inovação', 'Internacionalização'],
                f'Edição {get_year_from_edition(latest_edition)} (Original)': [
                    original_ufpe_ed6['Ranking'],
                    original_ufpe_ed6['Nota em Ensino'],
                    original_ufpe_ed6['Nota em Pesquisa'],
                    original_ufpe_ed6['Nota em Mercado'],
                    original_ufpe_ed6['Nota em Inovação'],
                    original_ufpe_ed6['Nota em Internacionalização'],
                    original_ufpe_ed6['Nota']
                ],
                f'Edição {get_year_from_edition(latest_edition + 1)} (Simulada)': [
                    simulated_ufpe_ed7['Simulated_Ranking'],
                    simulated_ufpe_ed7['Nota em Ensino'],
                    simulated_ufpe_ed7['Nota em Pesquisa'],
                    simulated_ufpe_ed7['Nota em Mercado'],
                    simulated_ufpe_ed7['Nota em Inovação'],
                    simulated_ufpe_ed7['Nota em Internacionalização'],
                    simulated_ufpe_ed7['Nota']
                ]
            })

            comparison_df['Diferença'] = comparison_df[f'Edição {get_year_from_edition(latest_edition + 1)} (Simulada)'] - comparison_df[f'Edição {get_year_from_edition(latest_edition)} (Original)']
            ranking_diff_idx = comparison_df[comparison_df['Métrica'] == 'Ranking'].index
            if not ranking_diff_idx.empty:
                comparison_df.loc[ranking_diff_idx, 'Diferença'] = -comparison_df.loc[ranking_diff_idx, 'Diferença']

            st.dataframe(comparison_df.set_index('Métrica'), hide_index=False)

            st.markdown("---")
            st.subheader("Comparativo Gráfico de Notas (Original vs. Simulada)")

            chart_data = pd.DataFrame({
                'Métrica': ['Ensino', 'Pesquisa', 'Mercado', 'Inovação', 'Internacionalização', 'Geral'],
                f'Edição {get_year_from_edition(latest_edition)}': [
                    original_ufpe_ed6['Nota em Ensino'],
                    original_ufpe_ed6['Nota em Pesquisa'],
                    original_ufpe_ed6['Nota em Mercado'],
                    original_ufpe_ed6['Nota em Inovação'],
                    original_ufpe_ed6['Nota em Internacionalização'],
                    original_ufpe_ed6['Nota']
                ],
                f'Edição {get_year_from_edition(latest_edition + 1)} (Simulada)': [
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

            st.markdown("---")
            st.subheader("Top 10 Instituições Previstas")
            # Selecionar e formatar colunas para exibição
            display_cols = ['Simulated_Ranking', 'Universidade', 'Nota'] + [col for col in simulated_df.columns if col.startswith('Nota em')]
            display_df = simulated_df[display_cols].copy()
            display_df.columns = [col.replace('Simulated_Ranking', 'Ranking Previsto').replace('Universidade', 'Instituição').replace('Nota', 'Nota Geral') for col in display_df.columns]
            # Formatar as notas para 2 casas decimais
            for col in display_df.columns:
                if 'Nota' in col:
                    display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}")

            st.dataframe(display_df.head(10), use_container_width=True)


        except Exception as e:
            st.error(f"Ocorreu um erro durante a execução da simulação: {e}.")
            st.exception(e)
            st.stop()

    st.markdown("---")
    st.info("Este simulador utiliza um modelo de Machine Learning treinado com dados históricos do RUF para prever o ranking. As previsões são estimativas e não garantem resultados futuros.")

except Exception as e:
    st.error(f"Um erro crítico ocorreu na inicialização do aplicativo: {e}. Isso pode ser um problema de importação ou um erro muito precoce no script.")
    st.exception(e)
    st.stop()
