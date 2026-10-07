import pandas as pd


def scenarios(summary):
    rows = []
    for bps in [-200, -100, -50, 50, 100, 200]:
        dy = bps / 10000
        linear = -summary['Modified'] * dy
        quadratic = linear + .5 * summary['Convexity'] * dy**2
        rows.append({'Shock bps': bps, 'ΔP/P duration': linear, 'ΔP/P convexity': quadratic,
                     'ΔMV duration': summary['Market Value'] * linear,
                     'ΔMV convexity': summary['Market Value'] * quadratic})
    return pd.DataFrame(rows)
