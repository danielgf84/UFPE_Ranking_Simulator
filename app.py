from __future__ import annotations

import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from models.model_logic import (
    load_model as ml_load_model,
    load_data as ml_load_data,
    simulate_full_ranking_avg_trend,
    calculate_average_trends,
    ufpe_exact_name,
    get_year_from_edition,
)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Simulador de Ranking RUF para a UFPE",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# CAMINHOS DO PROJETO
# ============================================================

PROJECT_BASE_PATH = Path(__file__).resolve().parent

DATA_PATH = PROJECT_BASE_PATH / "data"
MODELS_PATH = PROJECT_BASE_PATH / "models"

MODEL_PATH = MODELS_PATH / "xgboost_model.pkl"
INPUT_FILE_PATH = DATA_PATH / "ruf_consolidado_fe.xlsx"


# ============================================================
# FUNÇÕES DE CARREGAMENTO COM CACHE
# ============================================================

@st.cache_resource(show_spinner="Carregando modelo...")
def load_cached_model(path: str):
    """
    Carrega o modelo uma única vez.
    """
    return ml_load_model(path)


@st.cache_data(show_spinner="Carregando dados...")
def load_cached_data(path: str) -> pd.DataFrame:
    """
    Carrega a planilha uma única vez.
    """
    return ml_load_data(path)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def get_model_features(model) -> list[str]:
    """
    Obtém os nomes das features esperadas pelo modelo.

    Para modelos XGBoost, normalmente os nomes estão disponíveis
    em model.get_booster().feature_names.
    """

    feature_names = None

    try:
        booster = model.get_booster()
        feature_names = booster.feature_names
    except Exception:
        feature_names = None

    if not feature_names:
        feature_names = getattr(
            model,
            "feature_names_in_",
            None,
        )

    if not feature_names:
        raise ValueError(
            "Não foi possível identificar as features esperadas "
            "pelo modelo."
        )

    return list(feature_names)


def validate_required_columns(df: pd.DataFrame) -> None:
    """
    Verifica se a planilha possui as colunas necessárias.
    """

    required_columns = [
        "Edicao_RUF",
        "Universidade",
        "Ranking",
        "Nota",
        "Nota em Ensino",
        "Nota em Pesquisa",
        "Nota em Mercado",
        "Nota em Inovação",
        "Nota em Internacionalização",
        "Posição em Ensino",
        "Posição em Pesquisa",
        "Posição em Mercado",
        "Posição em Inovação",
        "Posição em Internacionalização",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "As seguintes colunas obrigatórias não foram encontradas "
            f"na planilha: {missing_columns}"
        )


def show_path_information() -> None:
    """
    Exibe informações sobre os caminhos do projeto.
    """

    st.write(
        f"Diretório do aplicativo: `{PROJECT_BASE_PATH}`"
    )

    st.write(
        f"Pasta de dados: `{DATA_PATH}`"
    )

    st.write(
        f"Pasta de modelos: `{MODELS_PATH}`"
    )

    st.write(
        f"Arquivo Excel: `{INPUT_FILE_PATH}`"
    )

    st.write(
        f"Arquivo do modelo: `{MODEL_PATH}`"
    )

    st.write(
        f"Excel encontrado: `{INPUT_FILE_PATH.exists()}`"
    )

    st.write(
        f"Modelo encontrado: `{MODEL_PATH.exists()}`"
    )

    if DATA_PATH.exists():
        st.write(
            "Arquivos na pasta `data`:",
            os.listdir(DATA_PATH),
        )

    if MODELS_PATH.exists():
        st.write(
            "Arquivos na pasta `models`:",
            os.listdir(MODELS_PATH),
        )


