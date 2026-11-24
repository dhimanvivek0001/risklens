"""Turn approve/decline decisions into euros.

Used by every phase: the baseline rules now, the models later.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Economics:
    net_margin: float = 0.08
    lgd: float = 0.60

    @property
    def break_even_bad_rate(self) -> float:
        """Bad rate at which an approved group makes zero profit."""
        return self.net_margin / (self.net_margin + self.lgd)


def policy_profit(
    approve: pd.Series | np.ndarray,
    target: pd.Series | np.ndarray,
    loan_amount: pd.Series | np.ndarray,
    econ: Economics,
) -> dict[str, float]:
    """Expected profit of a policy on labelled applications.

    approve: 1 = approve, 0 = decline
    target:  1 = bad (payment difficulties), 0 = good
    """
    approve = np.asarray(approve, dtype=bool)
    target = np.asarray(target, dtype=int)
    amount = np.asarray(loan_amount, dtype=float)

    good_approved = approve & (target == 0)
    bad_approved = approve & (target == 1)

    profit = econ.net_margin * amount[good_approved].sum() - econ.lgd * amount[bad_approved].sum()
    n = len(target)
    n_approved = int(approve.sum())

    return {
        "applications": n,
        "approval_rate": n_approved / n if n else 0.0,
        "bad_rate_approved": float(target[approve].mean()) if n_approved else 0.0,
        "bads_declined_share": float((~approve & (target == 1)).sum() / max((target == 1).sum(), 1)),
        "total_profit": float(profit),
        "profit_per_10k_apps": float(profit / n * 10_000) if n else 0.0,
    }
