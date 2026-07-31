# app.py
import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np
import altair as alt

# --- Definir Caminhos do Projeto no Colab ---
# Estes devem ser os mesmos caminhos definidos na célula 1.2 do seu notebook Colab
PROJECT_BASE_PATH = '/content/drive/MyDrive/TESE/simulador'
DATA_PATH = os.path.join(PROJECT_BASE_PATH, 'data')
MODELS_PATH = os.path.join(PROJECT_BASE_PATH, 'models')

# --- Variáveis de Arquivo e Modelo ---
# O nome do arquivo consolidado que você salvou na etapa de limpeza
input_file_name = 'ruf_consolidado_fe.xlsx' # Ajuste se o nome do seu arquivo consolidado for diferente
input_file_path = os.path.join(DATA_PATH, input_file_name)
model_file_name = 'xgboost_model.pkl' # Ajuste se o nome do seu modelo salvo for diferente
model_path = os.path.join(MODELS_PATH, model_file_name)

try:
    # Tenta importar do model_logic.py
    # Passa os caminhos como argumentos para as funções de carregamento
    from model_logic import (
        load_model as ml_load_model, # Renomeia para evitar conflito com @st.cache_resource
        load_data as ml_load_data,   # Renomeia para evitar conflito com @st.cache_data
        simulate_full_ranking_avg_trend,
        ufpe_exact_name, target_column, EDITION_YEAR_MAP, get_year_from_edition,
        calculate_average_trends # Importa a nova função de cálculo de tendências
    )

    st.set_page_config(layout="wide")
    st.success("DEBUG: 0. App started, imports complete, and model_logic imported successfully.")

    # --- Funções de Carregamento com Cache (agora no app.py) ---
    @st.cache_resource
    def load_cached_model(path):
        return ml_load_model(path)

    @st.cache_data
    def load_cached_data(path):
        return ml_load_data(path)

    # --- Carregamento Inicial de Dados e Modelo ---
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
        st.dataframe(original_ufpe_ed6_display, hide_index=True)
        st.success("DEBUG: 8. Tabela resumo da UFPE exibida.")
    except Exception as e:
        st.error(f"Erro ao preparar ou exibir a tabela resumo da UFPE: {e}.")
        st.exception(e)
        st.stop()

    st.sidebar.header("Ajustar Variações para a UFPE (Edição Simulada)")

    # Inicializa st.session_state para sliders e checkbox
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
        st.experimental_rerun()

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

            st.metric(label=f"Ranking Simulada da UFPE (Edição {get_year_from_edition(latest_edition + 1)})", value=f"#{int(simulated_ufpe_ed7['Simulated_Ranking'])}")

            st.subheader("Comparativo UFPE: Edição 6 (Original) vs. Edição 7 (Simulada)")
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
