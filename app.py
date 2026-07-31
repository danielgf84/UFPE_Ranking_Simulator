import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np

# --- 1. Configuração e Carregamento de Recursos ---
# O caminho para a sua pasta 'data' no Google Drive
data_path = 'data'

# Caminho completo para o arquivo do modelo XGBoost
model_path = os.path.join(data_path, 'xgboost_model.pkl')

# Caminho completo para o arquivo de dados processado
input_file_name = 'ruf_consolidado_fe.xlsx'
input_file_path = os.path.join(data_path, input_file_name)

ufpe_exact_name = 'Universidade Federal de Pernambuco'
target_column = 'Ranking'

# --- Funções de Carregamento (com cache para Streamlit) ---

@st.cache_resource # Usa o cache do Streamlit para carregar o modelo apenas uma vez
def load_model(path):
    try:
        st.write(f"Tentando carregar modelo de: {path}") # DEBUG
        model = joblib.load(path)
        st.write("Modelo carregado com sucesso.") # DEBUG
        return model
    except Exception as e:
        st.error(f"Erro ao carregar o modelo: {e}")
        return None

@st.cache_data # Usa o cache do Streamlit para carregar os dados apenas uma vez
def load_data(path):
    try:
        st.write(f"Tentando carregar dados de: {path}") # DEBUG
        df = pd.read_excel(path)
        st.write(f"Dados carregados com sucesso. Shape: {df.shape}") # DEBUG
        st.write("Colunas do DataFrame carregado:", df.columns.tolist()) # DEBUG
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

# Carrega o modelo e os dados
loaded_model = load_model(model_path)
df_model = load_data(input_file_path)

# Verifica se o modelo e os dados foram carregados com sucesso
if loaded_model is None or df_model.empty:
    st.error("Não foi possível carregar o modelo ou os dados. Verifique os caminhos e arquivos.")
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
    st.error(f"Erro: A universidade '{ufpe_exact_name}' não foi encontrada na Edição 6.")
    st.stop()

# Identifica as colunas que são features para o modelo
features = [col for col in df_model.columns if col not in ['Universidade', 'is_UFPE', 'Edicao_RUF', target_column]]

# --- Cálculo das Tendências Médias para Outras Universidades ---
# (Copiado do Bloco 3 do notebook)
notas_cols_base = ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota']
trend_pct_change_cols = [f'{col}_pct_change_prev' for col in notas_cols_base]

# Exclui a UFPE do cálculo das tendências médias
df_other_universities = df_model[df_model['Universidade'] != ufpe_exact_name].copy()

# Calcula as variações percentuais para todas as edições e universidades
for col_base in notas_cols_base:
    # Garante que a coluna existe antes de tentar calcular pct_change
    if col_base in df_other_universities.columns:
        df_other_universities[f'{col_base}_pct_change_prev'] = df_other_universities.groupby('Universidade')[col_base].pct_change()
    else:
        st.warning(f"Coluna '{col_base}' não encontrada para cálculo de tendência. Será ignorada.")
        # Adiciona a coluna de tendência com zeros para evitar KeyError no futuro
        df_other_universities[f'{col_base}_pct_change_prev'] = 0.0


# Filtra as colunas de tendência que realmente existem no DataFrame
existing_trend_pct_change_cols = [col for col in trend_pct_change_cols if col in df_other_universities.columns]

# Calcula a média dessas variações por universidade
average_trends = df_other_universities.groupby('Universidade')[existing_trend_pct_change_cols].mean()

# Preenche quaisquer NaNs restantes com 0 (para universidades com histórico incompleto)
average_trends = average_trends.fillna(0)


# --- 2. Função de Simulação (copiada do Bloco 4 do notebook) ---

