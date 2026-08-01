# model_logic.py

from __future__ import annotations

import os
from typing import Dict, Iterable, Optional

import joblib
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURAÇÕES
# ============================================================

UFPE_EXACT_NAME = "Universidade Federal de Pernambuco"

# Mantém compatibilidade com o app.py
ufpe_exact_name = UFPE_EXACT_NAME
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

RANKING_COLS = ["Ranking"] + POSICAO_COLS

# Mapeamento explícito para evitar problemas com acentos
SLIDER_TO_NOTA = {
    "pct_change_ensino": "Nota em Ensino",
    "pct_change_pesquisa": "Nota em Pesquisa",
    "pct_change_mercado": "Nota em Mercado",
    "pct_change_inovacao": "Nota em Inovação",
    "pct_change_internacionalizacao": "Nota em Internacionalização",
}

EPSILON = 1e-6


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def get_year_from_edition(edition_number: int):
    """
    Retorna o ano associado à edição RUF.
    """
    return EDITION_YEAR_MAP.get(
        int(edition_number),
        f"Ano Desconhecido (Edição {edition_number})",
    )


def _ensure_required_columns(
    df: pd.DataFrame,
    required_columns: Iterable[str],
    dataframe_name: str = "DataFrame",
) -> None:
    """
    Verifica se as colunas essenciais existem.
    """
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(
            f"{dataframe_name} não possui as seguintes colunas obrigatórias: "
            f"{missing}"
        )


def _to_numeric_columns(
    df: pd.DataFrame,
    columns: Iterable[str],
) -> pd.DataFrame:
    """
    Converte as colunas existentes para valores numéricos.
    """
    result = df.copy()

    for col in columns:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce")

    return result


def _get_model_feature_names(model) -> list[str]:
    """
    Obtém os nomes das features esperadas pelo modelo.

    O XGBoost normalmente disponibiliza os nomes em:
    model.get_booster().feature_names
    """
    feature_names = None

    try:
        booster = model.get_booster()
        feature_names = booster.feature_names
    except Exception:
        feature_names = None

    if not feature_names:
        feature_names = getattr(model, "feature_names_in_", None)

    if feature_names is None:
        raise ValueError(
            "Não foi possível obter os nomes das features esperadas pelo modelo. "
            "Verifique se o modelo foi treinado com um DataFrame contendo nomes "
            "de colunas."
        )

    return list(feature_names)