def format_number(value, decimals: int = 2) -> str:
    """
    Formata valores numéricos.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


# ============================================================
# APLICAÇÃO PRINCIPAL
# ============================================================

try:
    # --------------------------------------------------------
    # Verificação dos arquivos
    # --------------------------------------------------------

    if not INPUT_FILE_PATH.exists() or not MODEL_PATH.exists():
        st.error(
            "Um ou mais arquivos necessários não foram encontrados."
        )

        with st.expander("Ver detalhes dos caminhos"):
            show_path_information()

        st.stop()

    # --------------------------------------------------------
    # Carregamento do modelo e da planilha
    # --------------------------------------------------------

    loaded_model = load_cached_model(
        str(MODEL_PATH)
    )

    df_full = load_cached_data(
        str(INPUT_FILE_PATH)
    )

    if loaded_model is None:
        raise ValueError(
            "O modelo foi carregado como None."
        )

    if df_full is None or df_full.empty:
        raise ValueError(
            "A planilha foi carregada, mas não possui dados."
        )

    validate_required_columns(df_full)

    # --------------------------------------------------------
    # Tratamento da edição
    # --------------------------------------------------------

    df_full["Edicao_RUF"] = pd.to_numeric(
        df_full["Edicao_RUF"],
        errors="coerce",
    )

    df_full = df_full.dropna(
        subset=["Edicao_RUF"]
    ).copy()

    if df_full.empty:
        raise ValueError(
            "A coluna 'Edicao_RUF' não contém valores válidos."
        )

    df_full["Edicao_RUF"] = (
        df_full["Edicao_RUF"]
        .astype(int)
    )

    latest_edition = int(
        df_full["Edicao_RUF"].max()
    )

    df_edicao_base = df_full[
        df_full["Edicao_RUF"] == latest_edition
    ].copy()

    if df_edicao_base.empty:
        raise ValueError(
            "Não foram encontrados dados para a edição "
            f"{latest_edition}."
        )

    # --------------------------------------------------------
    # Localização da UFPE
    # --------------------------------------------------------

    ufpe_rows = df_edicao_base[
        df_edicao_base["Universidade"] == ufpe_exact_name
    ]

    if ufpe_rows.empty:
        sample_names = (
            df_edicao_base["Universidade"]
            .dropna()
            .astype(str)
            .head(20)
            .tolist()
        )

        raise ValueError(
            f"A universidade '{ufpe_exact_name}' não foi encontrada "
            f"na edição {latest_edition}.\n\n"
            "Verifique se o nome está exatamente igual ao da planilha.\n"
            f"Alguns nomes encontrados: {sample_names}"
        )

    original_ufpe = ufpe_rows.iloc[0]

    # --------------------------------------------------------
    # Tendências históricas
    # --------------------------------------------------------

    average_trends = calculate_average_trends(
        df_full,
        ufpe_exact_name,
    )

    # --------------------------------------------------------
    # Features esperadas pelo modelo
    # --------------------------------------------------------

    model_expected_features = get_model_features(
        loaded_model
    )

    if not model_expected_features:
        raise ValueError(
            "O modelo não possui nomes de features disponíveis."
        )

    # --------------------------------------------------------
    # Cabeçalho
    # --------------------------------------------------------

    base_year = get_year_from_edition(
        latest_edition
    )

    simulated_edition = latest_edition + 1

    simulated_year = get_year_from_edition(
        simulated_edition
    )

    st.title(
        "📊 Simulador de Ranking RUF para a UFPE"
    )

    st.markdown(
        f"**Edição base:** {base_year} "
        f"(Edição {latest_edition})"
    )

    st.markdown(
        f"**Edição simulada:** {simulated_year} "
        f"(Edição {simulated_edition})"
    )

    st.info(
        f"Foram encontradas {len(df_edicao_base)} "
        "universidades na edição base."
    )

    # --------------------------------------------------------
    # Controles da simulação
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "Configurações da simulação para a UFPE"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            "#### Variação das notas"
        )

        pct_change_ensino = (
            st.slider(
                "Ensino (%)",
                min_value=-10.0,
                max_value=10.0,
                value=0.0,
                step=0.1,
            )
            / 100.0
        )

        pct_change_pesquisa = (
            st.slider(
                "Pesquisa (%)",
                min_value=-10.0,
                max_value=10.0,
                value=0.0,
                step=0.1,
            )
            / 100.0
        )

    with col2:
        st.markdown(
            "#### Variação das notas"
        )

        pct_change_mercado = (
            st.slider(
                "Mercado (%)",
                min_value=-10.0,
                max_value=10.0,
                value=0.0,
                step=0.1,
            )
            / 100.0
        )

        pct_change_inovacao = (
            st.slider(
                "Inovação (%)",
                min_value=-10.0,
                max_value=10.0,
                value=0.0,
                step=0.1,
            )
            / 100.0
        )

    with col3:
        st.markdown(
            "#### Variação das notas"
        )

        pct_change_internacionalizacao = (
            st.slider(
                "Internacionalização (%)",
                min_value=-10.0,
                max_value=10.0,
                value=0.0,
                step=0.1,
            )
            / 100.0
        )

        apply_other_uni_trends = st.checkbox(
            "Aplicar tendências médias às outras universidades",
            value=True,
        )

    # --------------------------------------------------------
    # Execução da simulação
    # --------------------------------------------------------

    with st.spinner("Executando simulação..."):
        simulated_df = (
            simulate_full_ranking_avg_trend(
                df_edicao_base,
                loaded_model,
                ufpe_exact_name,
                average_trends,
                pct_change_ensino,
                pct_change_pesquisa,
                pct_change_mercado,
                pct_change_inovacao,
                pct_change_internacionalizacao,
                apply_other_uni_trends,
                model_expected_features,
            )
        )

    if simulated_df is None or simulated_df.empty:
        raise ValueError(
            "A simulação não retornou resultados."
        )

    # --------------------------------------------------------
    # Resultado da UFPE
    # --------------------------------------------------------

    simulated_ufpe_rows = simulated_df[
        simulated_df["Universidade"] == ufpe_exact_name
    ]

    if simulated_ufpe_rows.empty:
        raise ValueError(
            "A UFPE não foi encontrada no resultado da simulação."
        )

    simulated_ufpe = simulated_ufpe_rows.iloc[0]

    st.divider()

    st.subheader(
        "Resultado da simulação para a UFPE"
    )

    result_col1, result_col2 = st.columns(2)

    with result_col1:
        st.metric(
            label="Ranking previsto",
            value=int(
                simulated_ufpe["Simulated_Ranking"]
            ),
        )

    with result_col2:
        st.metric(
            label="Nota geral prevista",
            value=format_number(
                simulated_ufpe["Nota"]
            ),
        )

    # --------------------------------------------------------
    # Comparativo original versus simulado
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "Comparativo detalhado"
    )

    original_label = (
        f"Edição {base_year} — Original"
    )

    simulated_label = (
        f"Edição {simulated_year} — Simulada"
    )

    comparison_df = pd.DataFrame(
        {
            "Métrica": [
                "Ranking",
                "Nota Geral",
                "Nota em Ensino",
                "Nota em Pesquisa",
                "Nota em Mercado",
                "Nota em Inovação",
                "Nota em Internacionalização",
            ],
            original_label: [
                original_ufpe["Ranking"],
                original_ufpe["Nota"],
                original_ufpe["Nota em Ensino"],
                original_ufpe["Nota em Pesquisa"],
                original_ufpe["Nota em Mercado"],
                original_ufpe["Nota em Inovação"],
                original_ufpe[
                    "Nota em Internacionalização"
                ],
            ],
            simulated_label: [
                simulated_ufpe["Simulated_Ranking"],
                simulated_ufpe["Nota"],
                simulated_ufpe["Nota em Ensino"],
                simulated_ufpe["Nota em Pesquisa"],
                simulated_ufpe["Nota em Mercado"],
                simulated_ufpe["Nota em Inovação"],
                simulated_ufpe[
                    "Nota em Internacionalização"
                ],
            ],
        }
    )

    comparison_df["Diferença"] = (
        comparison_df[simulated_label]
        - comparison_df[original_label]
    )

    ranking_mask = (
        comparison_df["Métrica"] == "Ranking"
    )

    # No ranking, valor positivo representa melhora
    comparison_df.loc[
        ranking_mask,
        "Diferença",
    ] = -comparison_df.loc[
        ranking_mask,
        "Diferença",
    ]

    st.dataframe(
        comparison_df.set_index("Métrica"),
        use_container_width=True,
    )

    # --------------------------------------------------------
    # Gráfico comparativo
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "Comparativo gráfico das notas"
    )

    chart_data = pd.DataFrame(
        {
            "Métrica": [
                "Ensino",
                "Pesquisa",
                "Mercado",
                "Inovação",
                "Internacionalização",
                "Geral",
            ],
            original_label: [
                original_ufpe["Nota em Ensino"],
                original_ufpe["Nota em Pesquisa"],
                original_ufpe["Nota em Mercado"],
                original_ufpe["Nota em Inovação"],
                original_ufpe[
                    "Nota em Internacionalização"
                ],
                original_ufpe["Nota"],
            ],
            simulated_label: [
                simulated_ufpe["Nota em Ensino"],
                simulated_ufpe["Nota em Pesquisa"],
                simulated_ufpe["Nota em Mercado"],
                simulated_ufpe["Nota em Inovação"],
                simulated_ufpe[
                    "Nota em Internacionalização"
                ],
                simulated_ufpe["Nota"],
            ],
        }
    )

    chart_data_melted = chart_data.melt(
        id_vars=["Métrica"],
        var_name="Edição",
        value_name="Nota",
    )

    chart = (
        alt.Chart(chart_data_melted)
        .mark_bar()
        .encode(
            x=alt.X(
                "Métrica:N",
                title="Dimensão da nota",
            ),
            y=alt.Y(
                "Nota:Q",
                title="Valor da nota",
            ),
            color=alt.Color(
                "Edição:N",
                title="Edição RUF",
            ),
            tooltip=[
                "Métrica",
                "Edição",
                "Nota",
            ],
        )
        .properties(
            title="Notas da UFPE por dimensão",
            height=450,
        )
        .interactive()
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )

    # --------------------------------------------------------
    # Top 10
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "Top 10 instituições previstas"
    )

    note_columns = [
        column
        for column in simulated_df.columns
        if column.startswith("Nota em ")
    ]

    display_columns = [
        "Simulated_Ranking",
        "Universidade",
        "Nota",
        *note_columns,
    ]

    display_df = simulated_df[
        display_columns
    ].head(10).copy()

    display_df = display_df.rename(
        columns={
            "Simulated_Ranking": "Ranking Previsto",
            "Universidade": "Instituição",
            "Nota": "Nota Geral",
        }
    )

    numeric_columns = [
        column
        for column in display_df.columns
        if column == "Nota Geral"
        or column.startswith("Nota em ")
    ]

    for column in numeric_columns:
        display_df[column] = display_df[column].apply(
            lambda value: format_number(value)
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Aviso final
    # --------------------------------------------------------

    st.divider()

    st.info(
        "Este simulador utiliza um modelo de Machine Learning "
        "treinado com dados históricos do RUF. As previsões são "
        "estimativas e não garantem resultados futuros."
    )


except Exception as exc:
    st.error(
        "O aplicativo encontrou um erro durante a execução."
    )

    with st.expander("Exibir detalhes técnicos do erro"):
        st.exception(exc)

    st.stop()
