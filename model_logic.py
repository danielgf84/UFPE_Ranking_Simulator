# model_logic.py
# Este arquivo contém as funções de lógica de simulação para o aplicativo Streamlit.

import pandas as pd
import numpy as np
import os
import pickle

# Definir o caminho base para os artefatos.
# Usamos uma abordagem mais robusta para garantir que o caminho seja encontrado
# tanto localmente quanto no Streamlit Cloud.
# No Streamlit Cloud, o diretório de trabalho é a raiz do repositório.
# Então, 'data' é uma subpasta diretamente na raiz.

# Obter o diretório do arquivo atual (model_logic.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Definir o caminho para a pasta 'data' e para o modelo
ARTIFACTS_BASE_PATH = os.path.join(current_dir, 'data')
MODEL_PATH = os.path.join(current_dir, 'final_model.pkl')

# Função para carregar artefatos
def load_artifacts():
    try:
        # Carregar features e base_features primeiro, pois são usadas em prepare_simulated_university_data
        with open(os.path.join(ARTIFACTS_BASE_PATH, 'features.pkl'), 'rb') as f:
            features_data = pickle.load(f)
        features = features_data['features']
        base_features = features_data['base_features']
        UFPE_ORIGINAL_NAME = features_data['UFPE_ORIGINAL_NAME']
    # Carregar modelo
    with open(MODEL_PATH, 'rb') as f:
        final_model = pickle.load(f)

    # Carregar df_consolidado_processed
    df_consolidado_processed = pd.read_pickle(os.path.join(ARTIFACTS_BASE_PATH, 'df_consolidado_processed.pkl'))

    # Carregar notas da UFPE
    with open(os.path.join(ARTIFACTS_BASE_PATH, 'ufpe_notes.pkl'), 'rb') as f:
        ufpe_notes_data = pickle.load(f)
    current_ufpe_notes = ufpe_notes_data['current_ufpe_notes']
    previous_ufpe_notes = ufpe_notes_data['previous_ufpe_notes']

    return final_model, df_consolidado_processed, current_ufpe_notes, previous_ufpe_notes, features, base_features, UFPE_ORIGINAL_NAME
except FileNotFoundError as e:
    raise FileNotFoundError(f"Erro: Artefato não encontrado. Verifique se o backend foi executado e salvou os arquivos corretamente. Detalhes: {e}")
except Exception as e:
    raise Exception(f"Erro ao carregar artefatos: {e}")
# Função para preparar dados simulados de uma universidade
def prepare_simulated_university_data(current_notes_dict, previous_notes_dict, base_features,
                                      ensino_var_perc=0, pesquisa_var_perc=0,
                                      mercado_var_perc=0, inovacao_var_perc=0,
                                      internacionalizacao_var_perc=0):
    simulated_notes = current_notes_dict.copy()
    simulated_features_dict = {}
simulated_notes['Nota_em_Ensino'] *= (1 + ensino_var_perc / 100)
simulated_notes['Nota_em_Pesquisa'] *= (1 + pesquisa_var_perc / 100)
simulated_notes['Nota_em_Mercado'] *= (1 + mercado_var_perc / 100)
simulated_notes['Nota_em_Inovacao'] *= (1 + inovacao_var_perc / 100)
simulated_notes['Nota_em_Internacionalizacao'] *= (1 + internacionalizacao_var_perc / 100)

for feature in base_features:
    simulated_features_dict[feature] = simulated_notes[feature]
    var_abs = simulated_notes[feature] - previous_notes_dict[feature]
    var_perc = ((simulated_notes[feature] - previous_notes_dict[feature]) / previous_notes_dict[feature]) * 100 if previous_notes_dict[feature] != 0 else 0
    simulated_features_dict[f'Var_Abs_{feature}'] = var_abs
    simulated_features_dict[f'Var_Perc_{feature}'] = var_perc

return simulated_features_dict, simulated_notes
# Função principal de simulação
def run_simulation(ufpe_ensino_var, ufpe_pesquisa_var, ufpe_mercado_var,
                   ufpe_inovacao_var, ufpe_internacionalizacao_var,
                   df_consolidado_processed, current_ufpe_notes, previous_ufpe_notes, final_model,
                   features, base_features, UFPE_ORIGINAL_NAME):
