from __future__ import annotations

import os
from typing import Dict, Iterable, Optional

import joblib
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ufpe_exact_name = "Universidade Federal de Pernambuco"

target_column = "Ranking"

EDITION_YEAR_MAP = {
    1: 2017,
    2: 2018,
    3: 2019,
    4: 2023,
    5: 2024,
    6: 2025,
    7: 2026,
}

EPSILON = 1e-6

NOTA_COLS = [
    "Nota em Ensino",
    "Nota em Pesquisa",
    "Nota em Mercado",
    "Nota em Inovação",
    "Nota em Internacionalização",
]

POSICAO_COLS = [
    "Posição em Ensino",
    "Posição em Pesquisa",
    "Posição em Mercado",
    "Posição em Inovação",
    "Posição em Internacionalização",
]

RANKING_COLS = [
    "Ranking",
    *POSICAO_COLS,
]


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def get_year_from_edition(edition_number):
    """
    Retorna o ano correspondente à edição do RUF.
    """

    try:
        edition_number = int(edition_number)
    except (TypeError, ValueError):
        pass

    return EDITION_YEAR_MAP.get(
        edition_number,
        f"Ano Desconhecido (Edição {edition_number})",
    )


def get_model_feature_names(model) -> list[str]:
    """
    Retorna os nomes das features utilizadas no treinamento do modelo.

    Para modelos XGBoost, os nomes normalmente estão disponíveis em:
    model.get_booster().feature_names
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
            "Não foi possível identificar as features esperadas pelo modelo."
        )

    return list(feature_names)


def ensure_required_columns(
    df: pd.DataFrame,
    required_columns: Iterable[str],
    dataframe_name: str,
) -> None:
    """
    Verifica se as colunas obrigatórias estão presentes.
    """

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{dataframe_name} não possui as colunas obrigatórias: "
            f"{missing_columns}"
        )


# ============================================================
# CARREGAMENTO
# ============================================================

def load_model(path: str):
    """
    Carrega o modelo salvo.
    """

    print(f"MODEL_LOGIC_DEBUG: Carregando modelo de: {path}")

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Arquivo do modelo não encontrado: {path}"
        )

    try:
        model = joblib.load(path)

    except Exception as exc:
        raise RuntimeError(
            f"Erro ao carregar o modelo '{path}': {exc}"
        ) from exc

    print(
        "MODEL_LOGIC_DEBUG: Modelo carregado com sucesso: "
        f"{os.path.basename(path)}"
    )

    return model


def load_data(path: str) -> pd.DataFrame:
    """
    Carrega os dados da planilha Excel.
    """

    print(f"MODEL_LOGIC_DEBUG: Carregando dados de: {path}")

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Arquivo de dados não encontrado: {path}"
        )

    try:
        df = pd.read_excel(path)

    except Exception as exc:
        raise RuntimeError(
            f"Erro ao carregar a planilha '{path}': {exc}"
        ) from exc

    if df.empty:
        raise ValueError("A planilha está vazia.")

    print(
        "MODEL_LOGIC_DEBUG: Dados carregados com sucesso. "
        f"Linhas: {len(df)} | Colunas: {len(df.columns)}"
    )

    return df


# ============================================================
# TENDÊNCIAS MÉDIAS
# ============================================================

def calculate_average_trends(
    df_full_data: pd.DataFrame,
    ufpe_name: str,
) -> Dict[str, float]:
    """
    Calcula a variação percentual média das demais universidades
    entre edições consecutivas.
    """

    ensure_required_columns(
        df_full_data,
        ["Universidade", "Edicao_RUF"],
        "df_full_data",
    )

    df = df_full_data.copy()

    df = df[
        df["Universidade"] != ufpe_name
    ].copy()

    trend_columns = [
        "Ranking",
        "Nota",
        *NOTA_COLS,
        *POSICAO_COLS,
    ]

    available_columns = [
        column
        for column in trend_columns
        if column in df.columns
    ]

    df["Edicao_RUF"] = pd.to_numeric(
        df["Edicao_RUF"],
        errors="coerce",
    )

    for column in available_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=["Universidade", "Edicao_RUF"]
    ).sort_values(
        by=["Universidade", "Edicao_RUF"]
    )

    grouped = df.groupby(
        "Universidade",
        sort=False,
    )

    trends = {}

    for column in available_columns:
        current = df[column]
        previous = grouped[column].shift(1)

        valid_previous = previous.notna()

        denominator = previous.replace(
            0,
            EPSILON,
        )

        percentage_change = (
            (current - previous) / denominator
        )

        percentage_change = percentage_change.replace(
            [np.inf, -np.inf],
            np.nan,
        )

        percentage_change = percentage_change[
            valid_previous
            & percentage_change.notna()
        ]

        average_change = (
            float(percentage_change.mean())
            if not percentage_change.empty
            else 0.0
        )

        trends[
            f"{column}_pct_change_prev"
        ] = average_change

    print(
        "MODEL_LOGIC_DEBUG: Tendências médias calculadas."
    )

    return trends


# ============================================================
# PREPARAÇÃO DAS FEATURES
# ============================================================

def prepare_model_input(
    df_simulated: pd.DataFrame,
    df_base: pd.DataFrame,
    model_expected_features: list[str],
) -> pd.DataFrame:
    """
    Cria o DataFrame final enviado ao modelo, com as mesmas
    features e na mesma ordem do treinamento.
    """

    ensure_required_columns(
        df_simulated,
        ["Universidade"],
        "df_simulated",
    )

    ensure_required_columns(
        df_base,
        ["Universidade"],
        "df_base",
    )

    simulated = df_simulated.copy()
    base = df_base.copy()

    simulated = simulated.sort_values(
        "Universidade"
    ).set_index("Universidade")

    base = base.sort_values(
        "Universidade"
    ).set_index("Universidade")

    base_aligned = base.reindex(
        simulated.index
    )

    features = simulated.copy()

    columns_for_features = [
        *NOTA_COLS,
        *POSICAO_COLS,
        "Nota",
        "Ranking",
    ]

    for column in columns_for_features:
        if column not in simulated.columns:
            continue

        if column not in base_aligned.columns:
            continue

        current = pd.to_numeric(
            simulated[column],
            errors="coerce",
        ).fillna(0)

        previous = pd.to_numeric(
            base_aligned[column],
            errors="coerce",
        ).fillna(0)

        diff_column = f"{column}_diff_prev"
        pct_column = f"{column}_pct_change_prev"

        features[diff_column] = current - previous

        denominator = previous.replace(
            0,
            EPSILON,
        )

        features[pct_column] = (
            features[diff_column] / denominator
        ).replace(
            [np.inf, -np.inf],
            0,
        ).fillna(0)

    if "Universidade" in features.columns:
        features = features.drop(
            columns=["Universidade"]
        )

    X_model = pd.DataFrame(
        index=features.index,
        columns=model_expected_features,
    )

    for feature in model_expected_features:
        if feature in features.columns:
            X_model[feature] = features[feature]
        else:
            X_model[feature] = 0.0

    for column in X_model.columns:
        X_model[column] = pd.to_numeric(
            X_model[column],
            errors="coerce",
        ).fillna(0)

    return X_model[
        model_expected_features
    ].reset_index(drop=True)


# ============================================================
# SIMULAÇÃO
# ============================================================

def simulate_full_ranking_avg_trend(
    df_base_edicao_6,
    model,
    ufpe_name,
    all_universities_average_trends,
    pct_change_ensino,
    pct_change_pesquisa,
    pct_change_mercado,
    pct_change_inovacao,
    pct_change_internacionalizacao,
    apply_other_uni_trends,
    model_expected_features=None,
):
    """
    Executa a simulação do ranking.
    """

    required_columns = [
        "Universidade",
        "Ranking",
        "Nota",
        *NOTA_COLS,
        *POSICAO_COLS,
    ]

    ensure_required_columns(
        df_base_edicao_6,
        required_columns,
        "df_base_edicao_6",
    )

    df_base_original = (
        df_base_edicao_6
        .copy()
        .reset_index(drop=True)
    )

    df_simulated = df_base_original.copy()

    # --------------------------------------------------------
    # Localiza a UFPE
    # --------------------------------------------------------

    ufpe_indices = df_simulated.index[
        df_simulated["Universidade"] == ufpe_name
    ].tolist()

    if not ufpe_indices:
        raise ValueError(
            f"A universidade '{ufpe_name}' não foi encontrada."
        )

    ufpe_index = ufpe_indices[0]

    # --------------------------------------------------------
    # Variações da UFPE
    # --------------------------------------------------------

    ufpe_changes = {
        "Nota em Ensino": pct_change_ensino,
        "Nota em Pesquisa": pct_change_pesquisa,
        "Nota em Mercado": pct_change_mercado,
        "Nota em Inovação": pct_change_inovacao,
        "Nota em Internacionalização": (
            pct_change_internacionalizacao
        ),
    }

    for column, percentage in ufpe_changes.items():
        value = pd.to_numeric(
            df_simulated.loc[
                ufpe_index,
                column,
            ],
            errors="coerce",
        )

        if pd.isna(value):
            value = 0.0

        df_simulated.loc[
            ufpe_index,
            column,
        ] = value * (
            1 + float(percentage)
        )

    # --------------------------------------------------------
    # Tendências das demais universidades
    # --------------------------------------------------------

    if (
        apply_other_uni_trends
        and all_universities_average_trends
    ):
        other_mask = (
            df_simulated["Universidade"] != ufpe_name
        )

        for trend_name, average_change in (
            all_universities_average_trends.items()
        ):
            suffix = "_pct_change_prev"

            if not trend_name.endswith(suffix):
                continue

            original_column = trend_name[
                :-len(suffix)
            ]

            if original_column not in df_simulated.columns:
                continue

            values = pd.to_numeric(
                df_simulated.loc[
                    other_mask,
                    original_column,
                ],
                errors="coerce",
            ).fillna(0)

            updated_values = values * (
                1 + float(average_change)
            )

            if original_column in RANKING_COLS:
                updated_values = (
                    updated_values
                    .round()
                    .clip(lower=1)
                    .astype(int)
                )

            df_simulated.loc[
                other_mask,
                original_column,
            ] = updated_values

    # --------------------------------------------------------
    # Recalcula notas
    # --------------------------------------------------------

    for column in NOTA_COLS:
        df_simulated[column] = pd.to_numeric(
            df_simulated[column],
            errors="coerce",
        ).fillna(0)

        df_simulated[column] = (
            df_simulated[column]
            .clip(lower=0, upper=100)
        )

    df_simulated["Nota"] = (
        df_simulated[NOTA_COLS]
        .mean(axis=1)
    )

    # --------------------------------------------------------
    # Recalcula posições
    # --------------------------------------------------------

    for nota_column, position_column in zip(
        NOTA_COLS,
        POSICAO_COLS,
    ):
        df_simulated[position_column] = (
            df_simulated[nota_column]
            .rank(
                ascending=False,
                method="min",
            )
            .astype(int)
        )

    # --------------------------------------------------------
    # Features do modelo
    # --------------------------------------------------------

    if model_expected_features is None:
        model_expected_features = (
            get_model_feature_names(model)
        )

    X_model = prepare_model_input(
        df_simulated=df_simulated,
        df_base=df_base_original,
        model_expected_features=model_expected_features,
    )

    # --------------------------------------------------------
    # Previsão
    # --------------------------------------------------------

    try:
        predictions = model.predict(X_model)

    except Exception as exc:
        raise RuntimeError(
            "Erro ao executar a previsão. Verifique se as "
            "features do modelo são compatíveis com a planilha."
        ) from exc

    predictions = np.asarray(
        predictions
    ).reshape(-1)

    if len(predictions) != len(df_simulated):
        raise ValueError(
            "O modelo retornou uma quantidade de previsões "
            "diferente da quantidade de universidades."
        )

    df_simulated["Model_Prediction"] = predictions

    df_simulated = (
        df_simulated
        .sort_values(
            "Model_Prediction",
            ascending=True,
        )
        .reset_index(drop=True)
    )

    df_simulated["Simulated_Ranking"] = (
        np.arange(len(df_simulated)) + 1
    )

    return df_simulated
