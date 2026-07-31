import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np
import altair as alt # Importa Altair para gráficos

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
    return EDITION_YEAR_MAP.get(edition_number, f"Ano Desconhecido.._other - original_note_other
                if original_note_other != 0:
                    df_simulated_edicao.loc[uni_idx, f'{col_base}_pct_change_prev'] = (new_note_other - original_note_other) / original_note_other
                else:
                    df_simulated_edicao.loc[uni_idx, f'{col_base}_pct_change_prev'] = 0.0

            # Recalcular a Nota Geral e suas variações para as outras universidades
            original_overall_note_uni_ed6 = original_uni_notes_ed6['Nota']
            new_overall_note_uni_simulated = df_simulated_edicao.loc[uni_idx, ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']].sum()
            df_simulated_edicao.loc[uni_idx, 'Nota'] = new_overall_note_uni_simulated

            df_simulated_edicao.loc[uni_idx, 'Nota_diff_prev'] = new_overall_note_uni_simulated - original_overall_note_uni_ed6
            if original_overall_note_uni_ed6 != 0:
                df_simulated_edicao.loc[uni_idx, 'Nota_pct_change_prev'] = (new_overall_note_uni_simulated - original_overall_note_uni_ed6) / original_overall_note_uni_ed6
            else:
                df_simulated_edicao.loc[uni_idx, 'Nota_pct_change_prev'] = 0.0

    # Prever o ranking para a edição simulada
    X_simulated = df_simulated_edicao[features]
    df_simulated_edicao['Predicted_Ranking'] = model.predict(X_simulated)

    # Gerar o ranking final
    df_simulated_edicao['Simulated_Ranking'] = df_simulated_edicao['Predicted_Ranking'].rank(method='min', ascending=True).astype(int)

    # CORREÇÃO AQUI: Convertendo dict_keys para list antes de concatenar
    return df_simulated_edicao[['Universidade', 'Simulated_Ranking', 'Predicted_Ranking', 'Nota'] + list(ufpe_pct_changes.keys())]


# --- 3. Interface do Streamlit ---

st.set_page_config(layout="wide", page_title="Simulador de Ranking RUF UFPE")

st.title("📊 Simulador de Ranking RUF - UFPE")
st.markdown("Preveja o impacto de mudanças nas notas da UFPE no Ranking Universitário Folha (RUF).")

# --- Quadro Resumo com Notas Atuais da UFPE (Edição 6) ---
st.subheader(f"Notas Atuais da UFPE (Edição 6 - {get_year_from_edition(6)})") # Título atualizado

# Seleciona as colunas de interesse para o resumo
cols_to_display = ['Ranking', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota']
ufpe_current_notes = ufpe_data_edicao_6[cols_to_display].iloc[0]

# Cria um DataFrame para exibir de forma mais amigável
summary_df = pd.DataFrame({
    'Métrica': ufpe_current_notes.index,
    'Valor': ufpe_current_notes.values # Removido "(Edição 6)" pois já está no título
})
# Esconde o índice do DataFrame aqui
st.dataframe(summary_df.set_index('Métrica'), hide_index=False) # Mantém 'Métrica' como índice visível
st.markdown("---") # Adiciona um separador visual

st.header(f"Configurações de Simulação para a UFPE (Edição 7 - {get_year_from_edition(7)})") # Título atualizado
st.markdown("Ajuste as variações percentuais para as notas da UFPE na próxima edição do RUF.")

col1, col2, col3 = st.columns(3)

# --- NOVO: Variáveis de estado para os sliders ---
# Isso permite que o botão de reset funcione
if 'pct_ensino_display' not in st.session_state:
    st.session_state.pct_ensino_display = 0
if 'pct_pesquisa_display' not in st.session_state:
    st.session_state.pct_pesquisa_display = 0
if 'pct_mercado_display' not in st.session_state:
    st.session_state.pct_mercado_display = 0
if 'pct_inovacao_display' not in st.session_state:
    st.session_state.pct_inovacao_display = 0
if 'pct_internacionalizacao_display' not in st.session_state:
    st.session_state.pct_internacionalizacao_display = 0

with col1:
    pct_ensino_display = st.slider("Variação % em Ensino", -20, 20, st.session_state.pct_ensino_display, 1, format="%.0f%%", key="ensino_slider")
    pct_pesquisa_display = st.slider("Variação % em Pesquisa", -20, 20, st.session_state.pct_pesquisa_display, 1, format="%.0f%%", key="pesquisa_slider")

with col2:
    pct_mercado_display = st.slider("Variação % em Mercado", -20, 20, st.session_state.pct_mercado_display, 1, format="%.0f%%", key="mercado_slider")
    pct_inovacao_display = st.slider("Variação % em Inovação", -20, 20, st.session_state.pct_inovacao_display, 1, format="%.0f%%", key="inovacao_slider")

with col3:
    pct_internacionalizacao_display = st.slider("Variação % em Internacionalização", -20, 20, st.session_state.pct_internacionalizacao_display, 1, format="%.0f%%", key="internacionalizacao_slider")

# --- NOVO: Função para resetar os sliders ---
def reset_sliders():
    st.session_state.pct_ensino_display = 0
    st.session_state.pct_pesquisa_display = 0
    st.session_state.pct_mercado_display = 0
    st.session_state.pct_inovacao_display = 0
    st.session_state.pct_internacionalizacao_display = 0

# Botão para resetar os sliders
st.button("Resetar Variações", on_click=reset_sliders)


if st.button("Executar Simulação"):
    st.subheader(f"Resultados da Simulação (Edição 7 - {get_year_from_edition(7)})") # Título atualizado

    # Converte os valores dos sliders para decimais antes de passar para a função de simulação
    pct_ensino = pct_ensino_display / 100
    pct_pesquisa = pct_pesquisa_display / 100
    pct_mercado = pct_mercado_display / 100
    pct_inovacao = pct_inovacao_display / 100
    pct_internacionalizacao = pct_internacionalizacao_display / 100

    # Executa a simulação
    df_simulated_results = simulate_full_ranking_avg_trend(
        df_base_edicao_6=df_edicao_6,
        model=loaded_model,
        ufpe_name=ufpe_exact_name,
        average_trends_df=average_trends,
        pct_change_ensino=pct_ensino,
        pct_change_pesquisa=pct_pesquisa,
        pct_change_mercado=pct_mercado,
        pct_change_inovacao=pct_inovacao,
        pct_change_internacionalizacao=pct_internacionalizacao
    )

    # --- NOVO: Saídas de Depuração para Predicted_Ranking ---
    st.markdown("---")
    st.subheader("DEBUG: Predicted_Ranking (Notas Brutas do Modelo)")
    st.write(f"UFPE (Edição 6): Ranking {ufpe_data_edicao_6['Ranking'].iloc[0]}, Predicted_Ranking (não disponível diretamente aqui, mas seria o valor que gerou o ranking 12)")
    st.write(f"UFPE (Simulada): Ranking {df_simulated_results[df_simulated_results['Universidade'] == ufpe_exact_name]['Simulated_Ranking'].iloc[0]}, Predicted_Ranking: {df_simulated_results[df_simulated_results['Universidade'] == ufpe_exact_name]['Predicted_Ranking'].iloc[0]:.2f}")

    st.write("Top 5 Universidades (Edição 6) e seus Predicted_Rankings simulados:")
    top_5_ed6_names = df_edicao_6.sort_values('Ranking').head(5)['Universidade'].tolist()
    debug_df = df_simulated_results[df_simulated_results['Universidade'].isin(top_5_ed6_names)][['Universidade', 'Simulated_Ranking', 'Predicted_Ranking']].sort_values('Simulated_Ranking')
    st.dataframe(debug_df, hide_index=True)
    st.markdown("---")
    # --- FIM DAS SAÍDAS DE DEPURÇÃO ---


    # Exibe o ranking da UFPE
    ufpe_simulated_ranking = df_simulated_results[df_simulated_results['Universidade'] == ufpe_exact_name]
    st.write(f"**Ranking Simulador da UFPE:** Posição **#{ufpe_simulated_ranking['Simulated_Ranking'].iloc[0]}**")
    st.dataframe(ufpe_simulated_ranking, hide_index=True) # Esconde o índice

    st.markdown("---")
    st.subheader("Ranking Completo Simulador (Top 20)")
    st.dataframe(df_simulated_results.sort_values('Simulated_Ranking').head(20), hide_index=True) # Esconde o índice

    st.markdown("---")
    st.subheader(f"Comparativo UFPE (Edição 6 - {get_year_from_edition(6)} vs. Edição 7 - {get_year_from_edition(7)} Simulada)") # Título atualizado
    original_ufpe_ed6 = df_edicao_6[df_edicao_6['Universidade'] == ufpe_exact_name][['Universidade', 'Ranking', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota']].iloc[0]
    simulated_ufpe_ed7 = ufpe_simulated_ranking[['Universidade', 'Simulated_Ranking', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota']].iloc[0]

    comparison_df = pd.DataFrame({
        'Métrica': ['Ranking', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota Geral'],
        f'Edição {get_year_from_edition(6)} (Original)': [ # Coluna atualizada
            original_ufpe_ed6['Ranking'],
            original_ufpe_ed6['Nota em Ensino'],
            original_ufpe_ed6['Nota em Pesquisa'],
            original_ufpe_ed6['Nota em Mercado'],
            original_ufpe_ed6['Nota em Inovação'],
            original_ufpe_ed6['Nota em Internacionalização'],
            original_ufpe_ed6['Nota']
        ],
        f'Edição {get_year_from_edition(7)} (Simulada)': [ # Coluna atualizada
            simulated_ufpe_ed7['Simulated_Ranking'],
            simulated_ufpe_ed7['Nota em Ensino'],
            simulated_ufpe_ed7['Nota em Pesquisa'],
            simulated_ufpe_ed7['Nota em Mercado'],
            simulated_ufpe_ed7['Nota em Inovação'],
            simulated_ufpe_ed7['Nota em Internacionalização'],
            simulated_ufpe_ed7['Nota']
        ]
    })

    # --- NOVO: Adiciona a coluna de Diferença ---
    comparison_df['Diferença'] = comparison_df[f'Edição {get_year_from_edition(7)} (Simulada)'] - comparison_df[f'Edição {get_year_from_edition(6)} (Original)']
    # Para o Ranking, a diferença negativa é uma melhoria, então invertemos o sinal para clareza
    ranking_diff_idx = comparison_df[comparison_df['Métrica'] == 'Ranking'].index
    if not ranking_diff_idx.empty:
        comparison_df.loc[ranking_diff_idx, 'Diferença'] = -comparison_df.loc[ranking_diff_idx, 'Diferença']


    st.dataframe(comparison_df.set_index('Métrica'), hide_index=False) # Mantém 'Métrica' como índice visível

    # --- NOVO: Gráfico de Barras para Comparativo de Notas ---
    st.markdown("---")
    st.subheader("Comparativo Gráfico de Notas (Edição 6 vs. Edição 7 Simulada)")

    # Prepara os dados para o gráfico
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

    # Transforma o DataFrame para o formato "long" para Altair
    chart_data_melted = chart_data.melt('Métrica', var_name='Edição', value_name='Nota')

    # Cria o gráfico de barras
    chart = alt.Chart(chart_data_melted).mark_bar().encode(
        x=alt.X('Métrica', axis=alt.Axis(title='Dimensão da Nota')),
        y=alt.Y('Nota', axis=alt.Axis(title='Valor da Nota')),
        color=alt.Color('Edição', title='Edição RUF'),
        tooltip=['Métrica', 'Edição', 'Nota']
    ).properties(
        title='Notas da UFPE por Dimensão'
    ).interactive() # Permite zoom e pan

    st.altair_chart(chart, use_container_width=True)


st.markdown("---")
st.info("Este simulador utiliza um modelo de Machine Learning treinado com dados históricos do RUF para prever o ranking. As previsões são estimativas e não garantem resultados futuros.")
