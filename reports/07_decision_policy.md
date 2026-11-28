# 07 - Decision policy: calibration and profit cut-off

Economics: margin **8%** on good loans, loss **60%** on bad loans. Break-even bad rate = **11.76%**. Profit in dataset currency units.

## 1. Calibration (does predicted PD match reality?)

### valid

| PD group | Customers | Predicted PD | Actual bad rate |
| --- | --- | --- | --- |
| 1 | 6,151 | 1.41% | 1.41% |
| 2 | 6,150 | 2.21% | 2.10% |
| 3 | 6,150 | 2.95% | 2.68% |
| 4 | 6,150 | 3.77% | 4.05% |
| 5 | 6,150 | 4.79% | 5.01% |
| 6 | 6,150 | 6.11% | 6.31% |
| 7 | 6,150 | 7.92% | 7.97% |
| 8 | 6,150 | 10.63% | 10.85% |
| 9 | 6,150 | 15.05% | 15.09% |
| 10 | 6,151 | 26.01% | 25.26% |

Average calibration error: **0.21%**

### test

| PD group | Customers | Predicted PD | Actual bad rate |
| --- | --- | --- | --- |
| 1 | 6,151 | 1.42% | 1.50% |
| 2 | 6,150 | 2.21% | 2.44% |
| 3 | 6,150 | 2.94% | 2.93% |
| 4 | 6,150 | 3.77% | 3.98% |
| 5 | 6,150 | 4.82% | 4.52% |
| 6 | 6,150 | 6.16% | 6.28% |
| 7 | 6,150 | 8.00% | 8.59% |
| 8 | 6,150 | 10.68% | 10.50% |
| 9 | 6,150 | 15.14% | 14.76% |
| 10 | 6,151 | 26.06% | 25.23% |

Average calibration error: **0.29%**

## 2. Profit by cut-off (valid set)

| Cut-off | Approval rate | Bad rate of approved | Profit per 10k applications |
| --- | --- | --- | --- |
| 480 | 100.0% | 8.06% | 174,132,873 |
| 490 | 99.9% | 8.03% | 174,985,200 |
| 500 | 99.4% | 7.91% | 178,403,590 |
| 510 | 98.2% | 7.59% | 186,360,633 |
| 520 | 95.4% | 7.02% | 200,353,823 |
| 530 | 90.5% | 6.24% | 217,076,324 |
| 540 | 83.7% | 5.48% | 224,973,749 |
| 550 | 74.6% | 4.58% | 229,729,677 |
| 551 **<- chosen** | 73.5% | 4.46% | 230,404,615 |
| 560 | 63.7% | 3.82% | 218,071,978 |
| 570 | 50.7% | 3.11% | 193,414,387 |
| 580 | 36.9% | 2.41% | 154,300,220 |
| 590 | 23.5% | 1.77% | 105,832,892 |
| 600 | 12.3% | 1.48% | 57,705,271 |
| 610 | 4.9% | 1.20% | 24,037,893 |
| 620 | 1.1% | 1.59% | 5,493,747 |
| 630 | 0.1% | 2.17% | 378,911 |

- Best cut-off with no approval limit: **551** (approves 73.5%)
- Best cut-off approving at least 70%: **551** (approves 73.5%)

## 3. Final comparison on the test set

| Policy | Approval rate | Bad rate of approved | Bads caught | Profit per 10k applications |
| --- | --- | --- | --- | --- |
| Approve everyone | 100.0% | 8.07% | 0.0% | 174,522,929 |
| Phase 1 rules | 60.9% | 6.66% | 49.8% | 105,884,484 |
| Scorecard, cut-off 551 | 73.5% | 4.56% | 58.5% | 229,586,496 |
| PD below break-even | 78.3% | 4.94% | 52.1% | 230,459,362 |

Scorecard vs approve everyone: **+55,063,567** per 10k applications.
Scorecard vs Phase 1 rules: **+123,702,012** per 10k applications.
