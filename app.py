import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np
import altair as alt # Adicionado para gráficos

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
        st.error(f"Erro ao carregar o modelo: {e}. Verifique se o arquivo '{os.path.basename(path)}' está na pasta 'data' do seu repositório.")
        return None

@st.cache_data # Usa o cache do Streamlit para carregar os dados apenas uma vez
def load_data(path):
    try:
        df = pd.read_excel(path)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}. Verifique se o arquivo '{os.path.basename(path)}' está na pasta 'data' do seu repositório.")
        return pd.DataFrame()

# Carrega o modelo e os dados
loaded_model = load_model(model_path)
df_model = load_data(input_file_path)

# Verifica se o modelo e os dados foram carregados com sucesso
if loaded_model is None or df_model.empty:
    st.error("Não foi possível carregar o modelo ou os dados. A aplicação não pode continuar. Por favor, verifique os logs para mais detalhes.")
    st.stop() # Para a execução do Streamlit se houver erro

# --- Preparação dos Dados (similar aos Blocos 2 e 3 do notebook) ---

# Verifica se a coluna 'Edicao_RUF' existe antes de tentar usá-la
if 'Edicao_RUF' not in df_model.columns:
    st.error("Erro: A coluna 'Edicao_RUF' não foi encontrada no DataFrame carregado. Verifique o arquivo Excel.")
    st.stop()

df_edicao_6 = df_model[df_model['Edicao_RUF'] == 6].copy()
df_edicao_5 = df_model[df_model['Edicao_RUF'] == 5].copy()

ufpe_data_edicao_6 = df_edicao_6[df_edicao_6['Universidade'] == ufpe_exact_name].copy()

if ufpe_data_edicao_6.empty:
    st.error(f"Erro: A universidade '{ufpe_exact_name}' não foi encontrada na Edição 6. Verifique o nome ou os dados no arquivo.")
    st.stop()

# Colunas de notas que serão usadas como features no modelo
notas_cols_base_list = ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']
features = ['Edicao_RUF'] + notas_cols_base_list + [f'{col}_diff_prev' for col in notas_cols_base_list] + [f'{col}_pct_change_prev' for col in notas_cols_base_list] + ['Nota_diff_prev', 'Nota_pct_change_prev']

# --- Cálculo das Tendências Médias para Outras Universidades ---
# Exclui a UFPE do cálculo das tendências médias
df_other_universities = df_model[df_model['Universidade'] != ufpe_exact_name].copy()

# Calcula as variações percentuais para todas as edições e universidades
for col_base in notas_cols_base_list + ['Nota']: # Inclui a Nota Geral para cálculo de tendências
    if col_base in df_other_universities.columns:
        df_other_universities[f'{col_base}_pct_change_prev'] = df_other_universities.groupby('Universidade')[col_base].pct_change()
        df_other_universities[f'{col_base}_diff_prev'] = df_other_universities.groupby('Universidade')[col_base].diff()
    else:
        st.warning(f"Coluna '{col_base}' não encontrada para cálculo de tendência. Será ignorada.")
        df_other_universities[f'{col_base}_pct_change_prev'] = 0.0
        df_other_universities[f'{col_base}_diff_prev'] = 0.0

# Filtra as colunas de tendência que realmente existem no DataFrame
trend_pct_change_cols = [f'{col}_pct_change_prev' for col in notas_cols_base_list + ['Nota']]
existing_trend_pct_change_cols = [col for col in trend_pct_change_cols if col in df_other_universities.columns]

# Calcula a média dessas variações por universidade
average_trends = df_other_universities.groupby('Universidade')[existing_trend_pct_change_cols].mean()

# Preenche quaisquer NaNs restantes com 0 (para universidades com histórico incompleto)
average_trends = average_trends.fillna(0)