def _prepare_model_input(
    df_simulated: pd.DataFrame,
    df_base: pd.DataFrame,
    model_expected_features: list[str],
) -> pd.DataFrame:
    """
    Prepara o DataFrame de entrada do modelo.

    A função:

    1. Mantém as colunas originais disponíveis;
    2. Calcula features de diferença em relação à edição anterior;
    3. Calcula features de variação percentual;
    4. Alinha exatamente as colunas esperadas pelo modelo;
    5. Mantém a ordem original das features;
    6. Preenche features ausentes com zero.
    """

    _ensure_required_columns(
        df_simulated,
        ["Universidade"],
        "df_simulated",
    )

    _ensure_required_columns(
        df_base,
        ["Universidade"],
        "df_base",
    )

    simulated = df_simulated.copy()
    base = df_base.copy()

    # Ordenação determinística por universidade
    simulated = simulated.sort_values("Universidade").reset_index(drop=True)
    base = base.sort_values("Universidade").reset_index(drop=True)

    # Índice para fazer o alinhamento correto pela universidade
    simulated_by_uni = simulated.set_index("Universidade")
    base_by_uni = base.set_index("Universidade")

    common_universities = simulated_by_uni.index

    base_aligned = base_by_uni.reindex(common_universities)
    simulated_aligned = simulated_by_uni.reindex(common_universities)

    # DataFrame com todas as possíveis features
    feature_frame = simulated_aligned.copy()

    # Features utilizadas nas diferenças entre edições
    columns_for_trends = (
        NOTA_COLS
        + POSICAO_COLS
        + ["Nota", "Ranking"]
    )

    for col in columns_for_trends:
        if col not in simulated_aligned.columns:
            continue

        if col not in base_aligned.columns:
            continue

        current_values = pd.to_numeric(
            simulated_aligned[col],
            errors="coerce",
        ).fillna(0)

        previous_values = pd.to_numeric(
            base_aligned[col],
            errors="coerce",
        ).fillna(0)

        diff_col = f"{col}_diff_prev"
        pct_col = f"{col}_pct_change_prev"

        feature_frame[diff_col] = current_values - previous_values

        denominator = previous_values.copy()
        denominator = denominator.replace(0, EPSILON)

        feature_frame[pct_col] = (
            feature_frame[diff_col] / denominator
        ).replace([np.inf, -np.inf], 0).fillna(0)

    # Remove a coluna textual usada apenas para alinhamento
    if "Universidade" in feature_frame.columns:
        feature_frame = feature_frame.drop(columns=["Universidade"])

    # Cria o DataFrame final exatamente com as colunas do treinamento
    X_model = pd.DataFrame(
        index=feature_frame.index,
        columns=model_expected_features,
    )

    missing_features = []

    for feature in model_expected_features:
        if feature in feature_frame.columns:
            X_model[feature] = feature_frame[feature]
        else:
            # Para features ausentes, zero é apropriado principalmente
            # para variáveis one-hot. Deve ser validado contra o treinamento.
            X_model[feature] = 0.0
            missing_features.append(feature)

    # Converte todas as features para numérico
    for col in X_model.columns:
        X_model[col] = pd.to_numeric(
            X_model[col],
            errors="coerce",
        ).fillna(0)

    X_model = X_model[model_expected_features]

    if missing_features:
        print(
            "MODEL_LOGIC_WARNING: "
            f"{len(missing_features)} features esperadas pelo modelo "
            "não foram encontradas nos dados e foram preenchidas com zero."
        )
        print(
            "MODEL_LOGIC_WARNING: Features ausentes: "
            f"{missing_features}"
        )

    return X_model.reset_index(drop=True)


# ============================================================
# CARREGAMENTO
# ============================================================

def load_model(path: str):
    """
    Carrega o modelo de Machine Learning.
    """
    print(f"MODEL_LOGIC_DEBUG: Tentando carregar modelo de: {path}")

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Arquivo do modelo não encontrado: {path}"
        )

    try:
        model = joblib.load(path)

        print(
            "MODEL_LOGIC_DEBUG: Modelo carregado com sucesso: "
            f"{os.path.basename(path)}"
        )

        return model

    except Exception as exc:
        raise RuntimeError(
            f"Erro ao carregar o modelo '{path}': {exc}"
        ) from exc


