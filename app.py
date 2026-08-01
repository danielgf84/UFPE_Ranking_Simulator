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

print("APP_DEBUG: Script app.py iniciado.")

# --- Configuração da Página Streamlit ---
st.set_page_config(layout="wide", page_title="Simulador de Ranking RUF para a UFPE")
print("APP_DEBUG: st.set_page_config executado.")

# --- Definir Caminhos do Projeto para o ambiente de execução (GitHub/Streamlit Cloud) ---
PROJECT_BASE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(PROJECT_BASE_PATH, 'data')
MODELS_PATH = os.path.join(PROJECT_BASE_PATH, 'models')

model_file_name = 'xgboost_model.pkl'
input_file_name = 'ruf_consolidado_fe.xlsx'

model_path = os.path.join(DATA_PATH, model_file_name)
input_file_path = os.path.join(DATA_PATH, input_file_name)

print(f"APP_DEBUG: PROJECT_BASE_PATH: {PROJECT_BASE_PATH}")
print(f"APP_DEBUG: DATA_PATH: {DATA_PATH}")
print(f"APP_DEBUG: MODELS_PATH: {MODELS_PATH}")
print(f"APP_DEBUG: model_path (completo): {model_path}")
print(f"APP_DEBUG: input_file_path (completo): {input_file_path}")

print("APP_DEBUG: Conteúdo de DATA_PATH:")
try:
    if os.path.exists(DATA_PATH):
        for item in os.listdir(DATA_PATH):
            print(f"- {item}")
    else:
        print(f"APP_DEBUG: Pasta '{DATA_PATH}' não encontrada.")
except Exception as e:
    print(f"APP_DEBUG: Erro ao listar '{DATA_PATH}': {e}")

print("APP_DEBUG: Conteúdo de MODELS_PATH:")
try:
    if os.path.exists(MODELS_PATH):
        for item in os.listdir(MODELS_PATH):
            print(f"- {item}")
    else:
        print(f"APP_DEBUG: Pasta '{MODELS_PATH}' não encontrada.")
except Exception as e:
    print(f"APP_DEBUG: Erro ao listar '{MODELS_PATH}': {e}")
# --- FIM DO CÓDIGO DE DEPURACAO ---


# --- Funções de Carregamento com Cache para Streamlit ---
@st.cache_resource
def load_cached_model(path):
    print(f"APP_DEBUG: Chamando ml_load_model para {path}")
    return ml_load_model(path)

@st.cache_data
def load_cached_data(path):
    print(f"APP_DEBUG: Chamando ml_load_data para {path}")
    return ml_load_data(path)