# --- Função de Simulação ---
@st.cache_data(ttl=3600) # Cache para a função de simulação
def simulate_full_ranking_avg_trend(df_base_edicao_6, model, ufpe_name, average_trends_df,
                                    pct_change_ensino, pct_change_pesquisa, pct_change_mercado,
                                    pct_change_inovacao, pct_change_internacionalizacao,
                                    apply_other_uni_trends=True): # NOVO: Parâmetro para aplicar tendências

    df_simulated_edicao = df_base_edicao_6.copy()

    # Prepara as variações da UFPE
    ufpe_pct_changes = {
        'Nota em Ensino': pct_change_ensino,
        'Nota em Pesquisa': pct_change_pesquisa,
        'Nota em Mercado': pct_change_mercado,
        'Nota em Inovação': pct_change_inovacao,
        'Nota em Internacionalização': pct_change_internacionalizacao
    }

    # Garante que as colunas de diferença e pct_change estejam presentes e inicializadas
    for col_base in notas_cols_base_list + ['Nota']:
        if f'{col_base}_diff_prev' not in df_simulated_edicao.columns:
            df_simulated_edicao[f'{col_base}_diff_prev'] = 0.0
        if f'{col_base}_pct_change_prev' not in df_simulated_edicao.columns:
            df_simulated_edicao[f'{col_base}_pct_change_prev'] = 0.0

    # Itera sobre cada universidade para aplicar as variações
    for uni_idx, uni_row in df_simulated_edicao.iterrows():
        original_uni_notes_ed6 = df_base_edicao_6.loc[uni_idx].copy() # Notas originais da Edição 6

        if uni_row['Universidade'] == ufpe_name:
            # Aplica as variações da UFPE (definidas pelos sliders)
            for col_base, pct_change_val in ufpe_pct_changes.items():
                original_note_ufpe = original_uni_notes_ed6[col_base]
                new_note_ufpe = original_note_ufpe * (1 + pct_change_val)
                df_simulated_edicao.loc[uni_idx, col_base] = new_note_ufpe
                df_simulated_edicao.loc[uni_idx, f'{col_base}_diff_prev'] = new_note_ufpe - original_note_ufpe
                if original_note_ufpe != 0:
                    df_simulated_edicao.loc[uni_idx, f'{col_base}_pct_change_prev'] = (new_note_ufpe - original_note_ufpe) / original_note_ufpe
                else:
                    df_simulated_edicao.loc[uni_idx, f'{col_base}_pct_change_prev'] = 0.0
        else:
            # Aplica as tendências médias para as outras universidades (se apply_other_uni_trends for True)
            for col_base in notas_cols_base_list:
                if apply_other_uni_trends: # NOVO: Condição para aplicar tendências
                    col_pct_change_prev = f'{col_base}_pct_change_prev'
                    if uni_row['Universidade'] in average_trends_df.index and col_pct_change_prev in average_trends_df.columns:
                        trend_pct_change = average_trends_df.loc[uni_row['Universidade'], col_pct_change_prev]
                    else:
                        trend_pct_change = 0.0 # Se não houver tendência média, assume 0% de mudança
                else:
                    trend_pct_change = 0.0 # NOVO: Força 0% de mudança se apply_other_uni_trends for False

                original_note_other = original_uni_notes_ed6[col_base]
                new_note_other = original_note_other * (1 + trend_pct_change)
                df_simulated_edicao.loc[uni_idx, col_base] = new_note_other

                df_simulated_edicao.loc[uni_idx, f'{col_base}_diff_prev'] = new_note_other - original_note_other
                if original_note_other != 0:
                    df_simulated_edicao.loc[uni_idx, f'{col_base}_pct_change_prev'] = (new_note_other - original_note_other) / original_note_other
                else:
                    df_simulated_edicao.loc[uni_idx, f'{col_base}_pct_change_prev'] = 0.0

        # Recalcular a Nota Geral e suas variações para TODAS as universidades (UFPE e outras)
        original_overall_note_uni_ed6 = original_uni_notes_ed6['Nota']
        # Soma as notas das colunas base para obter a nova nota geral
        new_overall_note_uni_simulated = df_simulated_edicao.loc[uni_idx, notas_cols_base_list].sum()
        df_simulated_edicao.loc[uni_idx, 'Nota'] = new_overall_note_uni_simulated

        df_simulated_edicao.loc[uni_idx, 'Nota_diff_prev'] = new_overall_note_uni_simulated - original_overall_note_uni_ed6
        if original_overall_note_uni_ed6 != 0:
            df_simulated_edicao.loc[uni_idx, 'Nota_pct_change_prev'] = (new_overall_note_uni_simulated - original_overall_note_uni_ed6) / original_overall_note_uni_ed6
        else:
            df_simulated_edicao.loc[uni_idx, 'Nota_pct_change_prev'] = 0.0


    # Define a Edição RUF para a simulação
    df_simulated_edicao['Edicao_RUF'] = 7

    # Garante que todas as features necessárias para o modelo estão presentes
    missing_features = [f for f in features if f not in df_simulated_edicao.columns]
    if missing_features:
        st.error(f"Erro: As seguintes features necessárias para o modelo estão faltando no DataFrame simulado: {missing_features}")
        st.stop()

    # Faz a previsão do ranking usando o modelo
    X_simulated = df_simulated_edicao[features]
    df_simulated_edicao['Predicted_Ranking'] = model.predict(X_simulated)

    # Garante que Predicted_Ranking é numérico e trata NaNs se houver
    df_simulated_edicao['Predicted_Ranking'] = pd.to_numeric(df_simulated_edicao['Predicted_Ranking'], errors='coerce').fillna(df_simulated_edicao['Predicted_Ranking'].mean())

    # Garante que os rankings são positivos
    df_simulated_edicao['Predicted_Ranking'] = df_simulated_edicao['Predicted_Ranking'].apply(lambda x: max(1, x))

    # Gerar o ranking final
    df_simulated_edicao['Simulated_Ranking'] = df_simulated_edicao['Predicted_Ranking'].rank(method='min', ascending=True).astype(int)

    return df_simulated_edicao[['Universidade', 'Simulated_Ranking', 'Predicted_Ranking', 'Nota'] + list(ufpe_pct_changes.keys())]


