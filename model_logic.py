# model_logic.py
import pandas as pd
import os
import joblib
import numpy as np

# --- Variáveis de Configuração ---
ufpe_exact_name = 'Universidade Federal de Pernambuco'
target_column = 'Ranking' # Coluna que o modelo prediz

EDITION_YEAR_MAP = {
    1: 2017, 2: 2018, 3: 2019, 4: 2023, 5: 2024, 6: 2025, 7: 2026
}

def get_year_from_edition(edition_number):
    return EDITION_YEAR_MAP.get(edition_number, f"Ano Desconhecido (Edição {edition_number})")

# --- Funções de Carregamento ---
def load_model(path):
    """Carrega o modelo de Machine Learning do caminho especificado."""
    print(f"MODEL_LOGIC_DEBUG: Tentando carregar o modelo de: {path}")
    try:
        model = joblib.load(path)
        print(f"MODEL_LOGIC_DEBUG: Modelo carregado com sucesso de {os.path.basename(path)}.")
        return model
    except Exception as e:
        print(f"MODEL_LOGIC_ERROR: Erro CRÍTICO ao carregar o modelo de '{path}': {e}")
        raise # Levanta a exceção para ser tratada na camada de UI

def load_data(path):
    """Carrega os dados consolidados do arquivo Excel especificado."""
    print(f"MODEL_LOGIC_DEBUG: Tentando carregar os dados de: {path}")
    try:
        df = pd.read_excel(path)
        print(f"MODEL_LOGIC_DEBUG: Dados carregados com sucesso de {os.path.basename(path)}.")
        return df
    except Exception as e:
        print(f"MODEL_LOGIC_ERROR: Erro CRÍTICO ao carregar os dados de '{path}': {e}")
        raise # Levanta a exceção para ser tratada na camada de UI

# --- Função para calcular tendências médias de todas as edições ---
def calculate_average_trends(df_full_data, ufpe_name):
    """
    Calcula as tendências médias de mudança percentual para todas as universidades
    (exceto a UFPE) ao longo de todas as edições históricas.
    """
    print("MODEL_LOGIC_DEBUG: Iniciando calculate_average_trends.")

    # Exclui a UFPE para calcular as tendências médias das outras universidades
    df_other_universities = df_full_data[df_full_data['Universidade'] != ufpe_name].copy()

    # Colunas de notas e posições para as quais queremos calcular as tendências
    cols_to_trend = [
        'Ranking', 'Nota',
        'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização',
        'Posição em Ensino', 'Posição em Pesquisa', 'Posição em Mercado', 'Posição em Inovação', 'Posição em Internacionalização'
    ]

    # Garante que as colunas são numéricas antes de calcular as tendências
    for col in cols_to_trend:
        if col in df_other_universities.columns:
            df_other_universities[col] = pd.to_numeric(df_other_universities[col], errors='coerce')

    # Calcula a mudança percentual entre edições consecutivas para cada universidade
    # Agrupa por universidade e calcula a diferença percentual
    # Usa shift(1) para comparar com a edição anterior
    df_other_universities_sorted = df_other_universities.sort_values(by=['Universidade', 'Edicao_RUF'])
    df_other_universities_sorted['Edicao_RUF_prev'] = df_other_universities_sorted.groupby('Universidade')['Edicao_RUF'].shift(1)

    # Filtra para ter apenas pares de edições consecutivas
    df_pairs = df_other_universities_sorted[df_other_universities_sorted['Edicao_RUF_prev'].notna()].copy()

    all_universities_average_trends = {}
    epsilon = 1e-6 # Pequeno valor para evitar divisão por zero

    for col in cols_to_trend:
        if col in df_pairs.columns:
            # Calcula a mudança percentual para cada par de edições
            df_pairs[f'{col}_prev'] = df_other_universities_sorted.groupby('Universidade')[col].shift(1)
            df_pairs[f'{col}_pct_change'] = (
                (df_pairs[col] - df_pairs[f'{col}_prev']) / (df_pairs[f'{col}_prev'].replace(0, np.nan) + epsilon)
            ).fillna(0)

            # Calcula a média dessas mudanças percentuais
            avg_pct_change = df_pairs[f'{col}_pct_change'].mean()
            all_universities_average_trends[f'{col}_pct_change_prev'] = avg_pct_change
        else:
            print(f"MODEL_LOGIC_WARNING: Coluna '{col}' não encontrada para calcular tendências médias.")

    print("MODEL_LOGIC_DEBUG: Tendências médias calculadas.")
    return all_universities_average_trends