try:
    st.success("DEBUG: 0. App started, imports complete, and model_logic imported successfully.")
    print("APP_DEBUG: Iniciando carregamento de modelo e dados.")

    # --- Carregamento Inicial de Dados e Modelo ---
    loaded_model = load_cached_model(model_path)
    df_full = load_cached_data(input_file_path)

    if loaded_model is None or df_full.empty:
        st.error("Erro crítico: Modelo ou dados não puderam ser carregados. Verifique os logs acima.")
        st.stop()

    st.success("DEBUG: 1. Model and data loading functions called.")
    print("APP_DEBUG: Modelo e dados carregados com sucesso.")

    # --- Processamento Inicial de Dados ---
    try:
        latest_edition = df_full['Edicao_RUF'].max()
        df_edicao_6 = df_full[df_full['Edicao_RUF'] == latest_edition].copy()

        if df_edicao_6.empty:
            st.error(f"Erro: Não foram encontrados dados para a edição mais recente ({latest_edition}).")
            st.stop()

        st.success(f"DEBUG: 2. Data for latest edition extracted. {len(df_edicao_6)} universities.")
        print(f"APP_DEBUG: Dados da última edição extraídos. {len(df_edicao_6)} universidades.")

        # Extrai os dados da UFPE na última edição
        ufpe_data_ed6_row = df_edicao_6[df_edicao_6['Universidade'] == ufpe_exact_name]
        if ufpe_data_ed6_row.empty:
            st.error(f"Erro: Universidade '{ufpe_exact_name}' não encontrada na edição {latest_edition}.")
            st.stop()
        original_ufpe_ed6 = ufpe_data_ed6_row.iloc[0]
        st.success("DEBUG: 3. Dados da UFPE para a Edição 6 extraídos.")
        print("APP_DEBUG: Dados da UFPE extraídos.")

        # Cálculo das Tendências Médias para Outras Universidades
        print("APP_DEBUG: Iniciando cálculo de tendências médias.")
        average_trends = calculate_average_trends(df_full, ufpe_exact_name)
        st.success("DEBUG: 4. Tendências médias para outras universidades calculadas.")
        print("APP_DEBUG: Tendências médias calculadas.")

        # Obtém as features esperadas pelo modelo
        model_expected_features = loaded_model.get_booster().feature_names
        print(f"APP_DEBUG: Features esperadas pelo modelo obtidas: {len(model_expected_features)} features.")

        st.markdown("# Simulador de Ranking RUF para a UFPE")
        st.markdown(f"**Edição Base:** {get_year_from_edition(latest_edition)} (Edição {latest_edition})")
        st.markdown(f"**Próxima Edição Simulada:** {get_year_from_edition(latest_edition + 1)} (Edição {latest_edition + 1})")

        st.markdown("---")
        st.subheader("Configurações da Simulação para a UFPE")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("##### Variação Percentual das Notas da UFPE")
            pct_change_ensino = st.slider('Ensino (%)', -10.0, 10.0, 0.0, 0.1) / 100
            pct_change_pesquisa = st.slider('Pesquisa (%)', -10.0, 10.0, 0.0, 0.1) / 100
        with col2:
            st.markdown("#####") # Para alinhar os sliders
            pct_change_mercado = st.slider('Mercado (%)', -10.0, 10.0, 0.0, 0.1) / 100
            pct_change_inovacao = st.slider('Inovação (%)', -10.0, 10.0, 0.0, 0.1) / 100
        with col3:
            st.markdown("#####") # Para alinhar os sliders
            pct_change_internacionalizacao = st.slider('Internacionalização (%)', -10.0, 10.0, 0.0, 0.1) / 100
            apply_other_uni_trends = st.checkbox("Aplicar tendências médias para outras universidades", value=True)

        st.markdown("---")

        print("APP_DEBUG: Iniciando simulação.")
        simulated_df = simulate_full_ranking_avg_trend(
            df_edicao_6, loaded_model, ufpe_exact_name, average_trends,
            pct_change_ensino, pct_change_pesquisa, pct_change_mercado,
            pct_change_inovacao, pct_change_internacionalizacao,
            apply_other_uni_trends, model_expected_features
        )
        print("APP_DEBUG: Simulação concluída.")

        simulated_ufpe_ed7 = simulated_df[simulated_df['Universidade'] == ufpe_exact_name].iloc[0]

        st.subheader(f"Resultados da Simulação para a UFPE (Edição {get_year_from_edition(latest_edition + 1)})")

        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric(label="Ranking Previsto", value=int(simulated_ufpe_ed7['Simulated_Ranking']))
        with col_res2:
            st.metric(label="Nota Geral Prevista", value=f"{simulated_ufpe_ed7['Nota']:.2f}")

        st.markdown("---")
        st.subheader("Comparativo Detalhado (Original vs. Simulada)")

        comparison_df = pd.DataFrame({
            'Métrica': ['Ranking', 'Nota Geral', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização'],
            f'Edição {get_year_from_edition(latest_edition)} (Original)': [
                original_ufpe_ed6['Ranking'],
                original_ufpe_ed6['Nota'],
                original_ufpe_ed6['Nota em Ensino'],
                original_ufpe_ed6['Nota em Pesquisa'],
                original_ufpe_ed6['Nota em Mercado'],
                original_ufpe_ed6['Nota em Inovação'],
                original_ufpe_ed6['Nota em Internacionalização']
            ],
            f'Edição {get_year_from_edition(latest_edition + 1)} (Simulada)': [
                simulated_ufpe_ed7['Simulated_Ranking'],
                simulated_ufpe_ed7['Nota'],
                simulated_ufpe_ed7['Nota em Ensino'],
                simulated_ufpe_ed7['Nota em Pesquisa'],
                simulated_ufpe_ed7['Nota em Mercado'],
                simulated_ufpe_ed7['Nota em Inovação'],
                simulated_ufpe_ed7['Nota em Internacionalização']
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
