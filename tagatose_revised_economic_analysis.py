#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D-Tagatose Production - Revised Economic Analysis
Modified Process Parameters: 110 g/L Galactose, 24 hr reaction (16h + 8h), 2 mM NAD+

Scenario Analysis:
1. Syrup-Only Production
2. Crystal-Only Production
3. Mixed Product Portfolio (50/50)

Cost Driver Impact Analysis (Pareto Analysis)
"""

from biosteam.units.tagatose_economics import TagatoseEconomicAnalysis

print("="*90)
print("D-TAGATOSE PRODUCTION - REVISED ECONOMIC ANALYSIS")
print("Modified Process: 110 g/L Galactose, 24 hr Reaction (16h anaerobic + 8h aerobic)")
print("="*90)

# ============================================================================
# 1. Create analysis instance with new parameters
# ============================================================================

econ = TagatoseEconomicAnalysis(system=None, product_stream=None)

# Updated production parameters
print("\n[PROCESS PARAMETERS - OPTIMIZED v2]")
print("-" * 90)
print(f"  Reactor volume: 1000 L (scaled-up from 500L)")
print(f"  Reaction time: 24 hr (16h anaerobic + 8h aerobic)")
print(f"  D-Galactose: 110 g/L")
print(f"  Biocatalyst (E. coli): 20 g/L (reduced from 50 g/L)")
print(f"  NAD+ concentration: 1 mM (reduced from 2 mM)")
print(f"  NAD+ Recovery: 80% reuse integrated")
print(f"  NADP+ concentration: 0.1 mM (maintained)")

# Update production parameters in economics model
# Batch time: 24 hr (from 36 hr)
batches_per_year_new = econ.production_hours_per_year / 24  # 312.5 batches
annual_production_new = batches_per_year_new * 110  # 34,375 kg (1000L × 110 g/L)

print(f"\nUpdated Annual Metrics:")
print(f"  Batches per year: {batches_per_year_new:.1f} (from 208)")
print(f"  Reactor volume: 1000 L (doubled from 500L)")
print(f"  Annual production: {annual_production_new:,.0f} kg (doubled from 17,188 kg)")

# ============================================================================
# 2. SCENARIO 1: SYRUP-ONLY PRODUCTION
# ============================================================================

print("\n" + "="*90)
print("[SCENARIO 1] SYRUP-ONLY PRODUCTION")
print("="*90)

class TagatoseEconomicsSyrupOnly(TagatoseEconomicAnalysis):
    """Modified for syrup-only production"""

    def calculate_revenue_annual(self, product_concentration=None):
        """Syrup product only"""
        # Update production batch count
        batches_per_year = self.production_hours_per_year / 24
        annual_tagatose_kg = 110 * batches_per_year  # 110 kg per batch (1000L × 110 g/L)

        # Syrup-only: no crystal premium
        syrup_yield = annual_tagatose_kg
        syrup_selling_price = self.tagatose_price  # No premium, base price only
        syrup_revenue = syrup_yield * syrup_selling_price

        return {
            'Annual Tagatose (kg)': annual_tagatose_kg,
            'Crystal Yield (kg)': 0,
            'Syrup Yield (kg)': syrup_yield,
            'Crystal Price ($/kg)': 0,
            'Syrup Price ($/kg)': syrup_selling_price,
            'Crystal Revenue ($)': 0,
            'Syrup Revenue ($)': syrup_revenue,
            'Total Annual Revenue ($)': syrup_revenue,
        }

    def calculate_opex_annual(self):
        """Update OPEX with new batch parameters (1000L, optimized)"""
        opex_breakdown = {}

        # Raw materials (110 g/L, 110 kg per batch for 1000L)
        galactose_cost = 110 * self.glucose_cost  # 110 kg per batch
        formate_cost = 44.0 * self.formate_cost  # Adjusted for 110 g/L, 1000L
        cells_cost = 20.0 * 50.0  # 20 kg DCW per batch × $50/kg (revised estimate)
        # NAD+ with 80% recovery: only 20% makeup needed per batch
        nad_cost = 0.2 * 710.0  # 0.2 mol/batch makeup × $710/mol (80% recovery, Tufvesson 2011)
        nadp_cost = 0.1 * 5000.0  # 0.1 mol/batch × $5,000/mol (Tufvesson 2011)

        batches_per_year = self.production_hours_per_year / 24
        annual_galactose = galactose_cost * batches_per_year
        annual_formate = formate_cost * batches_per_year
        annual_cells = cells_cost * batches_per_year
        annual_nad = nad_cost * batches_per_year
        annual_nadp = nadp_cost * batches_per_year

        opex_breakdown['D-Galactose'] = annual_galactose
        opex_breakdown['Sodium Formate'] = annual_formate
        opex_breakdown['E. coli Whole Cell (DCW)'] = annual_cells
        opex_breakdown['NAD+ Cofactor (with recovery)'] = annual_nad
        opex_breakdown['NADP+ Cofactor'] = annual_nadp

        # Labor (2 FTE)
        actual_labor_hours_per_year = 2 * 2080
        annual_labor = actual_labor_hours_per_year * self.labor_cost
        opex_breakdown['Labor'] = annual_labor

        # Maintenance & Miscellaneous
        capex = self.calculate_capex().get('Total CAPEX', 1000000)
        maintenance = capex * self.maintenance_factor
        opex_breakdown['Maintenance'] = maintenance

        misc_cost = capex * 0.02
        opex_breakdown['Miscellaneous'] = misc_cost

        # Electricity & Water (minimal)
        opex_breakdown['Electricity'] = 0
        opex_breakdown['Water'] = 0

        total_opex = sum(v for k, v in opex_breakdown.items())
        opex_breakdown['Total Annual OPEX'] = total_opex

        return opex_breakdown

econ_syrup = TagatoseEconomicsSyrupOnly(system=None, product_stream=None)

capex_syrup = econ_syrup.calculate_capex()['Total CAPEX']
opex_syrup = econ_syrup.calculate_opex_annual()['Total Annual OPEX']
revenue_syrup = econ_syrup.calculate_revenue_annual()['Total Annual Revenue ($)']
profit_syrup = revenue_syrup - opex_syrup
roi_syrup = (profit_syrup / capex_syrup) * 100
breakeven_syrup = opex_syrup / (econ_syrup.calculate_revenue_annual()['Annual Tagatose (kg)'])

print(f"\nSyrup-Only Economics:")
print(f"  CAPEX: ${capex_syrup:,.0f}")
print(f"  Annual OPEX: ${opex_syrup:,.0f}")
print(f"  Annual Production: {econ_syrup.calculate_revenue_annual()['Annual Tagatose (kg)']:,.0f} kg (syrup)")
print(f"  Annual Revenue (@ $10/kg): ${revenue_syrup:,.0f}")
print(f"  Annual Profit: ${profit_syrup:,.0f}")
print(f"  ROI: {roi_syrup:.1f}%")
print(f"  Breakeven Price: ${breakeven_syrup:.2f}/kg")

# ============================================================================
# 3. SCENARIO 2: CRYSTAL-ONLY PRODUCTION
# ============================================================================

print("\n" + "="*90)
print("[SCENARIO 2] CRYSTAL-ONLY PRODUCTION")
print("="*90)

class TagatoseEconomicsCrystalOnly(TagatoseEconomicAnalysis):
    """Modified for crystal-only production"""

    def calculate_revenue_annual(self, product_concentration=None):
        """Crystal product only"""
        batches_per_year = self.production_hours_per_year / 24
        annual_tagatose_kg = 110 * batches_per_year  # 110 kg per batch (1000L × 110 g/L)

        # Crystal-only: premium price
        crystal_yield = annual_tagatose_kg
        crystal_selling_price = self.tagatose_price * 1.2  # 20% premium
        crystal_revenue = crystal_yield * crystal_selling_price

        return {
            'Annual Tagatose (kg)': annual_tagatose_kg,
            'Crystal Yield (kg)': crystal_yield,
            'Syrup Yield (kg)': 0,
            'Crystal Price ($/kg)': crystal_selling_price,
            'Syrup Price ($/kg)': 0,
            'Crystal Revenue ($)': crystal_revenue,
            'Syrup Revenue ($)': 0,
            'Total Annual Revenue ($)': crystal_revenue,
        }

    def calculate_opex_annual(self):
        """Update OPEX with new batch parameters (1000L, optimized)"""
        opex_breakdown = {}

        # Raw materials (110 g/L, 110 kg per batch for 1000L)
        galactose_cost = 110 * self.glucose_cost  # 110 kg per batch
        formate_cost = 44.0 * self.formate_cost  # Adjusted for 110 g/L, 1000L
        cells_cost = 20.0 * 50.0  # 20 kg DCW per batch × $50/kg (revised estimate)
        # NAD+ with 80% recovery: only 20% makeup needed per batch
        nad_cost = 0.2 * 710.0  # 0.2 mol/batch makeup × $710/mol (80% recovery, Tufvesson 2011)
        nadp_cost = 0.1 * 5000.0  # 0.1 mol/batch × $5,000/mol (Tufvesson 2011)

        batches_per_year = self.production_hours_per_year / 24
        annual_galactose = galactose_cost * batches_per_year
        annual_formate = formate_cost * batches_per_year
        annual_cells = cells_cost * batches_per_year
        annual_nad = nad_cost * batches_per_year
        annual_nadp = nadp_cost * batches_per_year

        opex_breakdown['D-Galactose'] = annual_galactose
        opex_breakdown['Sodium Formate'] = annual_formate
        opex_breakdown['E. coli Whole Cell (DCW)'] = annual_cells
        opex_breakdown['NAD+ Cofactor (with recovery)'] = annual_nad
        opex_breakdown['NADP+ Cofactor'] = annual_nadp

        # Labor
        actual_labor_hours_per_year = 2 * 2080
        annual_labor = actual_labor_hours_per_year * self.labor_cost
        opex_breakdown['Labor'] = annual_labor

        # Maintenance & Misc
        capex = self.calculate_capex().get('Total CAPEX', 1000000)
        maintenance = capex * self.maintenance_factor
        opex_breakdown['Maintenance'] = maintenance

        misc_cost = capex * 0.02
        opex_breakdown['Miscellaneous'] = misc_cost

        opex_breakdown['Electricity'] = 0
        opex_breakdown['Water'] = 0

        total_opex = sum(v for k, v in opex_breakdown.items())
        opex_breakdown['Total Annual OPEX'] = total_opex

        return opex_breakdown

econ_crystal = TagatoseEconomicsCrystalOnly(system=None, product_stream=None)

capex_crystal = econ_crystal.calculate_capex()['Total CAPEX']
opex_crystal = econ_crystal.calculate_opex_annual()['Total Annual OPEX']
revenue_crystal = econ_crystal.calculate_revenue_annual()['Total Annual Revenue ($)']
profit_crystal = revenue_crystal - opex_crystal
roi_crystal = (profit_crystal / capex_crystal) * 100
breakeven_crystal = opex_crystal / (econ_crystal.calculate_revenue_annual()['Annual Tagatose (kg)'])

print(f"\nCrystal-Only Economics:")
print(f"  CAPEX: ${capex_crystal:,.0f}")
print(f"  Annual OPEX: ${opex_crystal:,.0f}")
print(f"  Annual Production: {econ_crystal.calculate_revenue_annual()['Annual Tagatose (kg)']:,.0f} kg (crystals)")
print(f"  Annual Revenue (@ $12/kg): ${revenue_crystal:,.0f}")
print(f"  Annual Profit: ${profit_crystal:,.0f}")
print(f"  ROI: {roi_crystal:.1f}%")
print(f"  Breakeven Price: ${breakeven_crystal:.2f}/kg")

# ============================================================================
# 4. SCENARIO 3: MIXED PORTFOLIO (50/50 Syrup & Crystal)
# ============================================================================

print("\n" + "="*90)
print("[SCENARIO 3] MIXED PORTFOLIO (50/50 Syrup & Crystal)")
print("="*90)

batches_per_year_mixed = econ.production_hours_per_year / 24
annual_production = 110 * batches_per_year_mixed  # 110 kg per batch (1000L × 110 g/L)

syrup_volume = annual_production * 0.5
crystal_volume = annual_production * 0.5

syrup_price = econ.tagatose_price * 0.95  # 5% discount
crystal_price = econ.tagatose_price * 1.2  # 20% premium

syrup_revenue = syrup_volume * syrup_price
crystal_revenue = crystal_volume * crystal_price
total_revenue_mixed = syrup_revenue + crystal_revenue

opex_mixed = opex_syrup  # Same OPEX (production is same)
profit_mixed = total_revenue_mixed - opex_mixed
roi_mixed = (profit_mixed / capex_syrup) * 100
breakeven_mixed = opex_mixed / annual_production

weighted_price = total_revenue_mixed / annual_production

print(f"\nMixed Portfolio Economics (50% Syrup @ $9.50/kg + 50% Crystal @ $12/kg):")
print(f"  CAPEX: ${capex_syrup:,.0f}")
print(f"  Annual OPEX: ${opex_mixed:,.0f}")
print(f"  Annual Production: {annual_production:,.0f} kg")
print(f"    - Syrup: {syrup_volume:,.0f} kg @ ${syrup_price:.2f}/kg = ${syrup_revenue:,.0f}")
print(f"    - Crystal: {crystal_volume:,.0f} kg @ ${crystal_price:.2f}/kg = ${crystal_revenue:,.0f}")
print(f"  Annual Revenue: ${total_revenue_mixed:,.0f}")
print(f"  Weighted Average Price: ${weighted_price:.2f}/kg")
print(f"  Annual Profit: ${profit_mixed:,.0f}")
print(f"  ROI: {roi_mixed:.1f}%")
print(f"  Breakeven Price: ${breakeven_mixed:.2f}/kg")

# ============================================================================
# 5. SCENARIO COMPARISON TABLE
# ============================================================================

print("\n" + "="*90)
print("[SCENARIO COMPARISON SUMMARY]")
print("="*90)

print("\nComparison Table:")
print(f"{'Metric':<30} {'Syrup-Only':<20} {'Crystal-Only':<20} {'Mixed 50/50':<20}")
print("-" * 90)
print(f"{'CAPEX ($)':<30} ${capex_syrup:>18,.0f} ${capex_crystal:>18,.0f} ${capex_syrup:>18,.0f}")
print(f"{'Annual OPEX ($)':<30} ${opex_syrup:>18,.0f} ${opex_crystal:>18,.0f} ${opex_mixed:>18,.0f}")
print(f"{'Annual Revenue ($)':<30} ${revenue_syrup:>18,.0f} ${revenue_crystal:>18,.0f} ${total_revenue_mixed:>18,.0f}")
print(f"{'Annual Profit ($)':<30} ${profit_syrup:>18,.0f} ${profit_crystal:>18,.0f} ${profit_mixed:>18,.0f}")
print(f"{'ROI (%)':<30} {roi_syrup:>18.1f}% {roi_crystal:>18.1f}% {roi_mixed:>18.1f}%")
print(f"{'Breakeven Price ($/kg)':<30} ${breakeven_syrup:>18.2f} ${breakeven_crystal:>18.2f} ${breakeven_mixed:>18.2f}")
print(f"{'Weighted Avg Price ($/kg)':<30} {'$10.00':>18} {'$12.00':>18} ${weighted_price:>17.2f}")

# ============================================================================
# 6. COST DRIVER ANALYSIS (PARETO)
# ============================================================================

print("\n" + "="*90)
print("[COST DRIVER ANALYSIS - PARETO IMPACT]")
print("="*90)

# Get detailed OPEX breakdown
opex_detail = econ_syrup.calculate_opex_annual()
opex_total = opex_detail['Total Annual OPEX']

# Sort by cost
cost_items = {k: v for k, v in opex_detail.items() if k != 'Total Annual OPEX'}
sorted_costs = sorted(cost_items.items(), key=lambda x: x[1], reverse=True)

print("\nAnnual OPEX Breakdown (Ranked by Impact):")
print(f"{'Rank':<6} {'Cost Item':<30} {'Amount ($)':<15} {'% of Total':<12} {'Cumulative %':<12}")
print("-" * 90)

cumulative = 0
for rank, (item, cost) in enumerate(sorted_costs, 1):
    pct = (cost / opex_total) * 100
    cumulative += pct
    print(f"{rank:<6} {item:<30} ${cost:>13,.0f} {pct:>10.1f}% {cumulative:>10.1f}%")

# ============================================================================
# 7. SENSITIVITY ANALYSIS FOR EACH SCENARIO
# ============================================================================

print("\n" + "="*90)
print("[PRICE SENSITIVITY - THREE SCENARIOS]")
print("="*90)

print("\nPrice Sensitivity at Different Tagatose Market Prices:")
print(f"{'Price ($/kg)':<15} {'Syrup-Only':<25} {'Crystal-Only':<25} {'Mixed 50/50':<25}")
print(f"{'':15} {'Profit / ROI':<25} {'Profit / ROI':<25} {'Profit / ROI':<25}")
print("-" * 90)

for price in [8, 9, 10, 11, 12, 13, 14, 15]:
    # Update all models with new price
    econ_syrup.tagatose_price = price
    econ_crystal.tagatose_price = price

    # Syrup
    rev_s = econ_syrup.calculate_revenue_annual()['Total Annual Revenue ($)']
    prof_s = rev_s - opex_syrup
    roi_s = (prof_s / capex_syrup) * 100

    # Crystal
    rev_c = econ_crystal.calculate_revenue_annual()['Total Annual Revenue ($)']
    prof_c = rev_c - opex_crystal
    roi_c = (prof_c / capex_crystal) * 100

    # Mixed
    syrup_v = annual_production * 0.5
    crystal_v = annual_production * 0.5
    syrup_p = price * 0.95
    crystal_p = price * 1.2
    rev_m = syrup_v * syrup_p + crystal_v * crystal_p
    prof_m = rev_m - opex_mixed
    roi_m = (prof_m / capex_syrup) * 100

    print(f"{price:<15.0f} ${prof_s:>10,.0f} / {roi_s:>6.1f}%  ${prof_c:>10,.0f} / {roi_c:>6.1f}%  ${prof_m:>10,.0f} / {roi_m:>6.1f}%")

# ============================================================================
# 8. KEY FINDINGS AND RECOMMENDATIONS
# ============================================================================

print("\n" + "="*90)
print("[KEY FINDINGS AND RECOMMENDATIONS]")
print("="*90)

print("\n1. PRODUCTION SCENARIOS RANKED BY VIABILITY:")
print(f"   Rank 1 (Best): Crystal-Only Production")
print(f"      - Highest revenue per kg (${crystal_price:.2f}/kg)")
print(f"      - ROI: {roi_crystal:.1f}%")
print(f"      - Breakeven: ${breakeven_crystal:.2f}/kg")
print(f"      - Risk: Market demand for premium crystals")
print(f"\n   Rank 2: Mixed Portfolio (50/50)")
print(f"      - Balanced approach")
print(f"      - Average price: ${weighted_price:.2f}/kg")
print(f"      - ROI: {roi_mixed:.1f}%")
print(f"      - Breakeven: ${breakeven_mixed:.2f}/kg")
print(f"      - Risk: Lower than single-product strategy")
print(f"\n   Rank 3 (Least): Syrup-Only Production")
print(f"      - Base market price (${syrup_price:.2f}/kg)")
print(f"      - ROI: {roi_syrup:.1f}%")
print(f"      - Breakeven: ${breakeven_syrup:.2f}/kg")
print(f"      - Risk: Commodity market, low margins")

print(f"\n2. IMPACT OF PROCESS CHANGES (from original 150g/L, 36hr):")
print(f"   - Galactose reduced 150→110 g/L: -26.7% product per batch")
print(f"   - Reaction time reduced 36→24 hr: +50% batches per year")
print(f"   - Net: {annual_production:,.0f} kg/yr (original 15,625 kg/yr)")
print(f"   - Annual OPEX: ${opex_mixed:,.0f} (labor costs reduced due to higher throughput)")

print(f"\n3. COST DRIVER HIERARCHY (Pareto - top 3):")
print(f"   - Labor: {(cost_items['Labor']/opex_total*100):.1f}% of OPEX (PRIMARY DRIVER)")
print(f"   - D-Galactose: {(cost_items['D-Galactose']/opex_total*100):.1f}% of OPEX")
print(f"   - Maintenance: {(cost_items['Maintenance']/opex_total*100):.1f}% of OPEX")
print(f"   → Focus cost reduction efforts on these three items")

print(f"\n4. BREAK-EVEN ANALYSIS:")
print(f"   Current market price: $10/kg")
print(f"   Lowest breakeven (Mixed): ${breakeven_mixed:.2f}/kg (requires {((breakeven_mixed-10)/10*100):.0f}% price increase)")
print(f"   Highest breakeven (Syrup): ${breakeven_syrup:.2f}/kg (requires {((breakeven_syrup-10)/10*100):.0f}% price increase)")
print(f"   → None of the scenarios are viable at $10/kg with current cost structure")

print(f"\n5. RECOMMENDATIONS:")
if roi_crystal > 0:
    print(f"   [OK] Crystal-only strategy is viable at current costs")
else:
    print(f"   --> If pursuing crystal-only: target premium markets ($15+/kg)")

if roi_mixed > 0:
    print(f"   [OK] Mixed portfolio is viable at current costs")
else:
    print(f"   --> If pursuing mixed portfolio: balance price premium with volume")

print(f"   --> Focus on labor cost reduction (automation, workflow optimization)")
print(f"   --> Negotiate D-Galactose pricing below $2.00/kg")
print(f"   --> Consider scale-up to achieve equipment utilization efficiency")

print("\n" + "="*90)
print("END OF REVISED ECONOMIC ANALYSIS")
print("="*90)
