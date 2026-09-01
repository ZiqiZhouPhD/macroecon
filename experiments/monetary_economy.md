# Monetary Economy Simulation

## Simulation Step Sequence

The following describes the sequence of events within each simulation step.

### 1. Preprocess

All within-step accumulators are zeroed out — wage income, consumption spending, production, labor transacted, profit, etc. This is bookkeeping so step-level tallies don't carry over.

### 2. Prices Update

The firm acts; the household has no price logic. The firm:

- Solves wage and goods price jointly against a **frozen beginning-of-step state**. Candidate evaluations are side-effect free and do not advance economic time.
  - It assumes expected goods-market clearing: `desired consumption = production`.
  - It maximizes **expected real operating profit**: `production − (wage / goods price) × labor`.
  - The first solve uses constrained SLSQP in log-price coordinates. Later steps solve market clearing and the constrained-profit first-order condition directly, using the previous optimum as the starting point.
  - The old one-evaluation-per-step tracker is still available as `price_optimization_mode = 'stepwise'`, but is not the monetary default.
- Does not impose a nominal self-financing constraint. Cash records the settlement that occurs after the pricing decision.
- Computes **effective productivity** from the firm's beginning-of-step cash valued at the candidate current goods price — more real firm cash raises productivity up to 1.25× baseline; less lowers it toward 0.5×.

### 3. Volumes Update

The household reacts to the prices set in step 2. The firm does nothing in this stage.

- **Household** computes:
  - Real wage = nominal wage / goods price
  - **Labor supply**: determined first, via real-wage elasticity — higher real wage → more labor offered. This is the household's primary decision given the prices set in step 2.
  - **Desired consumption**: follows from the labor supply decision. Real income is computed from the chosen labor supply (wage × labor / goods price), and desired consumption is a weighted sum of that real income and a savings purchasing power adjustment. Beginning-of-step cash is divided by the candidate current goods price, not the previous price. Market settlement enforces the nonnegative-cash constraint.

### 4. Labor Market Clears and Production

- The firm absorbs the entire labor supply set by the household in step 3. No rationing occurs.
- The household delivers labor and receives wages; the firm pays wages and receives labor. Both cash balances update immediately.
- Production is then computed: `production = labor_supply × effective_productivity`.

### 5. Goods Market Clears

- The household purchases its desired consumption volume (set in step 3), paying `goods_price × consumption`. Both cash balances update.
- **Real operating profit** is `production − (wage / goods price) × labor`, matching the firm's expected-clearing objective.
- **Nominal operating profit** is realized sales revenue minus the wage bill; it changes firm cash before dividends.
- `production − realized consumption` is an ex-post goods imbalance, not profit. There is no inventory, so any nonzero residual exits the modeled goods flow.

### 6. Commit Prices

- `previous_price ← current price` for both markets for historical bookkeeping. Current decisions use the current candidate price.

## Key Asymmetry

The labor market does not ration while the firm remains solvent — the firm absorbs all labor the household offers. The money market's affordability rule is a hard fallback at the cash boundary. The goods market settles the short side of desired consumption and production. On the default optimum branch these rates are equal to numerical precision.

## Notes

**Inflation control**: Total cash in the economy is constant — money only flows between the household and the firm, never created or destroyed. This means inflation and deflation are self-correcting at the aggregate level: any rise in the price level erodes the real purchasing power of the fixed cash stock, which eventually dampens demand and pulls prices back.

**Household consumption demand**: The household's desired consumption is sensitive to the purchasing power of its savings. When the household holds more real cash than its target, it spends more; when its real cash falls below target, it cuts back. This makes consumption demand a function of both current income and the real value of accumulated savings.

**Firm cash drain**: To prevent the firm from accumulating cash indefinitely (which would saturate the liquidity-productivity factor), a dividend transfer is made each step from the firm to the household at a rate proportional to `log(firm_cash / household_cash)`. This is justified by two symmetric real-world pressures: when the household holds excess cash relative to the firm, it tends to invest that savings into the firm (capital flow inward); when the firm holds excess cash relative to the household, its owners withdraw dividends or distribute profits back to themselves as households (capital flow outward). The log ratio captures this pressure continuously and symmetrically, reversing direction depending on which side holds the relative surplus.

**System class and continuity**: cash balances are differential states integrated as `rate × dt`; prices and behavioral rates are algebraic solutions at the current state. The model is therefore a piecewise-smooth differential-algebraic system, not a single unconstrained smooth ODE. On the default positive-cash interior branch the expected-clearing solution is continuous and time-step refinement converges. `min`/`max`, affordability, and configured price bounds remain nondifferentiable at regime boundaries.
