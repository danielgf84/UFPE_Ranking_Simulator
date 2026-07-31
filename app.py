import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np
import altair as alt

st.write("DEBUG: 1. Imports complete.") # PRIMEIRA MENSAGEM DE DEBUG

# --- 1. Configuração e Carregamento de Recursos ---
data_path = 'data'
model_path = os.path.join(data_path, 'xgboost_model.pkl')
input_file_name = 'ruf_consolidado_fe.xlsx'
input_file_path = os.path.join(data_path, input_file_name)

st.write(f"DEBUG: 2. Paths configured. Model path: {model_path}, Data path: {input_file_path}") # SEGUNDA MENSAGEM DE DEBUG

ufpe_exact_name = 'Universidade Federal de Pernambuco'
target_column = 'Ranking'

EDITION_YEAR_MAP = {
    1: 2017, 2: 2018, 3: 2019, 4: 2023, 5: 2024, 6: 2025, 7: 2026
}

def get_year_from_edition(edition_number):
    return EDITION_YEAR_MAP.get(edition_number, f"Ano Desconhecido (Edição {edition_number})")

@st.cache_resource
def load_model(path):
    try:
        model = joblib.load(path)
        st.write(f"DEBUG: Model loaded from {path}") # DEBUG DENTRO DA FUNÇÃO
        return model
    except Exception as e:
        st.error(f"Erro ao carregar o modelo: {e}. Verifique se o arquivo '{os.path.basename(path)}' está na pasta 'data' do seu repositório.")
        st.stop() # Adicionado st.stop() aqui para garantir que o app pare
        return None

@st.cache_data
def load_data(path):
    try:
        df = pd.read_excel(path)
        st.write(f"DEBUG: Data loaded from {path}") # DEBUG DENTRO DA FUNÇÃO
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}. Verifique se o arquivo '{os.path.basename(path)}' está na pasta 'data' do seu repositório.")
        st.stop() # Adicionado st.stop() aqui para garantir que o app pare
        return pd.DataFrame()

loaded_model = load_model(model_path)
df_model = load_data(input_file_path)

st.write("DEBUG: 3. Model and data loading functions called.") # TERCEIRA MENSAGEM DE DEBUG

if loaded_model is None or df_model.empty:
    st.error("Não foi possível carregar o modelo ou os dados. A aplicação não pode continuar. Por favor, verifique os logs para mais detalhes.")
    st.stop()
st.write("DEBUG: 4. Model and data loaded successfully and checked.") # QUARTA MENSAGEM DE DEBUG

# --- Cálculo das Tendências Médias para Outras Universidades ---
notas_cols_base = ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota']
trend_pct_change_cols = [f'{col}_pct_change_prev' for col in notas_cols_base]

df_other_universities = df_model[df_model['Universidade'] != ufpe_exact_name].copy()

for col_base in notas_cols_base:
    if col_base in df_other_universities.columns:
        df_other_universities[f'{col_base}_pct_change_prev'] = df_other_universities.groupby('Universidade')[col_base].pct_change()
    else:
        st.warning(f"Coluna '{col_base}' não encontrada para cálculo de tendência. Será ignorada.")
        df_other_universities[f'{col_base}_pct_change_prev'] = 0.0

existing_trend_pct_change_cols = [col for col in trend_pct_change_cols if col in df_other_universities.columns]
average_trends = df_other_universities.groupby('Universidade')[existing_trend_pct_change_cols].mean()
average_trends = average_trends.fillna(0)
st.write("DEBUG: 5. Average trends calculated.") # QUINTA MENSAGEM DE DEBUG

# --- Extrai dados da Edição 6 para a UFPE ---
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
st.write("DEBUG: 6. Edition 6 data extracted.") # SEXTA MENSAGEM DE DEBUG

# --- Título e Descrição do Aplicativo ---
st.set_page_config(layout="wide")
st.title(f"Simulador de Ranking RUF da UFPE (Edição {get_year_from_edition(7)})")
st.write("Este aplicativo permite simular o impacto de variações nas notas da UFPE nas diferentes dimensões do Ranking Universitário Folha (RUF) para a próxima edição.")
st.write("DEBUG: 7. Page config and title set.") # SÉTIMA MENSAGEM DE DEBUG

