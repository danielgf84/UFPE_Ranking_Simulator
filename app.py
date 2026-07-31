import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np
import altair as alt

# Importa as funções e variáveis do arquivo de lógica do modelo
from model_logic import (
    load_model, load_data, simulate_full_ranking_avg_trend, calculate_average_trends,
    ufpe_exact_name, target_column, EDITION_YEAR_MAP, get_year_from_edition,
    model_path, input_file_path
)

st.set_page_config(layout="wide")

st.success("DEBUG: 0. App started and imports complete.")

# --- Carregamento do Modelo e Dados ---
try:
    loaded_model = load_model(model_path)
    df_full = load_data(input_file_path)
    st.success("DEBUG: 1. Model and data loading functions called.")
except Exception as e:
    st.error(f"Erro CRÍTICO na fase de carregamento inicial: {e}")
    st.exception(e)
    st.stop()

if loaded_model is None or df_full.empty:
    st.error("DEBUG: 2. Modelo ou dados não foram carregados. Encerrando.")
    st.stop()

# --- Processamento Inicial dos Dados ---
try:
    # Determina a última edição presente nos dados
    latest_edition = df_full['Edicao_RUF'].max()
    st.success(f"DEBUG: 3. Latest edition determined: {latest_edition}.")

    # Filtra os dados da última edição
    df_edicao_6 = df_full[df_full['Edicao_RUF'] == latest_edition].copy()
    st.success(f"DEBUG: 4. Data for latest edition extracted. {len(df_edicao_6)} universities.")

    # Extrai os dados da UFPE na última edição para exibição e simulação
    original_ufpe_ed6_series = df_edicao_6[df_edicao_6['Universidade'] == ufpe_exact_name]
    if original_ufpe_ed6_series.empty:
        st.error(f"Erro: Universidade '{ufpe_exact_name}' não encontrada na Edição {latest_edition}. Verifique o nome ou os dados.")
        st.stop()
    original_ufpe_ed6 = original_ufpe_ed6_series.iloc[0]
    st.success("DEBUG: 5. Dados da UFPE para a Edição 6 extraídos.")

    # Calcula as tendências médias para outras universidades
    average_trends = calculate_average_trends(df_full, latest_edition)
    st.success("DEBUG: 6. Tendências médias para outras universidades calculadas.")

    # Extrai as features esperadas pelo modelo (assumindo que o modelo tem um atributo feature_names_in_)
    # Se o seu modelo não tiver 'feature_names_in_', você precisará fornecer essa lista manualmente
    try:
        model_expected_features = loaded_model.feature_names_in_
        st.success(f"DEBUG: 7. Features esperadas pelo modelo extraídas. Total: {len(model_expected_features)}")
    except AttributeError:
        st.warning("Aviso: O modelo não possui 'feature_names_in_'. Usando lista de features padrão. Isso pode causar 'feature_names mismatch'.")
        # Esta lista deve ser EXATAMENTE a mesma usada no treinamento do modelo
        model_expected_features = [
            'Posição em Ensino', 'Nota em Ensino', 'Posição em Pesquisa', 'Nota em Pesquisa',
            'Posição em Mercado', 'Nota em Mercado', 'Posição em Inovação', 'Nota em Inovação',
            'Posição em Internacionalização', 'Nota em Internacionalização', 'Nota',
            'Estado_AL', 'Estado_AM', 'Estado_AP', 'Estado_BA', 'Estado_CE', 'Estado_DF',
            'Estado_ES', 'Estado_GO', 'Estado_MA', 'Estado_MG', 'Estado_MS', 'Estado_MT',
            'Estado_PA', 'Estado_PB', 'Estado_PE', 'Estado_PI', 'Estado_PR', 'Estado_RJ',
            'Estado_RN', 'Estado_RO', 'Estado_RR', 'Estado_RS', 'Estado_SC', 'Estado_SE',
            'Estado_SP', 'Estado_TO', 'Pública ou Privada_Federal', 'Pública ou Privada_Municipal',
            'Pública ou Privada_Privada', 'Ranking_diff_prev', 'Ranking_pct_change_prev',
            'Posição em Ensino_diff_prev', 'Posição em Ensino_pct_change_prev',
            'Nota em Ensino_diff_prev', 'Nota em Ensino_pct_change_prev',
            'Posição em Pesquisa_diff_prev', 'Posição em Pesquisa_pct_change_prev',
            'Nota em Pesquisa_diff_prev', 'Nota em Pesquisa_pct_change_prev',
            'Posição em Mercado_diff_prev', 'Posição em Mercado_pct_change_prev',
            'Nota em Mercado_diff_prev', 'Nota em Mercado_pct_change_prev',
            'Posição em Inovação_diff_prev', 'Posição em Inovação_pct_change_prev',
            'Nota em Inovação_diff_prev', 'Nota em Inovação_pct_change_prev',
            'Posição em Internacionalização_diff_prev', 'Posição em Internacionalização_pct_change_prev',
            'Nota em Internacionalização_diff_prev', 'Nota em Internacionalização_pct_change_prev',
            'Nota_diff_prev', 'Nota_pct_change_prev'
        ]

except Exception as e:
    st.error(f"Erro CRÍTICO na fase de processamento inicial dos dados: {e}")
    st.exception(e)
    st.stop()


# --- Interface do Streamlit ---
st.title("Simulador de Ranking RUF para a UFPE")
st.success("DEBUG: 8. Título do aplicativo definido.")

# Exibir tabela resumo da UFPE na última edição
st.subheader(f"Desempenho da UFPE na Edição {get_year_from_edition(latest_edition)} (Original)")
st.success("DEBUG: 9. Subtítulo da tabela resumo definido.")

try:
    # Prepara os dados da UFPE para exibição na tabela resumo
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
    st.success("DEBUG: 10. Tabela resumo da UFPE exibida.")
except Exception as e:
    st.error(f"Erro ao exibir a tabela resumo da UFPE: {e}")
    st.exception(e)
    st.stop()


st.sidebar.header("Ajustar Variações para a UFPE (Edição Simulada)")
st.success("DEBUG: 11. Header da sidebar definido.")

# Inicializa st.session_state para manter os valores dos sliders
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

st.success("DEBUG: 12. Sliders e checkbox da sidebar definidos.")

if st.button("Executar Simulação"):
    st.success("DEBUG: 13. Botão 'Executar Simulação' clicado.")
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
