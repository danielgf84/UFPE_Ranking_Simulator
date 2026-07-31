import pandas as pd
import os
import joblib
import numpy as np
import streamlit as st # Importar st para usar st.cache_resource/data e st.error/exception/stop

# --- Configuração de Recursos ---
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
    print(f"MODEL_LOGIC_DEBUG: Tentando carregar o modelo de: {path}")
    try:
        model = joblib.load(path)
        print(f"MODEL_LOGIC_DEBUG: Modelo carregado com sucesso de {os.path.basename(path)}.")
        return model
    except Exception as e:
        st.error(f"Erro CRÍTICO ao carregar o modelo: {e}. Verifique se o arquivo '{os.path.basename(path)}' está na pasta 'data' do seu repositório e se não está corrompido.")
        st.exception(e)
        st.stop()
        return None

@st.cache_data
def load_data(path):
    print(f"MODEL_LOGIC_DEBUG: Tentando carregar os dados de: {path}")
    try:
        df = pd.read_excel(path)
        print(f"MODEL_LOGIC_DEBUG: Dados carregados com sucesso de {os.path.basename(path)}.")
        return df
    except Exception as e:
        st.error(f"Erro CRÍTICO ao carregar os dados: {e}. Verifique se o arquivo '{os.path.basename(path)}' está na pasta 'data' do seu repositório e se não está corrompido.")
        st.exception(e)
        st.stop()
        return pd.DataFrame()

# --- Função de Simulação ---
def simulate_full_ranking_avg_trend(df_base_edicao_6, model, ufpe_name, all_universities_average_trends,
                                    pct_change_ensino, pct_change_pesquisa, pct_change_mercado,
                                    pct_change_inovacao, pct_change_internacionalizacao,
                                    apply_other_uni_trends, model_expected_features):

    print("MODEL_LOGIC_DEBUG: Iniciando simulate_full_ranking_avg_trend.")
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
                    if uni_row['Universidade'] in all_universities_average_trends.index and col_pct_change_prev in all_universities_average_trends.columns:
                        trend_pct_change = all_universities_average_trends.loc[uni_row['Universidade'], col_pct_change_prev]
                    else:
                        trend_pct_change = 0.0 # Se não houver tendência média para essa uni/col, assume 0% de mudança

                    original_note_other = uni_row[col_base]
                    new_note_other = original_note_other * (1 + trend_pct_change)
                    df_simulated_edicao.loc[uni_idx, col_base] = new_note_other

        # Recalcula a Nota Geral para cada universidade após as variações
        df_simulated_edicao.loc[uni_idx, 'Nota'] = df_simulated_edicao.loc[uni_idx, notas_cols_base_list].sum()

    # --- Pré-processamento para o Modelo ---
    print("MODEL_LOGIC_DEBUG: Iniciando pré-processamento para o modelo.")
    # 1. Calcular features de diferença e percentual de mudança (para a Edição 7 em relação à Edição 6)
    # df_base_edicao_6 é o df original da Edição 6
    # df_simulated_edicao é o df da Edição 7 com as notas ajustadas

    # Garante que ambos os dataframes têm as mesmas universidades na mesma ordem para o merge
    df_base_edicao_6_sorted = df_base_edicao_6.set_index('Universidade').sort_index()
    df_simulated_edicao_sorted = df_simulated_edicao.set_index('Universidade').sort_index()

    # Lista de colunas para calcular diff/pct_change
    cols_to_compare = ['Ranking'] + notas_cols_base_list + posicao_cols_base_list

    for col in cols_to_compare:
        if col in df_base_edicao_6_sorted.columns and col in df_simulated_edicao_sorted.columns:
            # Calcula a diferença
            df_simulated_edicao_sorted[f'{col}_diff_prev'] = df_simulated_edicao_sorted[col] - df_base_edicao_6_sorted[col]
            # Calcula o percentual de mudança (evita divisão por zero)
            df_simulated_edicao_sorted[f'{col}_pct_change_prev'] = (
                df_simulated_edicao_sorted[f'{col}_diff_prev'] / df_base_edicao_6_sorted[col].replace(0, np.nan)
            ).fillna(0) # Preenche NaN (de divisão por zero) com 0

    df_simulated_edicao_processed = df_simulated_edicao_sorted.reset_index()

    # 2. Aplicar One-Hot Encoding para 'Estado' e 'Pública ou Privada'
    # As categorias devem ser as mesmas usadas no treinamento do modelo
    # Para garantir isso, é ideal ter uma lista de todas as categorias possíveis
    # Por enquanto, vamos usar o pd.get_dummies e depois alinhar com as features esperadas
    df_simulated_edicao_processed = pd.get_dummies(df_simulated_edicao_processed, columns=['Estado', 'Pública ou Privada'], drop_first=False)
    print("MODEL_LOGIC_DEBUG: One-Hot Encoding aplicado.")

    # 3. Alinhar colunas com as features esperadas pelo modelo
    # Isso é CRÍTICO para evitar o 'feature_names mismatch'
    X_simulated = pd.DataFrame(columns=model_expected_features)

    for feature in model_expected_features:
        if feature in df_simulated_edicao_processed.columns:
            X_simulated[feature] = df_simulated_edicao_processed[feature]
        else:
            # Se uma feature esperada pelo modelo não existe nos dados simulados,
            # preenche com 0.0 (comum para colunas de OHE que não apareceram na simulação)
            # ou com a média/mediana da feature no conjunto de treinamento.
            # Para OHE, 0.0 é o mais seguro. Para outras, pode precisar de mais inteligência.
            X_simulated[feature] = 0.0

    # Garante que a ordem das colunas é a mesma do treinamento
    X_simulated = X_simulated[model_expected_features]
    print(f"MODEL_LOGIC_DEBUG: X_simulated preparado com {len(X_simulated.columns)} colunas.")

    # 4. Fazer a previsão
    print("MODEL_LOGIC_DEBUG: Realizando previsão com o modelo.")
    predicted_ranking = model.predict(X_simulated)
    df_simulated_edicao['Simulated_Ranking'] = predicted_ranking

    # Ordenar pelo ranking simulado
    df_simulated_edicao = df_simulated_edicao.sort_values(by='Simulated_Ranking').reset_index(drop=True)
    df_simulated_edicao['Simulated_Ranking'] = df_simulated_edicao.index + 1 # Atribui o ranking baseado na ordem
    print("MODEL_LOGIC_DEBUG: Simulação concluída.")
    return df_simulated_edicao