# --- Quadro Resumo da UFPE (Edição 6) ---
summary_df = pd.DataFrame({
    'Métrica': ['Ranking', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota Geral'],
    f'Edição {get_year_from_edition(6)}': [
        ufpe_data_edicao_6['Ranking'].iloc[0],
        ufpe_data_edicao_6['Nota em Ensino'].iloc[0],
        ufpe_data_edicao_6['Nota em Pesquisa'].iloc[0],
        ufpe_data_edicao_6['Nota em Mercado'].iloc[0],
        ufpe_data_edicao_6['Nota em Inovação'].iloc[0],
        ufpe_data_edicao_6['Nota em Internacionalização'].iloc[0],
        ufpe_data_edicao_6['Nota'].iloc[0]
    ]
})
st.dataframe(summary_df.set_index('Métrica'), hide_index=False)
st.write("DEBUG: 8. Summary table displayed.") # OITAVA MENSAGEM DE DEBUG

# --- Sliders de Variação para a UFPE ---
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
st.write("DEBUG: 9. Sliders initialized and displayed.") # NONA MENSAGEM DE DEBUG

# --- Botão para resetar os sliders ---
def reset_sliders():
    st.session_state.pct_ensino_display = 0
    st.session_state.pct_pesquisa_display = 0
    st.session_state.pct_mercado_display = 0
    st.session_state.pct_inovacao_display = 0
    st.session_state.pct_internacionalizacao_display = 0

st.button("Resetar Variações", on_click=reset_sliders)
st.write("DEBUG: 10. Reset button displayed.") # DÉCIMA MENSAGEM DE DEBUG

# --- Checkbox para considerar tendências de outras universidades ---
apply_other_uni_trends = st.checkbox("Considerar tendências históricas de outras universidades", value=True, help="Se marcado, o simulador aplicará as tendências históricas de melhoria/piora para as outras universidades. Se desmarcado, as notas das outras universidades permanecerão as mesmas da Edição 6, servindo como um baseline mais estável para a UFPE.")
st.write("DEBUG: 11. Checkbox displayed.") # DÉCIMA PRIMEIRA MENSAGEM DE DEBUG

# --- Execução da Simulação ---
if st.button("Executar Simulação"):
    st.write("DEBUG: 12. Simulation button clicked.") # DÉCIMA SEGUNDA MENSAGEM DE DEBUG
    with st.spinner("Executando simulação..."):
        # Converte as porcentagens para fatores de mudança (ex: 5% -> 0.05)
        pct_change_ensino = pct_ensino_display / 100
        pct_change_pesquisa = pct_pesquisa_display / 100
        pct_change_mercado = pct_mercado_display / 100
        pct_change_inovacao = pct_inovacao_display / 100
        pct_change_internacionalizacao = pct_internacionalizacao_display / 100
    # Chama a função de simulação
    simulated_df = simulate_full_ranking_avg_trend(
        df_edicao_6, loaded_model, ufpe_exact_name, average_trends,
        pct_change_ensino, pct_change_pesquisa, pct_change_mercado,
        pct_change_inovacao, pct_change_internacionalizacao,
        apply_other_uni_trends # Passa o valor do checkbox
    )
    st.write("DEBUG: 13. simulate_full_ranking_avg_trend completed.") # DÉCIMA TERCEIRA MENSAGEM DE DEBUG

    # Previsão dos rankings para o DataFrame simulado
    simulated_df['Predicted_Ranking'] = loaded_model.predict(simulated_df[loaded_model.feature_names_in_])
    st.write("DEBUG: 14. Model prediction completed.") # DÉCIMA QUARTA MENSAGEM DE DEBUG

    # O ranking é baseado na ordem crescente do Predicted_Ranking (menor valor = melhor ranking)
    simulated_df['Simulated_Ranking'] = simulated_df['Predicted_Ranking'].rank(method='min').astype(int)
    st.write("DEBUG: 15. Ranking calculation completed.") # DÉCIMA QUINTA MENSAGEM DE DEBUG

    # Extrai os resultados da UFPE
    simulated_ufpe_ed7 = simulated_df[simulated_df['Universidade'] == ufpe_exact_name].iloc[0]
    st.write("DEBUG: 16. UFPE results extracted.") # DÉCIMA SEXTA MENSAGEM DE DEBUG

    st.markdown("---")
    st.subheader(f"Resultados da Simulação para a UFPE (Edição {get_year_from_edition(7)})")
    st.metric(label="Ranking Simulado da UFPE", value=int(simulated_ufpe_ed7['Simulated_Ranking']))

    st.markdown("---")
    st.subheader("Comparativo Detalhado UFPE (Edição 6 Original vs. Edição 7 Simulada)")

    # Prepara o DataFrame para comparação
    original_ufpe_ed6 = ufpe_data_edicao_6.iloc[0]
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
st.markdown("---")
st.info("Este simulador utiliza um modelo de Machine Learning treinado com dados históricos do RUF para prever o ranking. As previsões são estimativas e não garantem resultados futuros.")
st.write("DEBUG: 17. End of script reached.") # ÚLTIMA MENSAGEM DE DEBUG
