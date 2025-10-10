import numpy as np
import pandas as pd

def calculate_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily log returns from a DataFrame of price data.

    Args:
        prices (pd.DataFrame): DataFrame of asset prices (index: date, columns: tickers)

    Returns:
        pd.DataFrame: DataFrame of log returns
    """
    log_returns = np.log(prices / prices.shift(1))
    return log_returns.dropna(how='all')

def calculate_sharpe_ratio(returns: pd.DataFrame, risk_free_rate: float = 0.0, annualization_factor: int = 252) -> pd.Series:
    """
    Calculate the annualized Sharpe ratio for each asset.

    Args:
        returns (pd.DataFrame): DataFrame of daily returns (can be log or simple returns)
        risk_free_rate (float): Daily risk-free rate (default: 0.0)
        annualization_factor (int): Number of trading days in a year (default: 252)

    Returns:
        pd.Series: Sharpe ratio for each asset
    """
    excess_returns = returns - risk_free_rate
    mean_excess_return = excess_returns.mean()
    std_excess_return = excess_returns.std()
    sharpe_ratios = (mean_excess_return / std_excess_return) * np.sqrt(annualization_factor)
    return sharpe_ratios

def calculate_max_drawdown(prices: pd.DataFrame) -> pd.Series:
    """
    Calculate the maximum drawdown for each asset.

    Args:
        prices (pd.DataFrame): DataFrame of price data

    Returns:
        pd.Series: Maximum drawdown values for each asset
    """
    drawdowns = (prices / prices.cummax()) - 1
    max_drawdown = drawdowns.min()
    return max_drawdown

def calculate_cumulative_returns(prices: pd.DataFrame, base: float = 100.0) -> pd.DataFrame:
    """
    Calculate cumulative returns indexed to a starting base (e.g., 100).

    Args:
        prices (pd.DataFrame): DataFrame of price data
        base (float): Starting index value (default: 100)

    Returns:
        pd.DataFrame: DataFrame of cumulative returns indexed to base
    """
    cumulative_returns = prices / prices.iloc[0] * base
    return cumulative_returns