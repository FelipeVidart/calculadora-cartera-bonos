"""ACT/365 fixed, annual effective rates. Nonnegative determined cash flows."""
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import logsumexp


def year_fractions(dates, valuation):
    return np.asarray((pd.DatetimeIndex(dates) - pd.Timestamp(valuation)).days, dtype=float) / 365.0


def xirr(market_value, times, flows):
    t, c = np.asarray(times, float), np.asarray(flows, float)
    if t.shape != c.shape or t.ndim != 1 or not len(t):
        raise ValueError('Fechas y flujos incompatibles')
    if not np.isfinite(market_value) or market_value <= 0 or not np.isfinite(t).all() or not np.isfinite(c).all() or (t <= 0).any() or (c < 0).any() or c.sum() <= 0:
        raise ValueError('Se requieren MV positivo, tiempos futuros y flujos no negativos')
    mask = c > 0
    def residual(z):
        return logsumexp(np.log(c[mask]) - t[mask] * z) - np.log(market_value)
    lo, hi = -1., 1.
    for _ in range(100):
        if residual(lo) >= 0 and residual(hi) <= 0:
            break
        lo *= 2; hi *= 2
    else:
        raise ValueError('No se pudo acotar la TIR')
    z = brentq(residual, lo, hi, xtol=1e-13)
    with np.errstate(over='ignore'):
        y = np.expm1(z)
    if not np.isfinite(y) or y <= -1:
        raise ValueError('TIR fuera del rango numérico representable')
    return float(y)


def metrics(market_value, times, income, principal):
    t = np.asarray(times, float)
    r, a = np.asarray(income, float), np.asarray(principal, float)
    if (r < 0).any() or (a < 0).any():
        raise ValueError('Renta y amortización deben ser no negativas')
    c = r + a
    y = xirr(market_value, t, c)
    pv = c * np.exp(-t * np.log1p(y))
    macaulay = np.dot(t, pv) / market_value
    return dict(TIR=y, Macaulay=macaulay, Modified=macaulay / (1+y),
                Convexity=np.dot(t*(t+1), pv) / (market_value*(1+y)**2),
                WAL=np.dot(t, a)/a.sum() if a.sum() else np.nan,
                Renta=r.sum(), Amortización=a.sum(), Flujos=c.sum())
