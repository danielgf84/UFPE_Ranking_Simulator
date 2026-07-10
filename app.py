
# app.py
# Este é o arquivo principal do aplicativo Streamlit (frontend).

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

# Adicionar o diretório atual ao PATH para que model_logic possa ser importado
# Isso é importante para que o Streamlit Cloud encontre model_logic.py
sys.path.append(os.path.dirname(__file__))

# Importar as funções de lógica do arquivo model_logic.py
from model_logic import load_artifacts, prepare_simulated_university_data, run_simulation

# --- Configuração do Streamlit ---
st.set_page_config(layout="wide", page_title="Simulador de Ranking UFPE")

# --- Carregar Artefatos (usando st.cache_resource para otimização) ---
# st.cache_resource garante que esta função seja executada apenas uma vez
# e seus resultados sejam armazenados em cache, melhorando a performance.
@st.cache_resource
def cached_load_artifacts():
    try:
        return load_artifacts()
    except Exception as e:
        st.error(f"Erro ao carregar artefatos: {e}. Verifique se o backend foi executado e os arquivos estão corretos.")
        st.stop() # Para a execução do aplicativo Streamlit

final_model, df_consolidado_processed, current_ufpe_notes, previous_ufpe_notes, features, base_features, UFPE_ORIGINAL_NAME = cached_load_artifacts()

# --- Construção da Interface Streamlit ---

st.title("Simulador de Ranking da UFPE (RUF)")
st.markdown("### Preveja a Posição da UFPE no Ranking RUF em um Cenário Dinâmico")
st.write("Ajuste as variações percentuais para os critérios da UFPE e veja o impacto na sua posição, considerando o crescimento médio dos concorrentes.")

# Barra Lateral (Sidebar) para as entradas do usuário
st.sidebar.header("Defina as Variações para a UFPE")
st.sidebar.write(f"Notas atuais da UFPE (ano mais recente):")
for k, v in current_ufpe_notes.items():
    st.sidebar.write(f"- {k.replace('_', ' ')}: {v:.2f}")

# Entradas do usuário para as variações percentuais usando sliders
ufpe_ensino_var = st.sidebar.slider("Variação % em Ensino", -20.0, 20.0, 0.0, 0.5)
ufpe_pesquisa_var = st.sidebar.slider("Variação % em Pesquisa", -20.0, 20.0, 0.0, 0.5)
ufpe_mercado_var = st.sidebar.slider("Variação % em Mercado", -20.0, 20.0, 0.0, 0.5)
ufpe_inovacao_var = st.sidebar.slider("Variação % em Inovação", -20.0, 20.0, 0.0, 0.5)
ufpe_internacionalizacao_var = st.sidebar.slider("Variação % em Internacionalização", -20.0, 20.0, 0.0, 0.5)

# Botão para iniciar a simulação
if st.sidebar.button("Simular Ranking"):
    with st.spinner("Executando simulação..."):
        ufpe_predicted_ranking, ufpe_predicted_position, ufpe_simulated_notes, top_10_ranking =             run_simulation(
                ufpe_ensino_var, ufpe_pesquisa_var, ufpe_mercado_var,
                ufpe_inovacao_var, ufpe_internacionalizacao_var,
                df_consolidado_processed, current_ufpe_notes, previous_ufpe_notes, final_model,
                features, base_features, UFPE_ORIGINAL_NAME
            )

        st.subheader("Resultados da Simulação")
        st.write(f"Com as variações propostas para a UFPE e o crescimento médio dos competidores:")
        st.metric(label="Posição Prevista da UFPE", value=f"{ufpe_predicted_position}º lugar")
        st.write(f"*(Ranking técnico previsto: {ufpe_predicted_ranking:.2f})*")

        st.subheader("Notas Simuladas da UFPE")
        simulated_notes_df = pd.DataFrame([ufpe_simulated_notes]).T
        simulated_notes_df.columns = ["Nota Simulada"]
        st.dataframe(simulated_notes_df.style.format("{:.2f}"))

        st.subheader("Top 10 Universidades no Cenário Simulado")
        st.dataframe(top_10_ranking[['Universidade', 'Predicted_Ranking', 'Predicted_Position']].style.format({'Predicted_Ranking': "{:.2f}"}))

        st.success("Simulação concluída!")
