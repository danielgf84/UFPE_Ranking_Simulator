import streamlit as st
import pandas as pd
import os
import joblib
import numpy as np

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

# --- NOVO: Mapeamento de Edições para Anos ---
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
        # st.write(f"DEBUG: Tentando carregar modelo de: {path}") # Descomente para depurar
        model = joblib.load(path)
        # st.write("DEBUG: Modelo carregado com sucesso.") # Descomente para depurar
        return model
    except Exception as e:
        st.error(f"Erro ao carregar o modelo: {e}. Verifique se o arquivo '{os.path.basename(path)}' está na pasta 'data' do seu repositório.")
        return None

@st.cache_data # Usa o cache do Streamlit para carregar os dados apenas uma vez
def load_data(path):
    try:
        # st.write(f"DEBUG: Tentando carregar dados de: {path}") # Descomente para depurar
        df = pd.read_excel(path)
        # st.write(f"DEBUG: Dados carregados com sucesso. Shape: {df.shape}") # Descomente para depurar
        # st.write("DEBUG: Colunas do DataFrame carregado:", df.columns.tolist()) # Descomente para depurar
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
    st.error(f"Erro: A universidade '{ufpe_exact_name}' não foi encontrada na Edição 6. Verifique o nome ou os dados no arquivo Excel.")
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

        df_simulated_edicao.loc[uni_idx, 'Nota_diff_prev'] = new_overall_note_uni_simulated - original_overall_note_uni_ed6
        if original_overall_note_uni_ed6 != 0:
            df_simulated_edicao.loc[uni_idx, 'Nota_pct_change_prev'] = (new_overall_note_uni_simulated - original_overall_note_uni_ed6) / original_overall_note_uni_ed6
        else:
            df_simulated_edicao.loc[uni_idx, 'Nota_pct_change_prev'] = 0.0

    # Prever o ranking para a edição simulada
    X_simulated = df_simulated_edicao[features]
    df_simulated_edicao['Predicted_Ranking'] = model.predict(X_simulated)

    # Gerar o ranking final
    df_simulated_edicao['Simulated_Ranking'] = df_simulated_edicao['Predicted_Ranking'].rank(method='min', ascending=True).astype(int)

    # CORREÇÃO AQUI: Convertendo dict_keys para list antes de concatenar
    return df_simulated_edicao[['Universidade', 'Simulated_Ranking', 'Predicted_Ranking', 'Nota'] + list(notas_cols_input.keys())]


# --- 3. Interface do Streamlit ---

st.set_page_config(layout="wide", page_title="Simulador de Ranking RUF UFPE")

st.title("📊 Simulador de Ranking RUF - UFPE")
st.markdown("Preveja o impacto de mudanças nas notas da UFPE no Ranking Universitário Folha (RUF).")

# --- Quadro Resumo com Notas Atuais da UFPE (Edição 6) ---
st.subheader(f"Notas Atuais da UFPE (Edição 6 - {get_year_from_edition(6)})") # Título atualizado

# Seleciona as colunas de interesse para o resumo
cols_to_display = ['Ranking', 'Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização', 'Nota']
ufpe_current_notes = ufpe_data_edicao_6[cols_to_display].iloc[0]

# Cria um DataFrame para exibir de forma mais amigável
summary_df = pd.DataFrame({
    'Métrica': ufpe_current_notes.index,
    'Valor': ufpe_current_notes.values # Removido "(Edição 6)" pois já está no título
})
# Esconde o índice do DataFrame aqui
st.dataframe(summary_df.set_index('Métrica'), hide_index=False) # Mantém 'Métrica' como índice visível
st.markdown("---") # Adiciona um separador visual

st.header(f"Configurações de Simulação para a UFPE (Edição 7 - {get_year_from_edition(7)})") # Título atualizado
st.markdown("Ajuste as variações percentuais para as notas da UFPE na próxima edição do RUF.")

col1, col2, col3 = st.columns(3)

with col1:
    # Ajustado para exibir como porcentagem e converter para decimal na simulação
    pct_ensino_display = st.slider("Variação % em Ensino", -20, 20, 0, 1, format="%.0f%%")
    pct_pesquisa_display = st.slider("Variação % em Pesquisa", -20, 20, 0, 1, format="%.0f%%")

with col2:
    # Ajustado para exibir como porcentagem e converter para decimal na simulação
    pct_mercado_display = st.slider("Variação % em Mercado", -20, 20, 0, 1, format="%.0f%%")
    pct_inovacao_display = st.slider("Variação % em Inovação", -20, 20, 0, 1, format="%.0f%%")

with col3:
    # Ajustado para exibir como porcentagem e converter para decimal na simulação
    pct_internacionalizacao_display = st.slider("Variação % em Internacionalização", -20, 20, 0, 1, format="%.0f%%")

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
        pct_change_internacionalizacao=pct_internacionalizacao
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
        f'Edição 6 ({get_year_from_edition(6)})': [ # Coluna atualizada
            original_ufpe_ed6['Ranking'],
            original_ufpe_ed6['Nota em Ensino'],
            original_ufpe_ed6['Nota em Pesquisa'],
            original_ufpe_ed6['Nota em Mercado'],
            original_ufpe_ed6['Nota em Inovação'],
            original_ufpe_ed6['Nota em Internacionalização'],
            original_ufpe_ed6['Nota']
        ],
        f'Edição 7 ({get_year_from_edition(7)}) Simulada': [ # Coluna atualizada
            simulated_ufpe_ed7['Simulated_Ranking'],
            simulated_ufpe_ed7['Nota em Ensino'],
            simulated_ufpe_ed7['Nota em Pesquisa'],
            simulated_ufpe_ed7['Nota em Mercado'],
            simulated_ufpe_ed7['Nota em Inovação'],
            simulated_ufpe_ed7['Nota em Internacionalização'],
            simulated_ufpe_ed7['Nota']
        ]
    })
    st.dataframe(comparison_df.set_index('Métrica'), hide_index=False) # Mantém 'Métrica' como índice visível

st.markdown("---")
st.info("Este simulador utiliza um modelo de Machine Learning treinado com dados históricos do RUF para prever o ranking. As previsões são estimativas e não garantem resultados futuros.")
