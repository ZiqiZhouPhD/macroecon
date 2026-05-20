# Monetary Economy Simulation

## Simulation Step Sequence

The following describes the sequence of events within each simulation step.

### 1. Preprocess

All within-step accumulators are zeroed out — wage income, consumption spending, production, labor transacted, profit, etc. This is bookkeeping so step-level tallies don't carry over.

### 2. Prices Update

The firm acts; the household has no price logic. The firm:

- Sets wage and goods price jointly using **Nelder-Mead** over the 2D space (wage, goods price). Each round, the firm records the (wage, price) pair it used and the resulting profit, and uses these observations to drive the simplex search — despite the economy being dynamic across rounds.
  - **Initialization (steps 0–2)**: the simplex is seeded with three moderately separated points: `(wage_init, price_init)`, `(wage_init * 1.2, price_init)`, `(wage_init, price_init * 1.2)`, evaluated on successive steps before the search begins. `wage_init` and `price_init` are set in the experiment and passed to the firm constructor.
  - **From step 3 onward**: standard Nelder-Mead iterations — reflect, expand, contract, or shrink the simplex based on observed profits.
  - Nelder-Mead may be implemented via an available package (e.g. `scipy.optimize.minimize` with `method='Nelder-Mead'`), managing the simplex state manually across steps rather than running to convergence in a single call.
- Computes **effective productivity**: baseline productivity scaled by a liquidity factor using the firm's cash balance at the end of the *previous* step — more firm cash → higher productivity (up to 1.25×), less cash → lower (down to 0.5×). This models financial frictions.

### 3. Volumes Update

The household reacts to the prices set in step 2. The firm does nothing in this stage.

- **Household** computes:
  - Real wage = nominal wage / goods price
  - **Labor supply**: determined first, via real-wage elasticity — higher real wage → more labor offered. This is the household's primary decision given the prices set in step 2.
  - **Desired consumption**: follows from the labor supply decision. Real income is computed from the chosen labor supply (wage × labor / goods price), and desired consumption is a weighted sum of that real income and a savings purchasing power adjustment. If the household's real cash holdings exceed its target, it spends more; if below, it cuts back. Desired consumption is capped so that the household cannot overspend into negative cash.

### 4. Labor Market Clears and Production

- The firm absorbs the entire labor supply set by the household in step 3. No rationing occurs.
- The household delivers labor and receives wages; the firm pays wages and receives labor. Both cash balances update immediately.
- Production is then computed: `production = labor_supply × effective_productivity`.

### 5. Goods Market Clears

- The household purchases its desired consumption volume (set in step 3), paying `goods_price × consumption`. Both cash balances update.
- **Profit** is the residual in real goods: `profit = production − consumption` (physical units). It exits the economy — there is no inventory. The firm's objective (targeted by Nelder-Mead in step 2) is to maximize this quantity.
- Profit is interpreted as being consumed by the firm's owner outside the model, or reinvested into the firm to sustain productivity — but this model does not track either effect explicitly.

### 6. Commit Prices

- `previous_price ← current price` for both markets.
- This is what both agents use in the next step to convert nominal cash to real values (e.g., real cash = `cash / previous_goods_price`).

## Key Asymmetry

The labor market does not ration — the firm absorbs all labor the household offers. The goods market is demand-determined — the household buys its desired consumption volume and the firm produces whatever that labor yields. The gap between production and consumption is profit, which exits the economy.

## Notes

**Inflation control**: Total cash in the economy is constant — money only flows between the household and the firm, never created or destroyed. This means inflation and deflation are self-correcting at the aggregate level: any rise in the price level erodes the real purchasing power of the fixed cash stock, which eventually dampens demand and pulls prices back.

**Household consumption demand**: The household's desired consumption is sensitive to the purchasing power of its savings. When the household holds more real cash than its target, it spends more; when its real cash falls below target, it cuts back. This makes consumption demand a function of both current income and the real value of accumulated savings.

**Firm cash drain**: To prevent the firm from accumulating cash indefinitely (which would saturate the liquidity-productivity factor), a dividend transfer is made each step from the firm to the household at a rate proportional to `log(firm_cash / household_cash)`. This is justified by two symmetric real-world pressures: when the household holds excess cash relative to the firm, it tends to invest that savings into the firm (capital flow inward); when the firm holds excess cash relative to the household, its owners withdraw dividends or distribute profits back to themselves as households (capital flow outward). The log ratio captures this pressure continuously and symmetrically, reversing direction depending on which side holds the relative surplus.
