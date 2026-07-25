
# model_logic.py
# Este arquivo contém a lógica de carregamento de artefatos e a função de simulação
# para ser utilizada pelo aplicativo Streamlit.

import pandas as pd
import numpy as np
import pickle
import os
import logging

# Configuração de logging para model_logic
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Definir o caminho base para os artefatos
# ATENÇÃO: Em ambiente de produção (Streamlit Cloud), este caminho pode precisar ser ajustado
# para ser relativo ao diretório onde o app.py está sendo executado.
# Para execução local, assumimos que os artefatos estão na mesma pasta ou em uma subpasta 'data'.
ARTIFACTS_BASE_PATH = os.path.dirname(os.path.abspath(__file__)) # Caminho do diretório atual (onde model_logic.py está)
DATA_PATH = os.path.join(ARTIFACTS_BASE_PATH, 'data')

# Função para carregar todos os artefatos necessários
def load_artifacts():
    logging.info("Carregando artefatos...")
    try:
        # Carregar o modelo
        with open(os.path.join(ARTIFACTS_BASE_PATH, 'final_model.pkl'), 'rb') as f:
            final_model = pickle.load(f)
        logging.info("Modelo final carregado.")

        # Carregar df_consolidado_processed
        with open(os.path.join(DATA_PATH, 'df_consolidado_processed.pkl'), 'rb') as f:
            df_consolidado_processed = pickle.load(f)
        logging.info("DataFrame consolidado processado carregado.")

        # Carregar notas da UFPE
        with open(os.path.join(DATA_PATH, 'ufpe_notes.pkl'), 'rb') as f:
            ufpe_notes = pickle.load(f)
        current_ufpe_notes = ufpe_notes['current_ufpe_notes']
        previous_ufpe_notes = ufpe_notes['previous_ufpe_notes']
        logging.info("Notas da UFPE (atuais e anteriores) carregadas.")

        # Carregar features e metadados
        with open(os.path.join(DATA_PATH, 'features.pkl'), 'rb') as f:
            features_data = pickle.load(f)
        features = features_data['features']
        base_features = features_data['base_features']
        UFPE_ORIGINAL_NAME = features_data['UFPE_ORIGINAL_NAME']
        target_name = features_data['target_name']
        logging.info("Features e metadados carregados.")

        logging.info("Todos os artefatos carregados com sucesso.")
        return final_model, df_consolidado_processed, current_ufpe_notes, previous_ufpe_notes, features, base_features, UFPE_ORIGINAL_NAME, target_name
    except FileNotFoundError as e:
        logging.error(f"Erro: Artefato não encontrado. Verifique se o backend foi executado e salvou os arquivos corretamente. Detalhes: {e}")
        raise FileNotFoundError(f"Erro: Artefato não encontrado. Detalhes: {e}")
    except Exception as e:
        logging.error(f"Erro ao carregar artefatos: {e}")
        raise Exception(f"Erro ao carregar artefatos: {e}")


# Função para preparar dados simulados de uma universidade
def prepare_simulated_university_data(current_notes_dict, previous_notes_dict, base_features,
                                      ensino_var_perc=0, pesquisa_var_perc=0,
                                      mercado_var_perc=0, inovacao_var_perc=0,
                                      internacionalizacao_var_perc=0):
    simulated_notes = current_notes_dict.copy()

    # Aplicar variações percentuais
    # Certifique-se de que a ordem das features base corresponde à ordem dos argumentos de variação
    simulated_notes[base_features[0]] *= (1 + ensino_var_perc / 100) # Nota_em_Ensino
    simulated_notes[base_features[1]] *= (1 + pesquisa_var_perc / 100) # Nota_em_Pesquisa
    simulated_notes[base_features[2]] *= (1 + mercado_var_perc / 100) # Nota_em_Mercado
    simulated_notes[base_features[3]] *= (1 + inovacao_var_perc / 100) # Nota_em_Inovacao
    simulated_notes[base_features[4]] *= (1 + internacionalizacao_var_perc / 100) # Nota_em_Internacionalizacao

    simulated_features_dict = {} # Corrigido aqui
    for feature in base_features:
        simulated_features_dict[feature] = simulated_notes[feature]
        var_abs = simulated_notes[feature] - previous_notes_dict[feature]
        # Tratar divisão por zero para variação percentual
        if previous_notes_dict[feature] != 0:
            var_perc = ((simulated_notes[feature] - previous_notes_dict[feature]) / previous_notes_dict[feature]) * 100
        else:
            var_perc = 0 # Se a nota anterior era zero, a variação percentual é zero ou indefinida, tratamos como zero para evitar inf
        simulated_features_dict[f'Var_Abs_{feature}'] = var_abs # Corrigido aqui
        simulated_features_dict[f'Var_Perc_{feature}'] = var_perc # Corrigido aqui

    return simulated_features_dict, simulated_notes

