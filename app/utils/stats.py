from datetime import timedelta

import pandas as pd


def duration(df: pd.DataFrame) -> timedelta:
    """
    所要時間
    """
    return df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]


def average_climb_rate(df: pd.DataFrame) -> float:
    """
    フライト通しての平均上昇率
    """
    df_ = df.copy()
    df_["group"] = df_["circling"].diff().ne(0).cumsum()
    df_ = df_[df_["circling"].eq(1)]

    if df_.empty:
        return 0

    df_agg = (
        df_.groupby("group")[["timestamp", "altitude"]]
        .apply(lambda x: x.iloc[-1] - x.iloc[0])
        .sum()
    )

    duration = df_agg["timestamp"].total_seconds()
    total_gain = df_agg["altitude"]

    return total_gain / duration
