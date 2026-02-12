#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D-Tagatose Production - Route A vs Route B Comparison

Route A: Purified D-Galactose (Step 3-7)
Route B: Red Algae Biomass + Step 2.5 (Step 1-7)

Author: Claude AI
Date: 2026-02-12
"""

import sys
import io

# Set stdout to UTF-8 encoding to handle special characters on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, r'C:\Users\Jahyun\PycharmProjects\biosteam')

from biosteam.units.tagatose_route_economics import RouteAEconomics, RouteBEconomics

# ============================================================================
# 1. Initialize Routes
# ============================================================================

print("=" * 90)
print("D-TAGATOSE PRODUCTION - ROUTE A vs ROUTE B ECONOMIC COMPARISON")
print("=" * 90)

route_a = RouteAEconomics()
route_b = RouteBEconomics()

print("\nRoute A: " + route_a.route_name)
print("Route B: " + route_b.route_name)

# ============================================================================
# 2. Production Summary
# ============================================================================

print("\n" + "=" * 90)
print("[1] PRODUCTION SUMMARY")
print("=" * 90)

summary_a = route_a.get_production_summary()
summary_b = route_b.get_production_summary()

print("\nRoute A (Purified D-Galactose):")
for key, value in summary_a.items():
    if key != 'route':
        print(f"  {key:<30} {value}")

print("\nRoute B (Red Algae + Step 2.5):")
for key, value in summary_b.items():
    if key != 'route':
        print(f"  {key:<30} {value}")

# ============================================================================
# 3. CAPEX Comparison
# ============================================================================

print("\n" + "=" * 90)
print("[2] CAPITAL EXPENDITURE (CAPEX) COMPARISON")
print("=" * 90)

capex_a = route_a.calculate_capex()
capex_b = route_b.calculate_capex()

print("\nRoute A CAPEX:")
for key, value in capex_a.items():
    print(f"  {key:<35} ${value:>12,.0f}")

print("\nRoute B CAPEX:")
for key, value in capex_b.items():
    print(f"  {key:<35} ${value:>12,.0f}")

capex_diff = capex_b['Total CAPEX'] - capex_a['Total CAPEX']
capex_diff_pct = capex_diff/capex_a['Total CAPEX']*100
sign = '+' if capex_diff_pct > 0 else ''
print("\nCapex Difference (B - A):        ${:>12,.0f}  ({}{}%)".format(
    int(capex_diff), sign, round(capex_diff_pct, 1)))

# ============================================================================
# 4. OPEX Detail Comparison
# ============================================================================

print("\n" + "=" * 90)
print("[3] OPERATING EXPENDITURE (OPEX) - ANNUAL DETAIL")
print("=" * 90)

opex_a = route_a.calculate_opex_annual()
opex_b = route_b.calculate_opex_annual()

total_opex_a = opex_a['Total Annual OPEX']
total_opex_b = opex_b['Total Annual OPEX']

print("\nRoute A OPEX Detail:")
for key, value in sorted(opex_a.items()):
    if key != 'Total Annual OPEX':
        pct = value / total_opex_a * 100 if total_opex_a > 0 else 0
        print(f"  {key:<40} ${value:>12,.0f}  ({pct:>5.1f}%)")
print(f"\n  {'TOTAL ANNUAL OPEX':<40} ${total_opex_a:>12,.0f}  (100.0%)")

print("\nRoute B OPEX Detail:")
for key, value in sorted(opex_b.items()):
    if key != 'Total Annual OPEX':
        pct = value / total_opex_b * 100 if total_opex_b > 0 else 0
        print(f"  {key:<40} ${value:>12,.0f}  ({pct:>5.1f}%)")
print(f"\n  {'TOTAL ANNUAL OPEX':<40} ${total_opex_b:>12,.0f}  (100.0%)")

opex_diff = total_opex_b - total_opex_a
opex_diff_pct = (total_opex_b - total_opex_a) / total_opex_a * 100
sign = '+' if opex_diff_pct > 0 else ''
print("\nOPEX Difference (B - A):             ${:>12,.0f}  ({}{}%)".format(
    int(opex_diff), sign, round(opex_diff_pct, 1)))

# ============================================================================
# 5. Revenue Comparison
# ============================================================================

print("\n" + "=" * 90)
print("[4] REVENUE COMPARISON")
print("=" * 90)

revenue_a = route_a.calculate_revenue_annual()
revenue_b = route_b.calculate_revenue_annual()

print("\nMetric                                   Route A            Route B")
print("-" * 75)
print("Annual Production (kg)                   {:>14,.0f}     {:>14,.0f}".format(
    revenue_a['Annual Tagatose (kg)'], revenue_b['Annual Tagatose (kg)']))
print("Price ($/kg)                             {:>14.2f}     {:>14.2f}".format(
    revenue_a['Dry Powder Price ($/kg)'], revenue_b['Dry Powder Price ($/kg)']))
print("Annual Revenue ($)                       ${:>13,.0f}    ${:>13,.0f}".format(
    revenue_a['Total Annual Revenue ($)'], revenue_b['Total Annual Revenue ($)']))

prod_diff = revenue_b['Annual Tagatose (kg)'] - revenue_a['Annual Tagatose (kg)']
prod_diff_pct = prod_diff / revenue_a['Annual Tagatose (kg)'] * 100
sign = '+' if prod_diff_pct > 0 else ''
print("\nProduction Difference (B - A):          {:>14,.0f} kg  ({}{}%)".format(
    int(prod_diff), sign, round(prod_diff_pct, 1)))

revenue_diff = revenue_b['Total Annual Revenue ($)'] - revenue_a['Total Annual Revenue ($)']
revenue_diff_pct = revenue_diff / revenue_a['Total Annual Revenue ($)'] * 100
sign = '+' if revenue_diff_pct > 0 else ''
print("Revenue Difference (B - A):             ${:>13,.0f}  ({}{}%)".format(
    int(revenue_diff), sign, round(revenue_diff_pct, 1)))

# ============================================================================
# 6. Profitability Analysis
# ============================================================================

print("\n" + "=" * 90)
print("[5] PROFITABILITY ANALYSIS")
print("=" * 90)

profit_a = route_a.calculate_profitability()
profit_b = route_b.calculate_profitability()

print("\nMetric                                   Route A            Route B        Diff")
print("-" * 80)
print("CAPEX ($)                                ${:>13,.0f}    ${:>13,.0f}".format(
    int(profit_a['CAPEX ($)']), int(profit_b['CAPEX ($)'])))
print("Annual OPEX ($)                          ${:>13,.0f}    ${:>13,.0f}".format(
    int(profit_a['Annual OPEX ($)']), int(profit_b['Annual OPEX ($)'])))
print("Annual Revenue ($)                       ${:>13,.0f}    ${:>13,.0f}".format(
    int(profit_a['Annual Revenue ($)']), int(profit_b['Annual Revenue ($)'])))
print("Annual Profit ($)                        ${:>13,.0f}    ${:>13,.0f}".format(
    int(profit_a['Annual Profit ($)']), int(profit_b['Annual Profit ($)'])))
print("ROI (%)                                  {:>14.1f}    {:>14.1f}".format(
    profit_a['ROI (Annual %)'], profit_b['ROI (Annual %)']))
print("Payback Period (years)                   {:>14.2f}    {:>14.2f}".format(
    profit_a['Payback Period (years)'], profit_b['Payback Period (years)']))
print("Break-even Price ($/kg)                  {:>14.2f}    {:>14.2f}".format(
    profit_a['Break-even Price ($/kg)'], profit_b['Break-even Price ($/kg)']))

# ============================================================================
# 7. Unit Cost Analysis
# ============================================================================

print("\n" + "=" * 90)
print("[6] UNIT COST ANALYSIS ($/kg) - KEY METRIC")
print("=" * 90)

opex_per_kg_a = total_opex_a / revenue_a['Annual Tagatose (kg)']
opex_per_kg_b = total_opex_b / revenue_b['Annual Tagatose (kg)']

capex_annualized_a = capex_a['Total CAPEX'] / 20  # 20-year amortization
capex_annualized_b = capex_b['Total CAPEX'] / 20

capex_per_kg_a = capex_annualized_a / revenue_a['Annual Tagatose (kg)']
capex_per_kg_b = capex_annualized_b / revenue_b['Annual Tagatose (kg)']

total_cost_per_kg_a = opex_per_kg_a + capex_per_kg_a
total_cost_per_kg_b = opex_per_kg_b + capex_per_kg_b

print("\nMetric                                   Route A            Route B        Diff")
print("-" * 80)
print("OPEX per kg                              {:>14.2f}    {:>14.2f}    {:>8.2f}".format(
    opex_per_kg_a, opex_per_kg_b, opex_per_kg_b - opex_per_kg_a))
print("CAPEX annualized per kg                  {:>14.2f}    {:>14.2f}    {:>8.2f}".format(
    capex_per_kg_a, capex_per_kg_b, capex_per_kg_b - capex_per_kg_a))
print("TOTAL (OPEX + CAPEX annualized)          {:>14.2f}    {:>14.2f}    {:>8.2f}".format(
    total_cost_per_kg_a, total_cost_per_kg_b, total_cost_per_kg_b - total_cost_per_kg_a))

print("\nBreakeven Price (OPEX only):             {:>14.2f}    {:>14.2f}    {:>8.2f}".format(
    profit_a['Break-even Price ($/kg)'], profit_b['Break-even Price ($/kg)'],
    profit_b['Break-even Price ($/kg)'] - profit_a['Break-even Price ($/kg)']))

# ============================================================================
# 8. Market Price Sensitivity
# ============================================================================

print("\n" + "=" * 90)
print("[7] MARKET PRICE SENSITIVITY")
print("=" * 90)

prices = [10.0, 12.0, 14.0, 15.0, 16.0, 17.0]

print("\nPrice ($/kg)    Route A Profit    Route B Profit    Better Route")
print("-" * 65)

for price in prices:
    route_a.tagatose_price = price
    route_b.tagatose_price = price

    profit_a_val = route_a.calculate_profitability()['Annual Profit ($)']
    profit_b_val = route_b.calculate_profitability()['Annual Profit ($)']

    diff = profit_a_val - profit_b_val
    better = "Route A" if diff > 0 else "Route B"

    print("   ${:<5.1f}        ${:>13,.0f}    ${:>13,.0f}    {}".format(
        price, int(profit_a_val), int(profit_b_val), better))

# Reset to market price
route_a.tagatose_price = 10.0
route_b.tagatose_price = 10.0

# ============================================================================
# 9. Conclusion
# ============================================================================

print("\n" + "=" * 90)
print("[8] CONCLUSION & RECOMMENDATIONS")
print("=" * 90)

print("\nRoute A (Purified D-Galactose) - RECOMMENDED:")
print("  o Higher production: {:.0f} kg/year".format(revenue_a['Annual Tagatose (kg)']))
print("  o Lower unit cost: ${:.2f}/kg (OPEX+CAPEX)".format(total_cost_per_kg_a))
print("  o Better breakeven: ${:.2f}/kg".format(profit_a['Break-even Price ($/kg)']))
print("  o Simpler process: Step 3-7 only (no upstream hydrolysis)")
print("  o Better economics at commodity prices ($10-12/kg)")

print("\nRoute B (Red Algae + Step 2.5) - FUTURE OPTION:")
print("  - Lower production: {:.0f} kg/year (-17.9%)".format(revenue_b['Annual Tagatose (kg)']))
print("  - Higher unit cost: ${:.2f}/kg".format(total_cost_per_kg_b))
print("  - Worse breakeven: ${:.2f}/kg".format(profit_b['Break-even Price ($/kg)']))
print("  o Lower feedstock cost: $0.75/kg (vs $2.00/kg)")
print("  - Consider if raw algae access improves Step 1-2 economics")

print("\nCurrent Market Context:")
print("  - Market Price: $10/kg (commodity baseline)")
print("  - Premium Market: $15-16/kg (pharmaceutical/specialty)")
print("  - Route A breakeven: ${:.2f}/kg".format(profit_a['Break-even Price ($/kg)']))

margin_pct = (15.0 - profit_a['Break-even Price ($/kg)']) / profit_a['Break-even Price ($/kg)'] * 100
print("  - Margin to premium market: {:.1f}% safety margin".format(margin_pct))

print("\nSTRATEGY:")
print("  1. Focus on Route A for baseline production")
print("  2. Pursue premium market ($15-16/kg) for profitability")
print("  3. Re-evaluate Route B if:")
print("     - Algae biomass cost drops to $0.50/kg or lower")
print("     - OR Step 1-2 efficiency improves significantly")
print("     - OR for integrated operations with algae cultivation")

print("\n" + "=" * 90)
print("END OF ANALYSIS")
print("=" * 90)
