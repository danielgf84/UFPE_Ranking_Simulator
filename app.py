import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np
import altair as alt

st.set_page_config(layout="wide") # Garante que a configuração da página seja a primeira coisa a ser definida

st.success("DEBUG: 0. App started and imports complete.") # Mensagem de sucesso bem no início

# --- 1. Configuração e Carregamento de Recursos ---
data_path = 'data'
model_path = os.path.join(data_path, 'xgboost_model.pkl')
input_file_name = 'ruf_consolidado_fe.xlsx'
input_file_path = os.path.join(data_path, input_file_name)

ufpe_exact_name = 'Universidade Federal de Pernambuco'
target_column = 'Ranking'

EDITION_YEAR_MAP = {
    1: 2017, 2: 2018, 3: 2019, 4: 2023, 5: 2024, 6: 2025, 7: 2026
}

def get_year_from_edition(edition_number):
    return EDITION_YEAR_MAP.get(edition_number, f"Ano Desconhecido (Edição {edition_number})")

# --- Funções de Carregamento (com cache para Streamlit) ---
@st.cache_resource
def load_model(path):
    try:
        model = joblib.load(path)
        st.success(f"DEBUG: Modelo carregado com sucesso de {os.path.basename(path)}.")
        return model
    except Exception as e:
        st.error(f"Erro CRÍTICO ao carregar o modelo: {e}. Verifique se o arquivo '{os.path.basename(path)}' está na pasta 'data' do seu repositório e se não está corrompido.")
        st.exception(e)
        st.stop()

@st.cache_data
def load_data(path):
    try:
        df = pd.read_excel(path)
        st.success(f"DEBUG: Dados carregados com sucesso de {os.path.basename(path)}.")
        return df
    except Exception as e:
        st.error(f"Erro CRÍTICO ao carregar os dados: {e}. Verifique se o arquivo '{os.path.basename(path)}' está na pasta 'data' do seu repositório e se não está corrompido.")
        st.exception(e)
        st.stop()
        return pd.DataFrame()