# Função principal de simulação
def run_simulation(ufpe_ensino_var, ufpe_pesquisa_var, ufpe_mercado_var,
                   ufpe_inovacao_var, ufpe_internacionalizacao_var,
                   df_consolidado_processed, current_ufpe_notes, previous_ufpe_notes, final_model,
                   features, base_features, UFPE_ORIGINAL_NAME, target_name):

    logging.info("Iniciando simulação de ranking...")

    # Usar 'Edicao_RUF' para identificar a edição mais recente
    latest_edition = df_consolidado_processed['Edicao_RUF'].max()
    df_latest_edition = df_consolidado_processed[df_consolidado_processed['Edicao_RUF'] == latest_edition].copy()
    df_competitors = df_latest_edition[df_latest_edition['Universidade'] != UFPE_ORIGINAL_NAME].copy()

    # Recalcular variações para o df_consolidado_processed para obter as médias dos competidores
    # Isso é feito para garantir que as variações sejam calculadas corretamente com base na Edicao_RUF
    df_model_for_avg_var = df_consolidado_processed.copy()
    df_model_for_avg_var = df_model_for_avg_var.sort_values(by=['Universidade', 'Edicao_RUF']).reset_index(drop=True) # Ordenar por Edicao_RUF
    for feature in base_features:
        df_model_for_avg_var[f'Var_Abs_{feature}'] = df_model_for_avg_var.groupby('Universidade')[feature].diff() # Corrigido aqui
        df_model_for_avg_var[f'Var_Perc_{feature}'] = df_model_for_avg_var.groupby('Universidade')[feature].pct_change() * 100 # Corrigido aqui
        df_model_for_avg_var[f'Var_Perc_{feature}'] = df_model_for_avg_var[f'Var_Perc_{feature}'].replace([np.inf, -np.inf], np.nan) # Corrigido aqui
    df_model_for_avg_var.dropna(subset=[f'Var_Abs_{f}' for f in base_features] + [f'Var_Perc_{f}' for f in base_features], inplace=True) # Corrigido aqui

    average_perc_variations = {} # Corrigido aqui
    for feature in base_features:
        avg_var = df_model_for_avg_var[f'Var_Perc_{feature}'].mean() # Corrigido aqui
        average_perc_variations[feature] = avg_var
    logging.info(f"Variações percentuais médias dos competidores: {average_perc_variations}") # Corrigido aqui

    # Preparar dados simulados da UFPE
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

    # Preparar dados simulados dos competidores
    for index, row in df_competitors.iterrows():
        uni_name = row['Universidade']
        current_uni_notes = row[base_features].to_dict()
        previous_uni_data = df_consolidado_processed[
            (df_consolidado_processed['Universidade'] == uni_name) &
            (df_consolidado_processed['Edicao_RUF'] == latest_edition - 1) # Usar Edicao_RUF
        ]
        if not previous_uni_data.empty:
            previous_uni_notes = previous_uni_data[base_features].iloc[0].to_dict()
        else:
            # Se não houver dados da edição anterior para o competidor, usar as notas atuais como "anteriores"
            # Isso fará com que as variações percentuais sejam 0.
            previous_uni_notes = current_uni_notes.copy()

        competitor_simulated_features, _ = prepare_simulated_university_data(
            current_uni_notes, previous_uni_notes, base_features,
            ensino_var_perc=average_perc_variations.get(base_features[0], 0),
            pesquisa_var_perc=average_perc_variations.get(base_features[1], 0),
            mercado_var_perc=average_perc_variations.get(base_features[2], 0),
            inovacao_var_perc=average_perc_variations.get(base_features[3], 0),
            internacionalizacao_var_perc=average_perc_variations.get(base_features[4], 0)
        )
        competitor_simulated_features_df = pd.DataFrame([competitor_simulated_features])
        competitor_simulated_features_df['Universidade'] = uni_name
        all_simulated_data.append(competitor_simulated_features_df)

    df_simulated_scenario = pd.concat(all_simulated_data, ignore_index=True)

    # Garantir que as colunas do DataFrame de simulação estejam na mesma ordem das features de treinamento
    df_simulated_scenario_features = df_simulated_scenario[features]

    # Fazer previsões
    predicted_rankings = final_model.predict(df_simulated_scenario_features)
    df_simulated_scenario['Predicted_Ranking'] = predicted_rankings

    # Ordenar e atribuir posições
    df_final_ranking = df_simulated_scenario.sort_values(by='Predicted_Ranking').reset_index(drop=True)
    df_final_ranking['Predicted_Position'] = df_final_ranking.index + 1

    ufpe_final_position_row = df_final_ranking[df_final_ranking['Universidade'] == UFPE_ORIGINAL_NAME]
    ufpe_predicted_ranking = ufpe_final_position_row['Predicted_Ranking'].iloc[0]
    ufpe_predicted_position = ufpe_final_position_row['Predicted_Position'].iloc[0]

    logging.info("Simulação de ranking concluída.")
    return ufpe_predicted_ranking, ufpe_predicted_position, ufpe_simulated_notes, df_final_ranking.head(10)
