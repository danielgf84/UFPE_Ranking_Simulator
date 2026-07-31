# model_logic.py
import pandas as pd
import os
import joblib
import numpy as np
# import streamlit as st # REMOVIDO: Não importe st aqui

# --- Configuração de Recursos ---
# Estes caminhos serão sobrescritos pelo app.py, que usará os caminhos do Colab
# Mas é bom ter valores padrão para testes locais, se necessário.
# Vamos torná-los variáveis que podem ser passadas para as funções.
# data_path = 'data' # Será definido externamente
# model_path = os.path.join(data_path, 'xgboost_model.pkl') # Será definido externamente
# input_file_name = 'ruf_consolidado_fe.xlsx' # Será definido externamente
# input_file_path = os.path.join(data_path, input_file_name) # Será definido externamente

ufpe_exact_name = 'Universidade Federal de Pernambuco'
target_column = 'Ranking'

EDITION_YEAR_MAP = {
    1: 2017, 2: 2018, 3: 2019, 4: 2023, 5: 2024, 6: 2025, 7: 2026
}

def get_year_from_edition(edition_number):
    return EDITION_YEAR_MAP.get(edition_number, f"Ano Desconhecido (Edição {edition_number})")

# --- Funções de Carregamento (sem st.cache_resource/data aqui, serão aplicados no app.py) ---
def load_model(path):
    print(f"MODEL_LOGIC_DEBUG: Tentando carregar o modelo de: {path}")
    try:
        model = joblib.load(path)
        print(f"MODEL_LOGIC_DEBUG: Modelo carregado com sucesso de {os.path.basename(path)}.")
        return model
    except Exception as e:
        print(f"MODEL_LOGIC_ERROR: Erro CRÍTICO ao carregar o modelo: {e}. Verifique o caminho e o arquivo.")
        raise # Levanta a exceção para ser tratada no app.py

def load_data(path):
    print(f"MODEL_LOGIC_DEBUG: Tentando carregar os dados de: {path}")
    try:
        df = pd.read_excel(path)
        print(f"MODEL_LOGIC_DEBUG: Dados carregados com sucesso de {os.path.basename(path)}.")
        return df
    except Exception as e:
        print(f"MODEL_LOGIC_ERROR: Erro CRÍTICO ao carregar os dados: {e}. Verifique o caminho e o arquivo.")
        raise # Levanta a exceção para ser tratada no app.py

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
                # all_universities_average_trends é um DataFrame com o índice 'Universidade'
                # e colunas como 'Nota em Ensino_pct_change_prev'
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
        # ATENÇÃO: Se a 'Nota' é calculada de forma mais complexa no RUF, ajuste aqui.
        # Por enquanto, soma simples das notas das dimensões.
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
    # Inclui 'Ranking' e as notas e posições das dimensões
    cols_to_compare = ['Ranking'] + notas_cols_base_list + posicao_cols_base_list

    # Cria um DataFrame para armazenar as features de diferença/pct_change
    features_for_model = pd.DataFrame(index=df_simulated_edicao_sorted.index)

    for col in cols_to_compare:
        if col in df_base_edicao_6_sorted.columns and col in df_simulated_edicao_sorted.columns:
            # Calcula a diferença
            features_for_model[f'{col}_diff_prev'] = df_simulated_edicao_sorted[col] - df_base_edicao_6_sorted[col]
            # Calcula o percentual de mudança (evita divisão por zero)
            features_for_model[f'{col}_pct_change_prev'] = (
                features_for_model[f'{col}_diff_prev'] / df_base_edicao_6_sorted[col].replace(0, np.nan)
            ).fillna(0) # Preenche NaN (de divisão por zero) com 0
        else:
            print(f"MODEL_LOGIC_WARNING: Coluna '{col}' não encontrada em um dos DataFrames para cálculo de features.")

    # Adiciona as colunas categóricas (Estado, Pública ou Privada) ao DataFrame de features
    # df_simulated_edicao_processed é o df_simulated_edicao_sorted com reset_index()
    # Precisamos garantir que as colunas categóricas também estejam no features_for_model
    # E que o OHE seja aplicado a elas.
    df_simulated_edicao_with_features = df_simulated_edicao_sorted.reset_index().merge(
        features_for_model.reset_index(), on='Universidade', how='left'
    )

    # 2. Aplicar One-Hot Encoding para 'Estado' e 'Pública ou Privada'
    # As categorias devem ser as mesmas usadas no treinamento do modelo
    # Para garantir isso, é ideal ter uma lista de todas as categorias possíveis
    # Por enquanto, vamos usar o pd.get_dummies e depois alinhar com as features esperadas
    df_simulated_edicao_processed = pd.get_dummies(df_simulated_edicao_with_features, columns=['Estado', 'Pública ou Privada'], drop_first=False)
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

# --- Função para calcular tendências médias (melhorada) ---
def calculate_average_trends(df_full, ufpe_name):
    print("MODEL_LOGIC_DEBUG: Iniciando calculate_average_trends.")
    # Exclui a UFPE para calcular as tendências médias das outras universidades
    df_other_universities = df_full[df_full['Universidade'] != ufpe_name].copy()

    # Ordena por universidade e edição para calcular pct_change corretamente
    df_other_universities_sorted = df_other_universities.sort_values(by=['Universidade', 'Edicao_RUF'])

    # Colunas para calcular as tendências (apenas as notas das dimensões)
    cols_to_trend = ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']

    # Calcula o percentual de mudança entre edições consecutivas para cada universidade
    # e para cada coluna de nota
    pct_changes_df = df_other_universities_sorted.groupby('Universidade')[cols_to_trend].pct_change()
    pct_changes_df = pct_changes_df.add_suffix('_pct_change_prev')

    # Adiciona as colunas de pct_change de volta ao df_other_universities_sorted
    df_other_universities_with_pct = pd.concat([df_other_universities_sorted, pct_changes_df], axis=1)

    # Calcula a média das mudanças percentuais para cada universidade
    # Ignora NaN que podem surgir no primeiro ano de cada universidade
    average_trends = df_other_universities_with_pct.groupby('Universidade')[
        [f'{col}_pct_change_prev' for col in cols_to_trend]
    ].mean()

    print("MODEL_LOGIC_DEBUG: calculate_average_trends concluída.")
    return average_trends
