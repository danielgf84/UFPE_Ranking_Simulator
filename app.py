import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np
import altair as alt

st.set_page_config(layout="wide")

st.success("DEBUG: 0. App started and imports complete.")

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

        # Recalcula a Nota Geral para cada universidade após as variações
        # Assumindo que 'Nota' é a soma das notas individuais para simplificar.
        # Se o cálculo for diferente, ajustar aqui.
        df_simulated_edicao.loc[uni_idx, 'Nota'] = df_simulated_edicao.loc[uni_idx, notas_cols_base_list].sum()


    # --- Preparação para o Modelo ---
    # 1. Calcular features de diferença e percentual de mudança para a Edição 7 (simulada) em relação à Edição 6 (base)
    # Isso é crucial para o modelo XGBoost que espera essas features.
    df_simulated_edicao_processed = df_simulated_edicao.copy()

    # Merge com os dados da Edição 6 para calcular as diferenças e % de mudança
    df_simulated_edicao_processed = pd.merge(
        df_simulated_edicao_processed,
        df_base_edicao_6[['Universidade', 'Ranking'] + notas_cols_base_list + posicao_cols_base_list + ['Nota']],
        on='Universidade',
        suffixes=('', '_prev')
    )

    # Calcula as features _diff_prev e _pct_change_prev
    for col in ['Ranking'] + notas_cols_base_list + posicao_cols_base_list + ['Nota']:
        if f'{col}_prev' in df_simulated_edicao_processed.columns:
            df_simulated_edicao_processed[f'{col}_diff_prev'] = df_simulated_edicao_processed[col] - df_simulated_edicao_processed[f'{col}_prev']
            # Evita divisão por zero
            df_simulated_edicao_processed[f'{col}_pct_change_prev'] = df_simulated_edicao_processed.apply(
                lambda row: (row[col] - row[f'{col}_prev']) / row[f'{col}_prev'] if row[f'{col}_prev'] != 0 else 0, axis=1
            )
        else:
            # Se a coluna _prev não existe (ex: para a primeira edição), preenche com 0
            df_simulated_edicao_processed[f'{col}_diff_prev'] = 0
            df_simulated_edicao_processed[f'{col}_pct_change_prev'] = 0

    # 2. Aplicar One-Hot Encoding para 'Estado' e 'Pública ou Privada'
    # É importante que as colunas geradas aqui sejam as mesmas que o modelo esperava.
    # Vamos criar todas as colunas possíveis que o modelo pode ter visto, preenchendo com 0 se não existirem.
    # Primeiro, identificamos as colunas de estado e pública/privada esperadas pelo modelo.
    state_features = [f for f in model_expected_features if f.startswith('Estado_')]
    public_private_features = [f for f in model_expected_features if f.startswith('Pública ou Privada_')]

    # Aplica One-Hot Encoding para as colunas categóricas
    df_simulated_edicao_processed = pd.get_dummies(df_simulated_edicao_processed, columns=['Estado', 'Pública ou Privada'], drop_first=False)

    # Garante que todas as colunas de estado e pública/privada esperadas pelo modelo existam, preenchendo com 0
    for feature in state_features + public_private_features:
        if feature not in df_simulated_edicao_processed.columns:
            df_simulated_edicao_processed[feature] = 0

    # 3. Selecionar e ordenar as colunas para a previsão
    # Garante que X_simulated tenha EXATAMENTE as mesmas colunas e na mesma ordem que o modelo espera.
    # Se alguma feature esperada pelo modelo não foi gerada, ela será adicionada com 0.
    for feature in model_expected_features:
        if feature not in df_simulated_edicao_processed.columns:
            df_simulated_edicao_processed[feature] = 0.0 # Preenche com 0.0 para features numéricas

    # 4. Fazer a previsão
    X_simulated = df_simulated_edicao_processed[model_expected_features]

    try:
        predicted_ranking = model.predict(X_simulated)
        df_simulated_edicao['Simulated_Ranking'] = predicted_ranking
    except Exception as e:
        st.error(f"Erro ao realizar a previsão do ranking com o modelo: {e}. Verifique se as features de entrada correspondem às features esperadas pelo modelo.")
        st.exception(e)
        st.stop()

    # Ordenar pelo ranking simulado
    df_simulated_edicao = df_simulated_edicao.sort_values(by='Simulated_Ranking').reset_index(drop=True)
    df_simulated_edicao['Simulated_Ranking'] = df_simulated_edicao.index + 1 # Atribui o ranking baseado na ordem

    return df_simulated_edicao

# --- Execução Principal ---
st.success("DEBUG: 1. Model and data loading functions called.")
loaded_model = load_model(model_path)
df_full = load_data(input_file_path)
st.success("DEBUG: 2. Model and data loaded successfully and checked.")

# Verifica se o modelo e os dados foram carregados
if loaded_model is None or df_full.empty:
    st.error("Erro crítico: Modelo ou dados não puderam ser carregados. Verifique os logs acima.")
    st.stop()