def simulate_full_ranking_avg_trend(
    df_base_edicao_6: pd.DataFrame,
    model,
    ufpe_name: str,
    average_trends_df: pd.DataFrame,
    pct_change_ensino: float = 0.0,
    pct_change_pesquisa: float = 0.0,
    pct_change_mercado: float = 0.0,
    pct_change_inovacao: float = 0.0,
    pct_change_internacionalizacao: float = 0.0
) -> pd.DataFrame:
    """
    Simula o ranking completo para a próxima edição (Edição 7) com base nos dados da Edição 6.

    Aplica variações percentuais nas notas da UFPE e usa tendências médias históricas
    para as outras universidades. Em seguida, prevê o ranking para todas as universidades
    e gera um ranking final.
    """
    df_simulated_edicao = df_base_edicao_6.copy()
    df_simulated_edicao['Edicao_RUF'] = 7 # Sinaliza para o modelo que esta é a "próxima" edição

    # Mapeamento das notas para as variações percentuais de entrada
    notas_cols_input = {
        'Nota em Ensino': pct_change_ensino,
        'Nota em Pesquisa': pct_change_pesquisa,
        'Nota em Mercado': pct_change_mercado,
        'Nota em Inovação': pct_change_inovacao,
        'Nota em Internacionalização': pct_change_internacionalizacao
    }

    # --- Processar a UFPE ---
    ufpe_idx = df_simulated_edicao[df_simulated_edicao['Universidade'] == ufpe_name].index[0]
    original_ufpe_notes_ed6 = df_base_edicao_6.loc[ufpe_idx].copy() # Notas originais da Edição 6

    for col_base, pct_change in notas_cols_input.items():
        original_note_ufpe = original_ufpe_notes_ed6[col_base]
        new_note_ufpe = original_note_ufpe * (1 + pct_change)
        df_simulated_edicao.loc[ufpe_idx, col_base] = new_note_ufpe

        df_simulated_edicao.loc[ufpe_idx, f'{col_base}_diff_prev'] = new_note_ufpe - original_note_ufpe
        if original_note_ufpe != 0:
            df_simulated_edicao.loc[ufpe_idx, f'{col_base}_pct_change_prev'] = (new_note_ufpe - original_note_ufpe) / original_note_ufpe
        else:
            df_simulated_edicao.loc[ufpe_idx, f'{col_base}_pct_change_prev'] = 0.0

    # Recalcular a Nota Geral e suas variações para a UFPE
    original_overall_note_ufpe_ed6 = original_ufpe_notes_ed6['Nota']
    new_overall_note_ufpe_simulated = df_simulated_edicao.loc[ufpe_idx, ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']].sum()
    df_simulated_edicao.loc[ufpe_idx, 'Nota'] = new_overall_note_ufpe_simulated

    df_simulated_edicao.loc[ufpe_idx, 'Nota_diff_prev'] = new_overall_note_ufpe_simulated - original_overall_note_ufpe_ed6
    if original_overall_note_ufpe_ed6 != 0:
        df_simulated_edicao.loc[ufpe_idx, 'Nota_pct_change_prev'] = (new_overall_note_ufpe_simulated - original_overall_note_ufpe_ed6) / original_overall_note_ufpe_ed6
    else:
        df_simulated_edicao.loc[ufpe_idx, 'Nota_pct_change_prev'] = 0.0

    # --- Processar as OUTRAS universidades (aplicando tendências médias) ---
    other_universities_names = df_simulated_edicao[df_simulated_edicao['Universidade'] != ufpe_name]['Universidade'].unique()

    for uni_name in other_universities_names:
        uni_idx = df_simulated_edicao[df_simulated_edicao['Universidade'] == uni_name].index[0]
        original_uni_notes_ed6 = df_base_edicao_6.loc[uni_idx].copy() # Notas originais da Edição 6

        for col_base in notas_cols_input.keys():
            col_pct_change_prev = f'{col_base}_pct_change_prev'
            # Tenta obter a tendência média para esta universidade e dimensão
            if uni_name in average_trends_df.index and col_pct_change_prev in average_trends_df.columns:
                trend_pct_change = average_trends_df.loc[uni_name, col_pct_change_prev]
            else:
                trend_pct_change = 0.0 # Se não houver tendência média, assume 0% de mudança

            original_note_other = original_uni_notes_ed6[col_base]
            new_note_other = original_note_other * (1 + trend_pct_change)
            df_simulated_edicao.loc[uni_idx, col_base] = new_note_other

            df_simulated_edicao.loc[uni_idx, f'{col_base}_diff_prev'] = new_note_other - original_note_other
            if original_note_other != 0:
                df_simulated_edicao.loc[uni_idx, f'{col_base}_pct_change_prev'] = (new_note_other - original_note_other) / original_note_other
            else:
                df_simulated_edicao.loc[uni_idx, f'{col_base}_pct_change_prev'] = 0.0

        # Recalcular a Nota Geral e suas variações para as outras universidades
        original_overall_note_uni_ed6 = original_uni_notes_ed6['Nota']
        new_overall_note_uni_simulated = df_simulated_edicao.loc[uni_idx, ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']].sum()
        df_simulated_edicao.loc[uni_idx, 'Nota'] = new_overall_note_uni_simulated

        df_simulated