def load_data(path: str) -> pd.DataFrame:
    """
    Carrega os dados consolidados do arquivo Excel.
    """
    print(f"MODEL_LOGIC_DEBUG: Tentando carregar dados de: {path}")

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Arquivo de dados não encontrado: {path}"
        )

    try:
        df = pd.read_excel(path)

        if df.empty:
            raise ValueError(
                "O arquivo Excel foi carregado, mas está vazio."
            )

        required_columns = [
            "Edicao_RUF",
            "Universidade",
            "Ranking",
            "Nota",
            *NOTA_COLS,
            *POSICAO_COLS,
        ]

        _ensure_required_columns(
            df,
            required_columns,
            "Arquivo Excel",
        )

        print(
            "MODEL_LOGIC_DEBUG: Dados carregados com sucesso. "
            f"Linhas: {len(df)} | Colunas: {len(df.columns)}"
        )

        return df

    except Exception as exc:
        raise RuntimeError(
            f"Erro ao carregar os dados '{path}': {exc}"
        ) from exc


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

    A UFPE é excluída do cálculo para evitar que a tendência média
    das outras instituições seja influenciada pela própria UFPE.
    """

    print(
        "MODEL_LOGIC_DEBUG: Iniciando cálculo das tendências médias."
    )

    _ensure_required_columns(
        df_full_data,
        ["Universidade", "Edicao_RUF"],
        "df_full_data",
    )

    df = df_full_data.copy()

    df = df[df["Universidade"] != ufpe_name].copy()

    trend_columns = [
        "Ranking",
        "Nota",
        *NOTA_COLS,
        *POSICAO_COLS,
    ]

    available_columns = [
        col for col in trend_columns if col in df.columns
    ]

    df = _to_numeric_columns(df, available_columns)

    df = df.sort_values(
        by=["Universidade", "Edicao_RUF"]
    ).reset_index(drop=True)

    grouped = df.groupby("Universidade", sort=False)

    trends: Dict[str, float] = {}

    for col in available_columns:
        previous = grouped[col].shift(1)
        current = df[col]

        valid_previous = previous.notna()
        denominator = previous.copy()

        # Evita divisão por zero sem transformar todos os resultados em NaN
        denominator = denominator.replace(0, EPSILON)

        pct_change = (
            (current - previous) / denominator
        ).replace([np.inf, -np.inf], np.nan)

        pct_change = pct_change[
            valid_previous & pct_change.notna()
        ]

        average_change = float(pct_change.mean()) if not pct_change.empty else 0.0

        trends[f"{col}_pct_change_prev"] = average_change

    print(
        "MODEL_LOGIC_DEBUG: Tendências médias calculadas: "
        f"{len(trends)} variáveis."
    )

    return trends


# ============================================================
# SIMULAÇÃO
# ============================================================

def simulate_full_ranking_avg_trend(
    df_base_edicao_6: pd.DataFrame,
    model,
    ufpe_name: str,
    all_universities_average_trends: Dict[str, float],
    pct_change_ensino: float,
    pct_change_pesquisa: float,
    pct_change_mercado: float,
    pct_change_inovacao: float,
    pct_change_internacionalizacao: float,
    apply_other_uni_trends: bool,
    model_expected_features: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Simula as notas da UFPE e, opcionalmente, aplica as tendências médias
    às demais universidades.

    O modelo prevê um ranking bruto. Em seguida, os resultados são
    ordenados e transformados em posições consecutivas.
    """

    print(
        "MODEL_LOGIC_DEBUG: Iniciando simulação do ranking."
    )

    _ensure_required_columns(
        df_base_edicao_6,
        [
            "Universidade",
            "Ranking",
            "Nota",
            *NOTA_COLS,
            *POSICAO_COLS,
        ],
        "df_base_edicao_6",
    )

    df_base_original = df_base_edicao_6.copy()
    df_simulated = df_base_edicao_6.copy()

    # --------------------------------------------------------
    # Localiza a UFPE
    # --------------------------------------------------------

    ufpe_indices = df_simulated.index[
        df_simulated["Universidade"] == ufpe_name
    ].tolist()

    if not ufpe_indices:
        raise ValueError(
            f"A universidade '{ufpe_name}' não foi encontrada "
            "na edição base."
        )

    ufpe_index = ufpe_indices[0]

    # --------------------------------------------------------
    # Aplica as variações da UFPE
    # --------------------------------------------------------

    slider_values = {
        "Nota em Ensino": pct_change_ensino,
        "Nota em Pesquisa": pct_change_pesquisa,
        "Nota em Mercado": pct_change_mercado,
        "Nota em Inovação": pct_change_inovacao,
        "Nota em Internacionalização": pct_change_internacionalizacao,
    }

    for nota_col, pct_change in slider_values.items():
        value = pd.to_numeric(
            df_simulated.loc[ufpe_index, nota_col],
            errors="coerce",
        )

        if pd.isna(value):
            value = 0.0

        df_simulated.loc[ufpe_index, nota_col] = (
            value * (1.0 + float(pct_change))
        )

    print(
        "MODEL_LOGIC_DEBUG: Variações da UFPE aplicadas."
    )

    # --------------------------------------------------------
    # Aplica as tendências médias às demais universidades
    # --------------------------------------------------------

    if apply_other_uni_trends and all_universities_average_trends:

        other_mask = df_simulated["Universidade"] != ufpe_name

        for trend_key, average_change in (
            all_universities_average_trends.items()
        ):
            suffix = "_pct_change_prev"

            if not trend_key.endswith(suffix):
                continue

            original_col = trend_key[:-len(suffix)]

            if original_col not in df_simulated.columns:
                continue

            avg_change = float(average_change)

            numeric_values = pd.to_numeric(
                df_simulated.loc[other_mask, original_col],
                errors="coerce",
            )

            numeric_values = numeric_values.fillna(0)

            updated_values = numeric_values * (1.0 + avg_change)

            if original_col in RANKING_COLS:
                updated_values = (
                    updated_values
                    .round()
                    .clip(lower=1)
                    .astype(int)
                )

            df_simulated.loc[
                other_mask,
                original_col,
            ] = updated_values

        print(
            "MODEL_LOGIC_DEBUG: Tendências médias aplicadas "
            "às demais universidades."
        )

    # --------------------------------------------------------
    # Recalcula notas e posições
    # --------------------------------------------------------

    for nota_col in NOTA_COLS:
        df_simulated[nota_col] = pd.to_numeric(
            df_simulated[nota_col],
            errors="coerce",
        ).fillna(0)

        # Limita as notas ao intervalo usual de 0 a 100
        df_simulated[nota_col] = df_simulated[nota_col].clip(0, 100)

    # Nota geral como média das cinco dimensões
    df_simulated["Nota"] = df_simulated[NOTA_COLS].mean(axis=1)

    # Recalcula as posições de cada dimensão
    for nota_col, posicao_col in zip(NOTA_COLS, POSICAO_COLS):
        df_simulated[posicao_col] = (
            df_simulated[nota_col]
            .rank(
                ascending=False,
                method="min",
            )
            .astype(int)
        )

    print(
        "MODEL_LOGIC_DEBUG: Notas e posições recalculadas."
    )

    # --------------------------------------------------------
    # Obtém as features esperadas pelo modelo
    # --------------------------------------------------------

    if model_expected_features is None:
        model_expected_features = _get_model_feature_names(model)

    if not model_expected_features:
        raise ValueError(
            "A lista de features esperadas pelo modelo está vazia."
        )

    # --------------------------------------------------------
    # Prepara os dados para previsão
    # --------------------------------------------------------

    X_model = _prepare_model_input(
        df_simulated=df_simulated,
        df_base=df_base_original,
        model_expected_features=model_expected_features,
    )

    print(
        "MODEL_LOGIC_DEBUG: Dados preparados para o modelo. "
        f"Linhas: {len(X_model)} | "
        f"Features: {len(X_model.columns)}"
    )

    # --------------------------------------------------------
    # Previsão
    # --------------------------------------------------------

    try:
        predicted_values = model.predict(X_model)

    except Exception as exc:
        raise RuntimeError(
            "Erro durante a previsão do modelo. "
            "Verifique se as features do arquivo Excel são compatíveis "
            "com as features usadas durante o treinamento."
        ) from exc

    predicted_values = np.asarray(predicted_values).reshape(-1)

    if len(predicted_values) != len(df_simulated):
        raise ValueError(
            "O modelo retornou uma quantidade de previsões diferente "
            "da quantidade de universidades."
        )

    # O valor previsto pelo modelo é usado apenas para ordenar
    df_simulated["Model_Prediction"] = predicted_values

    df_simulated = df_simulated.sort_values(
        by="Model_Prediction",
        ascending=True,
    ).reset_index(drop=True)

    # Ranking final consecutivo
    df_simulated["Simulated_Ranking"] = (
        np.arange(len(df_simulated)) + 1
    )

    print(
        "MODEL_LOGIC_DEBUG: Simulação finalizada."
    )

    return df_simulated