# --- Função para calcular tendências médias ---
def calculate_average_trends(df_full, latest_edition):
    print("MODEL_LOGIC_DEBUG: Iniciando calculate_average_trends.")
    df_prev_edition = df_full[df_full['Edicao_RUF'] == latest_edition - 1].set_index('Universidade')
    df_current_edition = df_full[df_full['Edicao_RUF'] == latest_edition].set_index('Universidade')

    # Alinha os índices para garantir que estamos comparando as mesmas universidades
    common_universities = df_prev_edition.index.intersection(df_current_edition.index)
    df_prev_edition = df_prev_edition.loc[common_universities]
    df_current_edition = df_current_edition.loc[common_universities]

    # Colunas para calcular as tendências
    cols_to_trend = ['Ranking', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota',
                     'Posição em Ensino', 'Posição em Pesquisa', 'Posição em Mercado', 'Posição em Inovação', 'Posição em Internacionalização']

    average_trends_data = {}
    for col in cols_to_trend:
        if col in df_prev_edition.columns and col in df_current_edition.columns:
            diff = df_current_edition[col] - df_prev_edition[col]
            pct_change = (diff / df_prev_edition[col].replace(0, np.nan)).fillna(0) # Evita divisão por zero

            average_trends_data[f'{col}_diff_prev'] = diff
            average_trends_data[f'{col}_pct_change_prev'] = pct_change

    average_trends_df = pd.DataFrame(average_trends_data)
    print("MODEL_LOGIC_DEBUG: calculate_average_trends concluída.")
    return average_trends_df