latest_year = df_consolidado_processed['Ano'].max()
df_latest_year = df_consolidado_processed[df_consolidado_processed['Ano'] == latest_year].copy()
df_competitors = df_latest_year[df_latest_year['Universidade'] != UFPE_ORIGINAL_NAME].copy()

df_model_for_avg_var = df_consolidado_processed.copy()
for feature in base_features:
    df_model_for_avg_var[f'Var_Abs_{feature}'] = df_model_for_avg_var.groupby('Universidade')[feature].diff()
    df_model_for_avg_var[f'Var_Perc_{feature}'] = df_model_for_avg_var.groupby('Universidade')[feature].pct_change() * 100
    df_model_for_avg_var[f'Var_Perc_{feature}'] = df_model_for_avg_var[f'Var_Perc_{feature}'].replace([np.inf, -np.inf], np.nan)
df_model_for_avg_var.dropna(subset=[f'Var_Abs_{f}' for f in base_features] + [f'Var_Perc_{f}' for f in base_features], inplace=True)

average_perc_variations = {}
for feature in base_features:
    avg_var = df_model_for_avg_var[f'Var_Perc_{feature}'].mean()
    average_perc_variations[feature] = avg_var

ufpe_simulated_features, ufpe_simulated_notes = prepare_simulated_university_data(
    current_ufpe_notes, previous_ufpe_notes, base_features,
    ensino_var_perc=ufpe_ensino_var,
    pesquisa_var_perc=ufpe_pesquisa_var,
    mercado_var_perc=ufpe_mercado_var,
    inovacao_var_perc=ufpe_inovacao_var,
    internacionalizacao_var_perc=ufpe_internacionalizacao_var
)

all_simulated_data = []
ufpe_simulated_features_df = pd.DataFrame([ufpe_simulated_features])
ufpe_simulated_features_df['Universidade'] = UFPE_ORIGINAL_NAME
all_simulated_data.append(ufpe_simulated_features_df)

for index, row in df_competitors.iterrows():
    uni_name = row['Universidade']
    current_uni_notes = row[base_features].to_dict()
    previous_uni_data = df_consolidado_processed[
        (df_consolidado_processed['Universidade'] == uni_name) &amp;
        (df_consolidado_processed['Ano'] == latest_year - 1)
    ]
    if not previous_uni_data.empty:
        previous_uni_notes = previous_uni_data[base_features].iloc[0].to_dict()
    else:
        previous_uni_notes = current_uni_notes.copy()
    competitor_simulated_features, _ = prepare_simulated_university_data(
        current_uni_notes, previous_uni_notes, base_features,
        ensino_var_perc=average_perc_variations.get('Nota_em_Ensino', 0),
        pesquisa_var_perc=average_perc_variations.get('Nota_em_Pesquisa', 0),
        mercado_var_perc=average_perc_variations.get('Nota_em_Mercado', 0),
        inovacao_var_perc=average_perc_variations.get('Nota_em_Inovacao', 0),
        internacionalizacao_var_perc=average_perc_variations.get('Nota_em_Internacionalizacao', 0)
    )
    competitor_simulated_features_df = pd.DataFrame([competitor_simulated_features])
    competitor_simulated_features_df['Universidade'] = uni_name
    all_simulated_data.append(competitor_simulated_features_df)

df_simulated_scenario = pd.concat(all_simulated_data, ignore_index=True)
df_simulated_scenario_features = df_simulated_scenario[features]
predicted_rankings = final_model.predict(df_simulated_scenario_features)
df_simulated_scenario['Predicted_Ranking'] = predicted_rankings
df_final_ranking = df_simulated_scenario.sort_values(by='Predicted_Ranking').reset_index(drop=True)
df_final_ranking['Predicted_Position'] = df_final_ranking.index + 1
ufpe_final_position_row = df_final_ranking[df_final_ranking['Universidade'] == UFPE_ORIGINAL_NAME]
ufpe_predicted_ranking = ufpe_final_position_row['Predicted_Ranking'].iloc[0]
ufpe_predicted_position = ufpe_final_position_row['Predicted_Position'].iloc[0]

return ufpe_predicted_ranking, ufpe_predicted_position, ufpe_simulated_notes, df_final_rankin