# --- NOVO: Função de Simulação ---
def simulate_full_ranking_avg_trend(df_base_edicao_6, model, ufpe_name, all_universities_average_trends,
                                    pct_change_ensino, pct_change_pesquisa, pct_change_mercado,
                                    pct_change_inovacao, pct_change_internacionalizacao,
                                    apply_other_uni_trends, model_expected_features):

    df_simulated_edicao = df_base_edicao_6.copy()

    notas_cols_base_list = ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']
    posicao_cols_base_list = ['Posição em Ensino', 'Posição em Pesquisa', 'Posição em Mercado', 'Posição em Inovação', 'Posição em Internacionalização']

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

        # Recalcula a Nota Geral (assumindo que é a soma das notas individuais)
        df_simulated_edicao.loc[uni_idx, 'Nota'] = df_simulated_edicao.loc[uni_idx, notas_cols_base_list].sum()

    # --- Preparação dos dados para o modelo XGBoost ---
    # 1. Calcular features de diferença e percentual de mudança (Edição 7 vs Edição 6)
    # df_base_edicao_6 já tem os dados da Edição 6.
    # df_simulated_edicao tem os dados da Edição 7 (simulados).

    # Para cada universidade, precisamos calcular a diferença e o pct_change
    # entre a Edição 6 (original) e a Edição 7 (simulada) para as features que o modelo espera.
    # Isso é um pouco complexo, pois o modelo espera '_prev' (em relação à edição anterior),
    # e aqui estamos simulando a 'próxima' edição.
    # A forma mais robusta é garantir que df_simulated_edicao contenha todas as colunas
    # que o modelo espera, incluindo as 'Posição em X' e as 'Estado_Y', 'Pública ou Privada_Z'.

    # Para simplificar e resolver o 'feature_names mismatch' imediatamente:
    # Vamos criar um DataFrame com as colunas que o modelo espera, preenchendo com valores
    # da Edição 6 e ajustando as notas da UFPE e outras conforme a simulação.

    # Garantir que df_simulated_edicao tenha todas as colunas necessárias para o modelo
    # (Posições, Estado, Pública ou Privada, e as features _diff_prev, _pct_change_prev)

    # Adicionar colunas de Posição (se não existirem, ou recalcular se as notas mudaram)
    # Por simplicidade, vamos assumir que as posições são calculadas com base nas notas.
    # Se o modelo usa posições, elas precisam ser geradas.
    # Se o seu modelo foi treinado com 'Posição em Ensino', etc., e você só tem 'Nota em Ensino',
    # você precisará de uma lógica para calcular essas posições a partir das notas.
    # Por enquanto, vamos copiar as posições da Edição 6 e ajustá-las se necessário.
    for col in posicao_cols_base_list:
        if col not in df_simulated_edicao.columns:
            df_simulated_edicao[col] = df_base_edicao_6[col] # Copia da edição base

    # Adicionar colunas categóricas (Estado, Pública ou Privada)
    # Primeiro, garantir que as colunas originais 'Estado' e 'Pública ou Privada' existam
    if 'Estado' not in df_simulated_edicao.columns:
        df_simulated_edicao['Estado'] = df_base_edicao_6['Estado']
    if 'Pública ou Privada' not in df_simulated_edicao.columns:
        df_simulated_edicao['Pública ou Privada'] = df_base_edicao_6['Pública ou Privada']

    # Criar um DataFrame para o One-Hot Encoding
    df_ohe = pd.get_dummies(df_simulated_edicao[['Estado', 'Pública ou Privada']], prefix=['Estado', 'Pública ou Privada'])
    df_simulated_edicao_processed = pd.concat([df_simulated_edicao.drop(columns=['Estado', 'Pública ou Privada']), df_ohe], axis=1)

    # Calcular as features _diff_prev e _pct_change_prev
    # Estas features são calculadas em relação à Edição 6 (df_base_edicao_6)
    # É crucial que as colunas de df_base_edicao_6 e df_simulated_edicao estejam alinhadas pela 'Universidade'
    df_merged = pd.merge(df_base_edicao_6[['Universidade', 'Ranking'] + notas_cols_base_list + posicao_cols_base_list],
                         df_simulated_edicao_processed[['Universidade', 'Ranking'] + notas_cols_base_list + posicao_cols_base_list],
                         on='Universidade', suffixes=('_prev', ''))

    # Calcula as diferenças e percentuais de mudança
    features_to_diff_pct = ['Ranking'] + notas_cols_base_list + posicao_cols_base_list
    for feature in features_to_diff_pct:
        df_merged[f'{feature}_diff_prev'] = df_merged[feature] - df_merged[f'{feature}_prev']
        df_merged[f'{feature}_pct_change_prev'] = (df_merged[feature] - df_merged[f'{feature}_prev']) / df_merged[f'{feature}_prev'].replace(0, np.nan) # Evita divisão por zero
        df_merged[f'{feature}_pct_change_prev'] = df_merged[f'{feature}_pct_change_prev'].fillna(0) # Preenche NaN com 0

    # Adicionar essas novas features ao df_simulated_edicao_processed
    df_simulated_edicao_processed = pd.merge(df_simulated_edicao_processed,
                                             df_merged[['Universidade'] + [col for col in df_merged.columns if '_diff_prev' in col or '_pct_change_prev' in col]],
                                             on='Universidade', how='left')

    # Garantir que todas as colunas esperadas pelo modelo existam, preenchendo com 0 se necessário
    for feature in model_expected_features:
        if feature not in df_simulated_edicao_processed.columns:
            df_simulated_edicao_processed[feature] = 0.0 # Preenche com 0, pode precisar de ajuste dependendo da feature

    # Alinhar as colunas de X_simulated com as features esperadas pelo modelo
    X_simulated = df_simulated_edicao_processed[model_expected_features]

    # Fazer a previsão
    predicted_ranking = model.predict(X_simulated)
    df_simulated_edicao['Simulated_Ranking'] = predicted_ranking

    # Ordenar pelo ranking simulado
    df_simulated_edicao = df_simulated_edicao.sort_values(by='Simulated_Ranking').reset_index(drop=True)
    df_simulated_edicao['Simulated_Ranking'] = df_simulated_edicao.index + 1 # Atribui o ranking baseado na ordem

    return df_simulated_edicao

# --- Início do Aplicativo Streamlit ---
st.title("Simulador de Ranking RUF para a UFPE")

# Carregar modelo e dados
loaded_model = load_model(model_path)
df_full = load_data(input_file_path)

# Verificar se o modelo e os dados foram carregados com sucesso
if loaded_model is None or df_full.empty:
    st.error("Não foi possível carregar o modelo ou os dados. Verifique os logs para mais detalhes.")
    st.stop()

st.success("DEBUG: Modelo e dados carregados e verificados.")

