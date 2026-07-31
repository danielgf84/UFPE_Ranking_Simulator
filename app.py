import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np
import altair as alt

# --- 1. Configuração e Carregamento de Recursos ---
# O caminho para a sua pasta 'data' no repositório GitHub
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
                                    apply_other_uni_trends, model_expected_features): # Adicionado model_expected_features

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

    # Itera sobre cada universidade para aplicar as variações ou tendências
    for uni_idx, uni_row in df_simulated_edicao.iterrows():
        if uni_row['Universidade'] == ufpe_name:
            # Aplica as variações da UFPE (definidas pelos sliders)
            for col_base, pct_change_val in ufpe_pct_changes.items():
                original_note_ufpe = uni_row[col_base]
                new_note_ufpe = original_note_ufpe * (1 + pct_change_val)
                df_simulated_edicao.loc[uni_idx, col_base] = new_note_ufpe
        else:
            # Aplica as tendências médias para as outras universidades, se o checkbox estiver marcado
            if apply_other_uni_trends:
                for col_base in notas_cols_base_list:
                    col_pct_change_prev = f'{col_base}_pct_change_prev'
                    # Verifica se a universidade e a coluna de tendência existem no DataFrame de tendências
                    if uni_row['Universidade'] in all_universities_average_trends.index and col_pct_change_prev in all_universities_average_trends.columns:
                        trend_pct_change = all_universities_average_trends.loc[uni_row['Universidade'], col_pct_change_prev]
                    else:
                        trend_pct_change = 0.0 # Se não houver tendência média para essa uni/col, assume 0% de mudança

                    original_note_other = uni_row[col_base]
                    new_note_other = original_note_other * (1 + trend_pct_change)
                    df_simulated_edicao.loc[uni_idx, col_base] = new_note_other
            # Se apply_other_uni_trends for False, as notas das outras universidades permanecem as mesmas da Edição 6

        # Recalcula a Nota Geral para cada universidade após as variações
        # Assumindo que 'Nota' é a soma das notas individuais. Ajuste se o cálculo for diferente.
        df_simulated_edicao.loc[uni_idx, 'Nota'] = df_simulated_edicao.loc[uni_idx, notas_cols_base_list].sum()

    # Recalcular Posições para a Edição 7 simulada
    for col in notas_cols_base_list + ['Nota']:
        df_simulated_edicao[f'Posição em {col.replace("Nota em ", "")}'] = df_simulated_edicao[col].rank(ascending=False).astype(int)

    # --- Preparar Features para o Modelo XGBoost ---
    # 1. Calcular features de diferença e percentual de mudança (Edição 7 vs Edição 6)
    #    Para isso, precisamos do df_base_edicao_6 original para cada universidade.
    #    Vamos juntar os dois DataFrames para facilitar o cálculo.

    # Renomear colunas do df_base_edicao_6 para evitar conflitos
    df_base_edicao_6_renamed = df_base_edicao_6.add_suffix('_ed6')
    df_base_edicao_6_renamed = df_base_edicao_6_renamed.rename(columns={'Universidade_ed6': 'Universidade'})

    df_merged = pd.merge(df_simulated_edicao, df_base_edicao_6_renamed, on='Universidade', how='left')

    # Lista de colunas para calcular _diff_prev e _pct_change_prev
    cols_for_diff_pct = ['Ranking', 'Nota'] + notas_cols_base_list + posicao_cols_base_list

    for col in cols_for_diff_pct:
        # Diferença: Edição 7 (simulada) - Edição 6 (original)
        df_merged[f'{col}_diff_prev'] = df_merged[col] - df_merged[f'{col}_ed6']

        # Percentual de mudança: (Edição 7 - Edição 6) / Edição 6
        # Evitar divisão por zero
        df_merged[f'{col}_pct_change_prev'] = df_merged.apply(
            lambda row: (row[col] - row[f'{col}_ed6']) / row[f'{col}_ed6'] if row[f'{col}_ed6'] != 0 else 0,
            axis=1
        )

    # 2. Aplicar One-Hot Encoding para 'Estado' e 'Pública ou Privada'
    #    É CRUCIAL que as colunas geradas aqui sejam as mesmas que o modelo foi treinado.
    #    Vamos assumir que o modelo foi treinado com todos os estados e tipos de instituição presentes no df_merged.

    # Criar um DataFrame temporário para o OHE
    df_ohe = df_merged[['Universidade', 'Estado', 'Pública ou Privada']].copy()
    df_ohe = pd.get_dummies(df_ohe, columns=['Estado', 'Pública ou Privada'], prefix=['Estado', 'Pública ou Privada'])

    # Juntar de volta ao df_merged
    df_simulated_edicao_processed = pd.merge(df_merged, df_ohe.drop(columns=['Universidade']), left_index=True, right_index=True, how='left')

    # 3. Garantir que todas as colunas esperadas pelo modelo existam e preencher as ausentes
    #    Isso é vital para o 'feature_names mismatch'.

    # Lista de features que o modelo espera (obtida do erro anterior)
    # É importante que esta lista seja EXATA.
    # Se o modelo foi treinado com um conjunto fixo de estados, precisamos garantir que
    # todas essas colunas de estado existam, mesmo que com valor 0.

    # Vamos extrair a lista de features do próprio modelo se possível, ou usar a que você me deu.
    # Para o XGBoost, o modelo tem um atributo feature_names_in_
    try:
        model_expected_features_from_model = list(model.get_booster().feature_names)
    except AttributeError:
        # Se não tiver, usamos a lista do erro. É importante que esta lista seja EXATA.
        # Eu vou usar a lista que você me forneceu no erro, mas a ordem é crucial.
        # A ordem que o erro 'expected' mostra é a ordem que o modelo espera.
        # Copiei a lista 'expected' do seu erro.
        model_expected_features_from_model = [
            'Posição em Ensino', 'Nota em Ensino', 'Posição em Pesquisa', 'Nota em Pesquisa',
            'Posição em Mercado', 'Nota em Mercado', 'Posição em Inovação', 'Nota em Inovação',
            'Posição em Internacionalização', 'Nota em Internacionalização', 'Nota',
            'Estado_AL', 'Estado_AM', 'Estado_AP', 'Estado_BA', 'Estado_CE', 'Estado_DF',
            'Estado_ES', 'Estado_GO', 'Estado_MA', 'Estado_MG', 'Estado_MS', 'Estado_MT',
            'Estado_PA', 'Estado_PB', 'Estado_PE', 'Estado_PI', 'Estado_PR', 'Estado_RJ',
            'Estado_RN', 'Estado_RO', 'Estado_RR', 'Estado_RS', 'Estado_SC', 'Estado_SE',
            'Estado_SP', 'Estado_TO',
            'Pública ou Privada_Federal', 'Pública ou Privada_Municipal', 'Pública ou Privada_Privada',
            'Ranking_diff_prev', 'Ranking_pct_change_prev',
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

    # Adicionar colunas ausentes e preencher com 0
    for feature in model_expected_features_from_model:
        if feature not in df_simulated_edicao_processed.columns:
            df_simulated_edicao_processed[feature] = 0

    # 4. Selecionar e ordenar as colunas para X_simulated
    X_simulated = df_simulated_edicao_processed[model_expected_features_from_model]

    # 5. Fazer a previsão
    try:
        predicted_ranking = model.predict(X_simulated)
        df_simulated_edicao['Simulated_Ranking'] = predicted_ranking
    except Exception as e:
        st.error(f"Erro ao realizar a previsão do ranking com o modelo: {e}")
        st.exception(e)
        st.stop()

    # Ordenar pelo ranking simulado
    df_simulated_edicao = df_simulated_edicao.sort_values(by='Simulated_Ranking').reset_index(drop=True)
    df_simulated_edicao['Simulated_Ranking'] = df_simulated_edicao.index + 1 # Atribui o ranking baseado na ordem

    return df_simulated_edicao


# --- Início do Aplicativo Streamlit ---
st.set_page_config(layout="wide", page_title="Simulador de Ranking RUF UFPE")

st.title("📊 Simulador de Ranking RUF - UFPE")
st.markdown("Este aplicativo permite simular o impacto de mudanças nas notas da UFPE nas dimensões do Ranking Universitário Folha (RUF) para a próxima edição.")

# Carregar modelo e dados
loaded_model = load_model(model_path)
df_full = load_data(input_file_path)

# Verifica se o modelo e os dados foram carregados com sucesso
if loaded_model is None or df_full.empty:
    st.error("Não foi possível carregar o modelo ou os dados. Verifique os logs para mais detalhes.")
    st.stop()

# --- Extrair features esperadas pelo modelo ---
# É crucial que esta lista seja EXATA.
# Se o modelo foi treinado com um conjunto fixo de estados, precisamos garantir que
# todas essas colunas de estado existam, mesmo que com valor 0.
# Copiei a lista 'expected' do seu erro.
model_expected_features = [
    'Posição em Ensino', 'Nota em Ensino', 'Posição em Pesquisa', 'Nota em Pesquisa',
    'Posição em Mercado', 'Nota em Mercado', 'Posição em Inovação', 'Nota em Inovação',
    'Posição em Internacionalização', 'Nota em Internacionalização', 'Nota',
    'Estado_AL', 'Estado_AM', 'Estado_AP', 'Estado_BA', 'Estado_CE', 'Estado_DF',
    'Estado_ES', 'Estado_GO', 'Estado_MA', 'Estado_MG', 'Estado_MS', 'Estado_MT',
    'Estado_PA', 'Estado_PB', 'Estado_PE', 'Estado_PI', 'Estado_PR', 'Estado_RJ',
    'Estado_RN', 'Estado_RO', 'Estado_RR', 'Estado_RS', 'Estado_SC', 'Estado_SE',
    'Estado_SP', 'Estado_TO',
    'Pública ou Privada_Federal', 'Pública ou Privada_Municipal', 'Pública ou Privada_Privada',
    'Ranking_diff_prev', 'Ranking_pct_change_prev',
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


# --- Pré-processamento dos Dados ---
# Garante que 'Edicao_RUF' seja numérica para ordenação
df_full['Edicao_RUF'] = pd.to_numeric(df_full['Edicao_RUF'], errors='coerce')
df_full.dropna(subset=['Edicao_RUF'], inplace=True)
df_full['Edicao_RUF'] = df_full['Edicao_RUF'].astype(int)

# Última edição disponível nos dados
latest_edition = df_full['Edicao_RUF'].max()
df_latest_edition = df_full[df_full['Edicao_RUF'] == latest_edition].copy()

# Edição anterior para cálculo de tendências
previous_edition = latest_edition - 1
df_previous_edition = df_full[df_full['Edicao_RUF'] == previous_edition].copy()

# --- Cálculo das Tendências Médias para Outras Universidades ---
# Isso é usado para simular o comportamento das outras universidades
# (se o checkbox 'Aplicar tendências médias...' estiver marcado)
average_trends = pd.DataFrame()
if not df_previous_edition.empty:
    # Calcular percentual de mudança entre a penúltima e a última edição
    df_merged_trends = pd.merge(df_latest_edition, df_previous_edition, on='Universidade', suffixes=('_latest', '_prev'))

    # Colunas para calcular as tendências
    cols_to_trend = ['Ranking', 'Nota'] + ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização'] + \
                    ['Posição em Ensino', 'Posição em Pesquisa', 'Posição em Mercado', 'Posição em Inovação', 'Posição em Internacionalização']

    for col in cols_to_trend:
        df_merged_trends[f'{col}_diff_prev'] = df_merged_trends[f'{col}_latest'] - df_merged_trends[f'{col}_prev']
        df_merged_trends[f'{col}_pct_change_prev'] = df_merged_trends.apply(
            lambda row: (row[f'{col}_latest'] - row[f'{col}_prev']) / row[f'{col}_prev'] if row[f'{col}_prev'] != 0 else 0,
            axis=1
        )

    # Calcular a média das tendências para cada universidade
    # Usar a universidade como índice para facilitar a busca
    average_trends = df_merged_trends.set_index('Universidade')[[col for col in df_merged_trends.columns if '_pct_change_prev' in col or '_diff_prev' in col]]


# Dados da Edição 6 (latest_edition) para a simulação
df_edicao_6 = df_latest_edition.copy()

# Extrai os dados originais da UFPE para a Edição 6
original_ufpe_ed6 = df_edicao_6[df_edicao_6['Universidade'] == ufpe_exact_name].iloc[0]

# --- Interface do Usuário ---
st.subheader(f"Resumo da UFPE - Edição {get_year_from_edition(latest_edition)} (Original)")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Ranking", value=f"#{int(original_ufpe_ed6['Ranking'])}")
with col2:
    st.metric(label="Nota Geral", value=f"{original_ufpe_ed6['Nota']:.2f}")
with col3:
    st.metric(label="Nota em Ensino", value=f"{original_ufpe_ed6['Nota em Ensino']:.2f}")

st.markdown("---")
st.subheader(f"Simulação para a Edição {get_year_from_edition(latest_edition + 1)}")

# Sliders para ajustar as notas da UFPE
st.sidebar.header("Ajustar Notas da UFPE (Variação %)")
pct_change_ensino = st.sidebar.slider("Ensino (%)", -10.0, 10.0, 0.0, 0.1) / 100
pct_change_pesquisa = st.sidebar.slider("Pesquisa (%)", -10.0, 10.0, 0.0, 0.1) / 100
pct_change_mercado = st.sidebar.slider("Mercado (%)", -10.0, 10.0, 0.0, 0.1) / 100
pct_change_inovacao = st.sidebar.slider("Inovação (%)", -10.0, 10.0, 0.0, 0.1) / 100
pct_change_internacionalizacao = st.sidebar.slider("Internacionalização (%)", -10.0, 10.0, 0.0, 0.1) / 100

# Checkbox para aplicar tendências médias a outras universidades
apply_other_uni_trends = st.sidebar.checkbox("Aplicar tendências médias a outras universidades", value=True)

# Botão de reset
if st.sidebar.button("Resetar Variações"):
    st.session_state.pct_change_ensino = 0.0
    st.session_state.pct_change_pesquisa = 0.0
    st.session_state.pct_change_mercado = 0.0
    st.session_state.pct_change_inovacao = 0.0
    st.session_state.pct_change_internacionalizacao = 0.0
    st.session_state.apply_other_uni_trends = True
    st.experimental_rerun() # Recarrega o app para aplicar o reset

# Botão para executar a simulação
if st.button("Executar Simulação"):
    try:
        with st.spinner("Executando simulação..."):
            simulated_df = simulate_full_ranking_avg_trend(
                df_edicao_6, loaded_model, ufpe_exact_name, average_trends,
                pct_change_ensino, pct_change_pesquisa, pct_change_mercado,
                pct_change_inovacao, pct_change_internacionalizacao,
                apply_other_uni_trends, model_expected_features # Passa as features esperadas
            )

        # Extrai os dados da UFPE simulados
        simulated_ufpe_ed7 = simulated_df[simulated_df['Universidade'] == ufpe_exact_name].iloc[0]

        # Exibe o ranking simulado da UFPE
        st.metric(label=f"Ranking Simulada da UFPE (Edição {get_year_from_edition(latest_edition + 1)})", value=f"#{int(simulated_ufpe_ed7['Simulated_Ranking'])}")

        # Tabela comparativa
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

        # Adiciona a coluna de Diferença
        comparison_df['Diferença'] = comparison_df[f'Edição {get_year_from_edition(latest_edition + 1)} (Simulada)'] - comparison_df[f'Edição {get_year_from_edition(latest_edition)} (Original)']
        ranking_diff_idx = comparison_df[comparison_df['Métrica'] == 'Ranking'].index
        if not ranking_diff_idx.empty:
            # Para ranking, uma diferença positiva significa que o ranking PIOROU, então invertemos o sinal para a métrica de "melhora"
            comparison_df.loc[ranking_diff_idx, 'Diferença'] = -comparison_df.loc[ranking_diff_idx, 'Diferença']

        st.dataframe(comparison_df.set_index('Métrica'), hide_index=False)

        # Gráfico de Barras para Comparativo de Notas
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
