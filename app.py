from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from models.model_logic import (
    calculate_average_trends,
    get_model_feature_names,
    get_year_from_edition,
    load_data,
    load_model,
    simulate_full_ranking_avg_trend,
    ufpe_exact_name,
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
# FUNÇÕES CACHEADAS
# ============================================================

@st.cache_resource(show_spinner="Carregando modelo...")
def load_cached_model(path: str):
    """
    Carrega o modelo apenas uma vez durante a execução do aplicativo.
    """
    return load_model(path)


@st.cache_data(show_spinner="Carregando dados...")
def load_cached_data(path: str) -> pd.DataFrame:
    """
    Carrega a planilha e mantém os dados em cache.
    """
    return load_data(path)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def validate_required_columns(df: pd.DataFrame) -> None:
    """
    Verifica se a planilha possui as colunas essenciais.
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
            "As seguintes colunas obrigatórias não existem na planilha:\n"
            f"{missing_columns}"
        )


def show_path_information() -> None:
    """
    Exibe os caminhos utilizados pelo aplicativo para facilitar a depuração.
    """

    st.write(f"Diretório do aplicativo: `{PROJECT_BASE_PATH}`")
    st.write(f"Pasta de dados: `{DATA_PATH}`")
    st.write(f"Pasta de modelos: `{MODELS_PATH}`")
    st.write(f"Arquivo Excel: `{INPUT_FILE_PATH}`")
    st.write(f"Arquivo do modelo: `{MODEL_PATH}`")

    st.write(
        f"Arquivo Excel existe: `{INPUT_FILE_PATH.exists()}`"
    )
    st.write(
        f"Arquivo do modelo existe: `{MODEL_PATH.exists()}`"
    )


def format_value(value, decimals: int = 2):
    """
    Formata valores numéricos para exibição.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


# ============================================================
# EXECUÇÃO PRINCIPAL
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
    # Carregamento do modelo e dos dados
    # --------------------------------------------------------

    loaded_model = load_cached_model(str(MODEL_PATH))
    df_full = load_cached_data(str(INPUT_FILE_PATH))

    if df_full.empty:
        st.error("A planilha foi carregada, mas não contém dados.")
        st.stop()

    validate_required_columns(df_full)

    # --------------------------------------------------------
    # Preparação da coluna de edição
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
            "A coluna 'Edicao_RUF' não possui valores válidos."
        )

    df_full["Edicao_RUF"] = (
        df_full["Edicao_RUF"]
        .astype(int)
    )

    latest_edition = int(
        df_full["Edicao_RUF"].max()
    )

    df_base = df_full[
        df_full["Edicao_RUF"] == latest_edition
    ].copy()

    if df_base.empty:
        raise ValueError(
            f"Não foram encontrados dados para a edição "
            f"{latest_edition}."
        )

    # --------------------------------------------------------
    # Localização da UFPE
    # --------------------------------------------------------

    ufpe_rows = df_base[
        df_base["Universidade"] == ufpe_exact_name
    ]

    if ufpe_rows.empty:
        sample_names = (
            df_base["Universidade"]
            .dropna()
            .astype(str)
            .head(20)
            .tolist()
        )

        raise ValueError(
            f"A universidade '{ufpe_exact_name}' não foi encontrada "
            f"na edição {latest_edition}.\n\n"
            "Verifique se o nome na planilha é exatamente igual. "
            f"Alguns nomes encontrados: {sample_names}"
        )

    original_ufpe = ufpe_rows.iloc[0]

    # --------------------------------------------------------
    # Tendências históricas
    # --------------------------------------------------------

    average_trends = calculate_average_trends(
        df_full_data=df_full,
        ufpe_name=ufpe_exact_name,
    )

    # --------------------------------------------------------
    # Features esperadas pelo modelo
    # --------------------------------------------------------

    model_expected_features = get_model_feature_names(
        loaded_model
    )

    # --------------------------------------------------------
    # Interface
    # --------------------------------------------------------

    st.title("📊 Simulador de Ranking RUF para a UFPE")

    base_year = get_year_from_edition(latest_edition)
    simulated_edition = latest_edition + 1
    simulated_year = get_year_from_edition(
        simulated_edition
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
        f"Foram encontradas {len(df_base)} universidades "
        "na edição base."
    )

    # --------------------------------------------------------
    # Controles da simulação
    # --------------------------------------------------------

    st.divider()
    st.subheader("Configurações da simulação")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Variação das notas da UFPE")

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
        st.markdown("#### Variação das notas da UFPE")

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
        st.markdown("#### Variação das notas da UFPE")

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
    # Execução
    # --------------------------------------------------------

    with st.spinner("Executando simulação..."):
        simulated_df = simulate_full_ranking_avg_trend(
            df_base_edicao_6=df_base,
            model=loaded_model,
            ufpe_name=ufpe_exact_name,
            all_universities_average_trends=average_trends,
            pct_change_ensino=pct_change_ensino,
            pct_change_pesquisa=pct_change_pesquisa,
            pct_change_mercado=pct_change_mercado,
            pct_change_inovacao=pct_change_inovacao,
            pct_change_internacionalizacao=(
                pct_change_internacionalizacao
            ),
            apply_other_uni_trends=apply_other_uni_trends,
            model_expected_features=model_expected_features,
        )

    simulated_ufpe_rows = simulated_df[
        simulated_df["Universidade"] == ufpe_exact_name
    ]

    if simulated_ufpe_rows.empty:
        raise ValueError(
            "A UFPE não foi encontrada no resultado da simulação."
        )

    simulated_ufpe = simulated_ufpe_rows.iloc[0]

    # --------------------------------------------------------
    # Resultado principal
    # --------------------------------------------------------

    st.divider()
    st.subheader(
        f"Resultado da simulação para a UFPE — {simulated_year}"
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
            value=format_value(
                simulated_ufpe["Nota"]
            ),
        )

    # --------------------------------------------------------
    # Comparativo detalhado
    # --------------------------------------------------------

    st.divider()
    st.subheader("Comparativo original versus simulado")

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
    # Gráfico
    # --------------------------------------------------------

    st.divider()
    st.subheader("Comparativo gráfico das notas")

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
                title="Edição",
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
    st.subheader("Top 10 instituições previstas")

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
            lambda value: format_value(value)
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

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

    with st.expander("Exibir detalhes técnicos"):
        st.exception(exc)

    st.stop()