# Extrair as features esperadas pelo modelo (do próprio modelo)
try:
    model_expected_features = loaded_model.get_booster().feature_names
    if not model_expected_features:
        st.error("O modelo carregado não possui 'feature_names'. Não é possível prosseguir.")
        st.stop()
    st.success(f"DEBUG: Features esperadas pelo modelo extraídas. Total: {len(model_expected_features)}")
except Exception as e:
    st.error(f"Erro ao extrair feature_names do modelo: {e}")
    st.exception(e)
    st.stop()


# Encontrar a última edição disponível nos dados
latest_edition = df_full['Edicao_RUF'].max()
st.success(f"DEBUG: Última edição encontrada: {latest_edition}")

# Filtrar dados da última edição para usar como base
df_edicao_6 = df_full[df_full['Edicao_RUF'] == latest_edition].copy()
if df_edicao_6.empty:
    st.error(f"Não foram encontrados dados para a Edição {latest_edition}. Verifique o arquivo de dados.")
    st.stop()
st.success(f"DEBUG: Dados da Edição {latest_edition} extraídos. {len(df_edicao_6)} universidades.")

# Extrair dados da UFPE para a última edição
original_ufpe_ed6 = df_edicao_6[df_edicao_6['Universidade'] == ufpe_exact_name]
if original_ufpe_ed6.empty:
    st.error(f"A universidade '{ufpe_exact_name}' não foi encontrada na Edição {latest_edition}. Verifique o nome ou os dados.")
    st.stop()
original_ufpe_ed6 = original_ufpe_ed6.iloc[0]
st.success(f"DEBUG: Dados da UFPE para a Edição {latest_edition} extraídos.")

# Cálculo das Tendências Médias para Outras Universidades (se aplicável)
# Esta lógica precisa ser robusta para o caso de não haver edições anteriores suficientes
try:
    if latest_edition > 1:
        df_prev_edition = df_full[df_full['Edicao_RUF'] == latest_edition - 1].copy()
        if not df_prev_edition.empty:
            df_merged_trends = pd.merge(df_prev_edition[['Universidade', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']],
                                        df_edicao_6[['Universidade', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']],
                                        on='Universidade', suffixes=('_prev', ''))

            # Calcular percentual de mudança para cada nota
            for col in ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']:
                df_merged_trends[f'{col}_pct_change_prev'] = (df_merged_trends[col] - df_merged_trends[f'{col}_prev']) / df_merged_trends[f'{col}_prev'].replace(0, np.nan)
                df_merged_trends[f'{col}_pct_change_prev'] = df_merged_trends[f'{col}_pct_change_prev'].fillna(0)

            average_trends = df_merged_trends.set_index('Universidade')
            st.success("DEBUG: Tendências médias para outras universidades calculadas.")
        else:
            average_trends = pd.DataFrame() # DataFrame vazio se não houver edição anterior
            st.warning("DEBUG: Não há dados da edição anterior para calcular tendências médias.")
    else:
        average_trends = pd.DataFrame() # DataFrame vazio se for a primeira edição
        st.warning("DEBUG: Não há edições anteriores para calcular tendências médias.")
except Exception as e:
    st.error(f"Erro ao calcular tendências médias: {e}")
    st.exception(e)
    st.stop()


st.sidebar.header(f"Simulação para Edição {get_year_from_edition(latest_edition + 1)}")

pct_change_ensino = st.sidebar.slider("Ensino (%)", -10.0, 10.0, 0.0, 0.1) / 100
pct_change_pesquisa = st.sidebar.slider("Pesquisa (%)", -10.0, 10.0, 0.0, 0.1) / 100
pct_change_mercado = st.sidebar.slider("Mercado (%)", -10.0, 10.0, 0.0, 0.1) / 100
pct_change_inovacao = st.sidebar.slider("Inovação (%)", -10.0, 10.0, 0.0, 0.1) / 100
pct_change_internacionalizacao = st.sidebar.slider("Internacionalização (%)", -10.0, 10.0, 0.0, 0.1) / 100

apply_other_uni_trends = st.sidebar.checkbox("Aplicar tendências médias a outras universidades", value=True)

if st.sidebar.button("Resetar Variações"):
    st.session_state.pct_change_ensino = 0.0
    st.session_state.pct_change_pesquisa = 0.0
    st.session_state.pct_change_mercado = 0.0
    st.session_state.pct_change_inovacao = 0.0
    st.session_state.pct_change_internacionalizacao = 0.0
    st.session_state.apply_other_uni_trends = True
    st.experimental_rerun()

if st.button("Executar Simulação"):
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
            'Métrica': ['Ranking', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota Geral'],
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