# --- 3. Interface do Streamlit ---
st.set_page_config(layout="wide", page_title="Simulador de Ranking RUF")

st.title("Simulador de Ranking RUF - UFPE")
st.markdown(f"Explore o impacto de mudanças nas notas da UFPE no Ranking Universitário Folha (RUF) para a Edição 7 - {get_year_from_edition(7)}.")

# --- NOVO: Quadro Resumo da UFPE (Edição 6) ---
st.subheader(f"Situação Atual da UFPE (Edição 6 - {get_year_from_edition(6)})")
summary_ufpe_ed6 = ufpe_data_edicao_6[['Ranking', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota']].iloc[0]
summary_df = pd.DataFrame({
    'Métrica': ['Ranking', 'Ensino', 'Pesquisa', 'Mercado', 'Inovação', 'Internacionalização', 'Nota Geral'],
    'Valor': [
        summary_ufpe_ed6['Ranking'],
        summary_ufpe_ed6['Nota em Ensino'],
        summary_ufpe_ed6['Nota em Pesquisa'],
        summary_ufpe_ed6['Nota em Mercado'],
        summary_ufpe_ed6['Nota em Inovação'],
        summary_ufpe_ed6['Nota em Internacionalização'],
        summary_ufpe_ed6['Nota']
    ]
})
st.dataframe(summary_df.set_index('Métrica'), hide_index=False)

st.markdown("---")
st.header(f"Configurar Simulação (Edição 7 - {get_year_from_edition(7)})") # Título atualizado
st.markdown("Ajuste as variações percentuais para as notas da UFPE na próxima edição do RUF.")

col1, col2, col3 = st.columns(3)

# --- Variáveis de estado para os sliders ---
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

# --- Função para resetar os sliders ---
def reset_sliders():
    st.session_state.pct_ensino_display = 0
    st.session_state.pct_pesquisa_display = 0
    st.session_state.pct_mercado_display = 0
    st.session_state.pct_inovacao_display = 0
    st.session_state.pct_internacionalizacao_display = 0

# Botão para resetar os sliders
st.button("Resetar Variações", on_click=reset_sliders)

# --- NOVO: Checkbox para considerar tendências de outras universidades ---
apply_other_uni_trends = st.checkbox("Considerar tendências históricas de outras universidades", value=True, help="Se marcado, as outras universidades terão suas notas ajustadas com base em suas tendências históricas médias. Se desmarcado, as notas das outras universidades permanecerão as mesmas da Edição 6.")


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
        pct_change_internacionalizacao=pct_internacionalizacao,
        apply_other_uni_trends=apply_other_uni_trends # NOVO: Passa o valor do checkbox
    )

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

    # --- Adiciona a coluna de Diferença ---
    comparison_df['Diferença'] = comparison_df[f'Edição {get_year_from_edition(7)} (Simulada)'] - comparison_df[f'Edição {get_year_from_edition(6)} (Original)']
    # Para o Ranking, a diferença negativa é uma melhoria, então invertemos o sinal para clareza
    ranking_diff_idx = comparison_df[comparison_df['Métrica'] == 'Ranking'].index
    if not ranking_diff_idx.empty:
        comparison_df.loc[ranking_diff_idx, 'Diferença'] = -comparison_df.loc[ranking_diff_idx, 'Diferença']


    st.dataframe(comparison_df.set_index('Métrica'), hide_index=False) # Mantém 'Métrica' como índice visível

    # --- Gráfico de Barras para Comparativo de Notas ---
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
