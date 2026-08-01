# app.py

from __future__ import annotations

import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


from model_logic import (
    calculate_average_trends,
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
    page_title="Simulador de Ranking RUF",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# CAMINHOS
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
def load_cached_model(model_path: str):
    """
    Carrega o modelo uma única vez durante a execução do app.
    """
    return load_model(model_path)


@st.cache_data(show_spinner="Carregando dados...")
def load_cached_data(input_path: str) -> pd.DataFrame:
    """
    Carrega os dados e mantém o resultado em cache.
    """
    return load_data(input_path)


# ============================================================
# FUNÇÕES AUXILIARES DA INTERFACE
# ============================================================

def show_file_status() -> None:
    """
    Mostra informações úteis caso algum arquivo não seja encontrado.
    """
    st.write("Diretório do aplicativo:", PROJECT_BASE_PATH)
    st.write("Pasta de dados:", DATA_PATH)
    st.write("Pasta de modelos:", MODELS_PATH)

    if not DATA_PATH.exists():
        st.error(f"A pasta de dados não existe: {DATA_PATH}")

    if not MODELS_PATH.exists():
        st.error(f"A pasta de modelos não existe: {MODELS_PATH}")

    if not INPUT_FILE_PATH.exists():
        st.error(
            "Arquivo Excel não encontrado:\n"
            f"{INPUT_FILE_PATH}"
        )

    if not MODEL_PATH.exists():
        st.error(
            "Arquivo do modelo não encontrado:\n"
            f"{MODEL_PATH}"
        )


def validate_dataframe(df: pd.DataFrame) -> None:
    """
    Valida colunas mínimas necessárias para a aplicação.
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
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "As seguintes colunas obrigatórias não foram encontradas "
            f"na planilha: {missing_columns}"
        )


def get_model_features(model) -> list[str]:
    """
    Obtém a lista de features do modelo XGBoost.
    """
    feature_names = None

    try:
        feature_names = model.get_booster().feature_names
    except Exception:
        feature_names = None

    if not feature_names:
        feature_names = getattr(model, "feature_names_in_", None)

    if not feature_names:
        raise ValueError(
            "Não foi possível identificar as features esperadas pelo modelo. "
            "O modelo precisa ter sido treinado com nomes de colunas."
        )

    return list(feature_names)


def format_number(value, decimals: int = 2):
    """
    Formata números para exibição.
    """
    if pd.isna(value):
        return "N/A"

    return f"{float(value):.{decimals}f}"


# ============================================================
# APLICAÇÃO PRINCIPAL
# ============================================================

st.title("📊 Simulador de Ranking RUF para a UFPE")

try:
    # --------------------------------------------------------
    # Verificação inicial dos arquivos
    # --------------------------------------------------------

    if not MODEL_PATH.exists() or not INPUT_FILE_PATH.exists():
        st.error(
            "Não foi possível localizar um ou mais arquivos necessários."
        )

        with st.expander("Detalhes dos caminhos"):
            show_file_status()

        st.stop()

    # --------------------------------------------------------
    # Carregamento
    # --------------------------------------------------------

    model = load_cached_model(str(MODEL_PATH))
    df_full = load_cached_data(str(INPUT_FILE_PATH))

    validate_dataframe(df_full)

    # --------------------------------------------------------
    # Edição mais recente
    # --------------------------------------------------------

    df_full["Edicao_RUF"] = pd.to_numeric(
        df_full["Edicao_RUF"],
        errors="coerce",
    )

    if df_full["Edicao_RUF"].isna().all():
        raise ValueError(
            "A coluna 'Edicao_RUF' não contém valores numéricos válidos."
        )

    latest_edition = int(df_full["Edicao_RUF"].max())

    df_base = df_full[
        df_full["Edicao_RUF"] == latest_edition
    ].copy()

    if df_base.empty:
        raise ValueError(
            f"Não existem dados para a edição {latest_edition}."
        )

    # --------------------------------------------------------
    # Localização da UFPE
    # --------------------------------------------------------

    ufpe_data = df_base[
        df_base["Universidade"] == ufpe_exact_name
    ]

    if ufpe_data.empty:
        available_names = (
            df_base["Universidade"]
            .dropna()
            .astype(str)
            .head(20)
            .tolist()
        )

        raise ValueError(
            f"A universidade '{ufpe_exact_name}' não foi encontrada "
            f"na edição {latest_edition}.\n\n"
            "Alguns nomes disponíveis na planilha: "
            f"{available_names}"
        )

    original_ufpe = ufpe_data.iloc[0]

    # --------------------------------------------------------
    # Tendências médias
    # --------------------------------------------------------

    with st.spinner("Calculando tendências históricas..."):
        average_trends = calculate_average_trends(
            df_full_data=df_full,
            ufpe_name=ufpe_exact_name,
        )

    # --------------------------------------------------------
    # Features do modelo
    # --------------------------------------------------------

    model_expected_features = get_model_features(model)

    # --------------------------------------------------------
    # Cabeçalho
    # --------------------------------------------------------

    base_year = get_year_from_edition(latest_edition)
    simulated_edition = latest_edition + 1
    simulated_year = get_year_from_edition(simulated_edition)

    st.markdown(
        f"**Edição base:** {base_year} "
        f"(Edição {latest_edition})"
    )

    st.markdown(
        f"**Próxima edição simulada:** {simulated_year} "
        f"(Edição {simulated_edition})"
    )

    st.info(
        f"Foram encontradas {len(df_base)} universidades na edição base."
    )

    # --------------------------------------------------------
    # Controles da simulação
    # --------------------------------------------------------

    st.divider()
    st.subheader("Configurações da simulação")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Notas da UFPE")

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
        st.markdown("#### Notas da UFPE")

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
        st.markdown("#### Notas da UFPE")

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
        simulated_df = simulate_full_ranking_avg_trend(
            df_base_edicao_6=df_base,
            model=model,
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
        f"Resultado da simulação para a UFPE — {simulated_year}"
    )

    result_col1, result_col2 = st.columns(2)

    with result_col1:
        st.metric(
            label="Ranking previsto",
            value=int(simulated_ufpe["Simulated_Ranking"]),
        )

    with result_col2:
        st.metric(
            label="Nota geral prevista",
            value=format_number(simulated_ufpe["Nota"]),
        )

    # --------------------------------------------------------
    # Comparativo tabular
    # --------------------------------------------------------

    st.divider()
    st.subheader("Comparativo original versus simulado")

    comparison_metrics = [
        ("Ranking", "Ranking", "Simulated_Ranking"),
        ("Nota Geral", "Nota", "Nota"),
        ("Nota em Ensino", "Nota em Ensino", "Nota em Ensino"),
        ("Nota em Pesquisa", "Nota em Pesquisa", "Nota em Pesquisa"),
        ("Nota em Mercado", "Nota em Mercado", "Nota em Mercado"),
        ("Nota em Inovação", "Nota em Inovação", "Nota em Inovação"),
        (
            "Nota em Internacionalização",
            "Nota em Internacionalização",
            "Nota em Internacionalização",
        ),
    ]

    comparison_rows = []

    for label, original_column, simulated_column in comparison_metrics:
        original_value = original_ufpe[original_column]
        simulated_value = simulated_ufpe[simulated_column]

        difference = simulated_value - original_value

        # Para ranking, uma diferença positiva deve significar melhora
        if label == "Ranking":
            difference = original_value - simulated_value

        comparison_rows.append(
            {
                "Métrica": label,
                f"{base_year} — Original": original_value,
                f"{simulated_year} — Simulada": simulated_value,
                "Diferença": difference,
            }
        )

    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df = comparison_df.set_index("Métrica")

    st.dataframe(
        comparison_df,
        use_container_width=True,
    )

    # --------------------------------------------------------
    # Gráfico
    # --------------------------------------------------------

    st.divider()
    st.subheader("Comparativo gráfico das notas")

    chart_rows = []

    chart_metrics = [
        ("Ensino", "Nota em Ensino"),
        ("Pesquisa", "Nota em Pesquisa"),
        ("Mercado", "Nota em Mercado"),
        ("Inovação", "Nota em Inovação"),
        (
            "Internacionalização",
            "Nota em Internacionalização",
        ),
        ("Geral", "Nota"),
    ]

    for label, column in chart_metrics:
        chart_rows.append(
            {
                "Métrica": label,
                "Edição": f"{base_year} — Original",
                "Nota": original_ufpe[column],
            }
        )

        chart_rows.append(
            {
                "Métrica": label,
                "Edição": f"{simulated_year} — Simulada",
                "Nota": simulated_ufpe[column],
            }
        )

    chart_data = pd.DataFrame(chart_rows)

    chart = (
        alt.Chart(chart_data)
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
            height=450,
            title="Notas da UFPE por dimensão",
        )
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

    display_df = simulated_df[display_columns].head(10).copy()

    display_df = display_df.rename(
        columns={
            "Simulated_Ranking": "Ranking Previsto",
            "Universidade": "Instituição",
            "Nota": "Nota Geral",
        }
    )

    note_display_columns = [
        column
        for column in display_df.columns
        if "Nota" in column
    ]

    for column in note_display_columns:
        display_df[column] = display_df[column].map(
            lambda value: format_number(value)
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Rodapé
    # --------------------------------------------------------

    st.divider()

    st.caption(
        "As previsões são estimativas baseadas no modelo carregado "
        "e não representam garantia de resultados futuros."
    )

except Exception as exc:
    st.error(
        "O aplicativo encontrou um erro durante a execução."
    )

    with st.expander("Exibir detalhes técnicos do erro"):
        st.exception(exc)

    st.stop()