# Tenta obter as features esperadas pelo modelo
try:
    model_expected_features = loaded_model.feature_names_in_
    if model_expected_features is None:
        st.error("Erro: Não foi possível obter as feature_names_in_ do modelo. O modelo pode não ter sido treinado com essa propriedade.")
        st.stop()
    st.success(f"DEBUG: Features esperadas pelo modelo obtidas. Total: {len(model_expected_features)}")
except Exception as e:
    st.error(f"Erro ao tentar obter as feature_names_in_ do modelo: {e}. O modelo pode não ter sido treinado com essa propriedade.")
    st.exception(e)
    st.stop()


# --- Processamento de Dados ---
st.success("DEBUG: 3. Latest edition determined.")
latest_edition = df_full['Edicao_RUF'].max()

st.success(f"DEBUG: 4. Data for latest edition ({latest_edition}) extracted. Total: {len(df_full[df_full['Edicao_RUF'] == latest_edition])} universities.")
df_edicao_6 = df_full[df_full['Edicao_RUF'] == latest_edition].copy()

st.success("DEBUG: Dados da UFPE para a Edição 6 extraídos.")
ufpe_data_ed6_check = df_edicao_6[df_edicao_6['Universidade'] == ufpe_exact_name]
if ufpe_data_ed6_check.empty:
    st.error(f"Erro: Não foi possível encontrar a '{ufpe_exact_name}' na Edição {latest_edition} dos dados. Verifique o nome da universidade ou os dados.")
    st.stop()
original_ufpe_ed6 = ufpe_data_ed6_check.iloc[0]

st.success("DEBUG: Tendências médias para outras universidades calculadas.")
# Cálculo das Tendências Médias para Outras Universidades
# Exclui a UFPE do cálculo das tendências médias
df_others = df_full[df_full['Universidade'] != ufpe_exact_name].copy()

# Calcula a variação percentual entre a penúltima e a última edição para as outras universidades
# Assumindo que 'latest_edition - 1' é a penúltima edição
df_penultima_edicao = df_others[df_others['Edicao_RUF'] == latest_edition - 1].set_index('Universidade')
df_ultima_edicao = df_others[df_others['Edicao_RUF'] == latest_edition].set_index('Universidade')

# Colunas para calcular a tendência
cols_to_trend = ['Ranking', 'Nota', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização',
                 'Posição em Ensino', 'Posição em Pesquisa', 'Posição em Mercado', 'Posição em Inovação', 'Posição em Internacionalização']

average_trends = pd.DataFrame(index=df_ultima_edicao.index)

for col in cols_to_trend:
    if col in df_penultima_edicao.columns and col in df_ultima_edicao.columns:
        # Calcula a diferença
        average_trends[f'{col}_diff_prev'] = df_ultima_edicao[col] - df_penultima_edicao[col]
        # Calcula a variação percentual, evitando divisão por zero
        average_trends[f'{col}_pct_change_prev'] = df_ultima_edicao.apply(
            lambda row: (row[col] - df_penultima_edicao.loc[row.name, col]) / df_penultima_edicao.loc[row.name, col] if df_penultima_edicao.loc[row.name, col] != 0 else 0, axis=1
        )
    else:
        # Se a coluna não existe em uma das edições, preenche com 0
        average_trends[f'{col}_diff_prev'] = 0
        average_trends[f'{col}_pct_change_prev'] = 0

# --- Interface do Streamlit ---
st.title("Simulador de Ranking RUF para a UFPE")

st.success("DEBUG: 5. Preparing UFPE summary table.")
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
    st.success("DEBUG: 6. UFPE summary table data prepared.")
except Exception as e:
    st.error(f"Erro ao preparar os dados da UFPE para exibição: {e}. Verifique se as colunas esperadas existem e contêm valores válidos.")
    st.exception(e)
    st.stop()

st.subheader(f"Desempenho da UFPE na Edição {get_year_from_edition(latest_edition)} (Original)")
st.dataframe(original_ufpe_ed6_display, hide_index=True)
st.success("DEBUG: 7. UFPE summary table displayed.")

st.sidebar.header("Ajustar Variações para a UFPE (Edição Simulada)")

# Inicializa st.session_state para sliders e checkbox
if 'pct_change_ensino' not in st.session_state:
    st.session_state.pct_change_ensino = 0.0
if 'pct_change_pesquisa' not in st.session_state:
    st.session_state.pct_change_pesquisa = 0.0
if 'pct_change_mercado' not in st.session_state:
    st.session_state.pct_change_mercado = 0.0
if 'pct_change_inovacao' not in st.session_state:
    st.session_state.pct_change_inovacao = 0.0
if 'pct_change_internacionalizacao' not in st.session_state:
    st.session_state.pct_change_internacionalizacao = 0.0
if 'apply_other_uni_trends' not in st.session_state:
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