# --- Função de Simulação Principal ---
def simulate_full_ranking_avg_trend(
    df_base_edicao_6, model, ufpe_name, all_universities_average_trends,
    pct_change_ensino, pct_change_pesquisa, pct_change_mercado,
    pct_change_inovacao, pct_change_internacionalizacao,
    apply_other_uni_trends, model_expected_features
):
    print("MODEL_LOGIC_DEBUG: Iniciando simulate_full_ranking_avg_trend.")

    # Cria uma cópia do DataFrame da edição base para a simulação
    df_simulated_edicao = df_base_edicao_6.copy()

    # Lista de colunas de notas e posições
    notas_cols_base_list = ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']
    posicao_cols_base_list = ['Posição em Ensino', 'Posição em Pesquisa', 'Posição em Mercado', 'Posição em Inovação', 'Posição em Internacionalização']
    ranking_cols = ['Ranking'] + posicao_cols_base_list # Colunas que devem ser inteiras

    # Aplica as variações percentuais à UFPE
    ufpe_row_index = df_simulated_edicao[df_simulated_edicao['Universidade'] == ufpe_name].index
    if not ufpe_row_index.empty:
        idx = ufpe_row_index[0]
        # Garante que as colunas são float antes de aplicar a variação
        for col in notas_cols_base_list:
            df_simulated_edicao.loc[idx, col] = pd.to_numeric(df_simulated_edicao.loc[idx, col], errors='coerce')
            # --- CORREÇÃO AQUI: Adiciona .replace('ç', 'c') para corresponder aos nomes das variáveis ---
            df_simulated_edicao.loc[idx, col] *= (1 + locals()[f'pct_change_{col.replace("Nota em ", "").lower().replace("ç", "c")}'])
        print(f"MODEL_LOGIC_DEBUG: Variações aplicadas à UFPE.")
    else:
        print(f"MODEL_LOGIC_WARNING: UFPE não encontrada em df_simulated_edicao para aplicar variações.")

    # Aplica as tendências médias às outras universidades, se a opção estiver marcada
    if apply_other_uni_trends and all_universities_average_trends:
        for col_name, avg_pct_change in all_universities_average_trends.items():
            if '_pct_change_prev' in col_name:
                original_col = col_name.replace('_pct_change_prev', '')
                if original_col in df_simulated_edicao.columns:
                    # Converte a coluna para float temporariamente para o cálculo
                    # Isso é crucial para evitar TypeError ao multiplicar com float
                    df_simulated_edicao[original_col] = pd.to_numeric(df_simulated_edicao[original_col], errors='coerce')

                    # Aplica a tendência apenas para universidades que não são a UFPE
                    mask = df_simulated_edicao['Universidade'] != ufpe_name
                    df_simulated_edicao.loc[mask, original_col] *= (1 + avg_pct_change)

                    # Para colunas de Ranking e Posição, converte de volta para inteiro após arredondamento
                    if original_col in ranking_cols:
                        df_simulated_edicao.loc[mask, original_col] = df_simulated_edicao.loc[mask, original_col].round().astype(int)
        print(f"MODEL_LOGIC_DEBUG: Tendências médias aplicadas a outras universidades.")
    elif apply_other_uni_trends and not all_universities_average_trends:
        print("MODEL_LOGIC_WARNING: 'apply_other_uni_trends' está True, mas 'all_universities_average_trends' está vazio. Nenhuma tendência aplicada a outras universidades.")


    # Recalcula a Nota Geral e Posições para a edição simulada
    # Garante que as notas não excedam 100
    for col in notas_cols_base_list:
        df_simulated_edicao[col] = df_simulated_edicao[col].clip(0, 100)

    # Recalcula a Nota Geral (média das notas das dimensões)
    df_simulated_edicao['Nota'] = df_simulated_edicao[notas_cols_base_list].mean(axis=1)

    # Recalcula as Posições (rankings individuais para cada dimensão)
    for col in notas_cols_base_list:
        df_simulated_edicao[f'Posição em {col.replace("Nota em ", "").replace("ç", "c")}'] = df_simulated_edicao[col].rank(ascending=False).astype(int)
    print("MODEL_LOGIC_DEBUG: Notas e Posições recalculadas para a edição simulada.")

    # Prepara o DataFrame para o modelo
    df_simulated_edicao_sorted = df_simulated_edicao.sort_values(by='Universidade').reset_index(drop=True)

    # Cria as features de diferença e mudança percentual para a edição simulada
    # (Estas são as features que o modelo espera, baseadas na edição anterior)
    features_for_model = pd.DataFrame(index=df_simulated_edicao_sorted['Universidade'])
    epsilon = 1e-6 # Pequeno valor para evitar divisão por zero

    for col in notas_cols_base_list + posicao_cols_base_list + ['Nota', 'Ranking']:
        if col in df_base_edicao_6.columns and col in df_simulated_edicao_sorted.columns:
            # Garante que as colunas são numéricas antes de calcular diff/pct_change
            df_base_edicao_6[col] = pd.to_numeric(df_base_edicao_6[col], errors='coerce').fillna(0)
            df_simulated_edicao_sorted[col] = pd.to_numeric(df_simulated_edicao_sorted[col], errors='coerce').fillna(0)

            features_for_model[f'{col}_diff_prev'] = df_simulated_edicao_sorted[col] - df_base_edicao_6[col]
            features_for_model[f'{col}_pct_change_prev'] = (
                features_for_model[f'{col}_diff_prev'] / (df_base_edicao_6[col].replace(0, np.nan) + epsilon)
            ).fillna(0) # Preenche NaN (de divisão por zero) com 0
        else:
            print(f"MODEL_LOGIC_WARNING: Coluna '{col}' não encontrada em um dos DataFrames para cálculo de features. Será ignorada para features de diff/pct_change.")

    # Adiciona as colunas categóricas (Estado_XX, Pública ou Privada_YY) ao DataFrame de features
    # df_simulated_edicao_with_features é o df_simulated_edicao_sorted com reset_index()
    # As colunas OHE já estão em df_simulated_edicao_sorted
    df_simulated_edicao_with_features = df_simulated_edicao_sorted.copy()

    # 2. Aplicar One-Hot Encoding para 'Estado' e 'Pública ou Privada'
    # REMOVIDO: As colunas 'Estado' e 'Pública ou Privada' já estão One-Hot Encoded no DataFrame de entrada.
    # O DataFrame df_simulated_edicao_with_features já deve conter as colunas como 'Estado_AL', 'Pública ou Privada_Federal', etc.
    # Apenas copia o DataFrame, pois as colunas já estão no formato OHE.
    df_simulated_edicao_processed = df_simulated_edicao_with_features.copy()
    print("MODEL_LOGIC_DEBUG: One-Hot Encoding não aplicado, colunas já estão no formato OHE.")

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
