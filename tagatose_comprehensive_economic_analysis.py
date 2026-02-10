#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D-Tagatose Production - Comprehensive Economic Analysis (v2 Optimized)
Based on 2024-2025 Market Prices with 1000L Scale-Up & NAD+ Recovery

완전한 경제성 분석 (v2 최적화):
1. 1000L 반응기 + 20 g/L 셀 투입 + 1 mM NAD+ with 80% 회수
2. 현실적 시장 가격 적용 (D-Tagatose $10/kg, D-Galactose $2/kg, Sodium Formate $0.25/kg)
3. 손익분기점 분석 (OPEX only vs 전체 자본 회수)
4. 가격 민감도 분석 (프리미엄 시장 $12-16/kg)
5. 원료비 & 프로세스 최적화 영향도 분석
6. 경제 타당성 평가 및 권고사항
7. 비용 감소 기회 분석 (E. coli 계약, 노동 자동화 등)

v2 Key Changes:
- Annual Production: 17,188 kg → 34,375 kg (+100%)
- OPEX: $520,096 → $493,912 (-5%)
- Breakeven: $30.26/kg → $14.37/kg (-53%)
- NAD+ Cost: $46,875 → $9,375/year (-80%)
"""

import sys
sys.path.insert(0, 'C:\\Users\\Jahyun\\PycharmProjects\\biosteam')

from biosteam.units.tagatose_economics import TagatoseEconomicAnalysis

# ============================================================================
# 1. Analysis Setup
# ============================================================================

print("="*80)
print("D-TAGATOSE PRODUCTION PROCESS - v2 OPTIMIZED")
print("1000L Reactor | 20 g/L Biocatalyst | 1 mM NAD+ with 80% Recovery")
print("Comprehensive Economic Analysis with 2024-2025 Market Prices")
print("="*80)

# ============================================================================
# 2. 경제성 분석 인스턴스 생성
# ============================================================================

# 시스템 없이 경제 분석만 수행 (순수 경제성 평가)
econ = TagatoseEconomicAnalysis(system=None, product_stream=None)

# v2 최적화 기준 가격이 설정되어 있음:
# - Tagatose: $10/kg (기본값, 프리미엄 시장 $15-16/kg 목표)
# - D-Galactose: $2/kg (산업급, 벌크 계약 시 $1.50/kg)
# - Sodium Formate: $0.25/kg (안정적 시장가)
# - E. coli: $50/kg DCW (벌크 계약 시 $35/kg)
# - NAD+: $710/mol (Tufvesson 2011, 80% 회수로 실제 $142/mol 효과)

print(f"\nBase Market Prices (2024-2025):")
print(f"  D-Tagatose: ${econ.tagatose_price:.2f}/kg (Target: $15-16/kg premium markets)")
print(f"  D-Galactose: ${econ.glucose_cost:.2f}/kg (Industrial bulk)")
print(f"  Sodium Formate: ${econ.formate_cost:.2f}/kg (Stable)")

# ============================================================================
# 3. 상세 경제성 보고서 출력
# ============================================================================

econ.print_detailed_economic_report()

# ============================================================================
# 4. 추가 분석: 가격별 시나리오
# ============================================================================

print("\n" + "="*80)
print("[SUPPLEMENTAL] SCENARIO ANALYSIS - Key Business Cases")
print("="*80)

scenarios = {
    'Commodity Market ($10/kg)': 10.0,
    'Near Breakeven ($13/kg)': 13.0,
    'Pharma Entry ($15/kg)': 15.0,
    'Premium Target ($16/kg)': 16.0,
    'Specialty Food ($17/kg)': 17.0,
}

print("\nScenario Comparison:\n")
print("Scenario                CAPEX      Annual OPEX  Annual Profit  ROI (%)  Payback (yr)")
print("-" * 85)

for scenario_name, price in scenarios.items():
    econ.tagatose_price = price
    capex = econ.calculate_capex().get('Total CAPEX', 0)
    opex = econ.calculate_opex_annual().get('Total Annual OPEX', 0)
    profit_data = econ.calculate_profitability()
    profit = profit_data.get('Annual Profit ($)', 0)
    roi = profit_data.get('ROI (Annual %)', 0)
    payback = profit_data.get('Payback Period (years)', 999)

    payback_str = f"{payback:.1f}" if payback < 999 else "∞"
    print(f"{scenario_name:<24} ${capex:>10,.0f}  ${opex:>11,.0f}  ${profit:>13,.0f}  {roi:>7.1f}  {payback_str:>10}")

# Reset to market price
econ.tagatose_price = 10.0

# ============================================================================
# 5. 최종 권고사항
# ============================================================================

print("\n" + "="*80)
print("[FINAL RECOMMENDATION]")
print("="*80)

breakeven_data = econ.calculate_breakeven_analysis()
breakeven_price = breakeven_data['Breakeven Price (w/ CAPEX recovery) ($/kg)']

print(f"\nv2 Optimization Economics:")
print(f"  Current Market Price: ${econ.tagatose_price:.2f}/kg (commodity baseline)")
print(f"  Breakeven Price: ${breakeven_price:.2f}/kg")
print(f"  Premium Target: $15-16/kg (pharmaceutical/specialty food)")
print(f"  Safety Margin @ Premium: {((16.0 - breakeven_price) / breakeven_price * 100):.1f}% (at $16/kg)")

profit_data = econ.calculate_profitability()
annual_profit = profit_data['Annual Profit ($)']

print(f"\nAt Current Market Price:")
print(f"  - Annual Revenue: ${econ.calculate_revenue_annual()['Total Annual Revenue ($)']:,.0f}")
print(f"  - Annual Profit: ${annual_profit:,.0f}")
print(f"  - Annual ROI: {profit_data['ROI (Annual %)']:.1f}%")
print(f"  - Payback Period: {profit_data['Payback Period (years)']:.1f} years")

if econ.tagatose_price >= 15.0 and annual_profit > 0:
    print("\n[OK] Conclusion: ECONOMICALLY VIABLE (Premium Market)")
    print("  -> v2 Strategy: Focus on pharmaceutical/specialty food markets ($15-16/kg)")
    print("  -> Recommend commercialization with premium market entry strategy")
elif econ.tagatose_price >= 14.0 and annual_profit > 0:
    print("\n[✓] Conclusion: MARGINALLY VIABLE (Near Breakeven)")
    print("  -> v2 Viability: Breakeven at $14.37/kg")
    print("  -> Recommend combined strategy: Premium market + cost optimization")
elif annual_profit > 0:
    print("\n[~] Conclusion: REQUIRES OPTIMIZATION")
    print("  -> Current commodity market ($10/kg) not viable")
    print("  -> Required: Premium market access ($15+/kg) OR cost reduction initiatives")
else:
    print("\n[X] Conclusion: NOT VIABLE AT CURRENT PRICE")
    print(f"  -> Breakeven Price: ${breakeven_price:.2f}/kg")
    print(f"  -> v2 Strategy Options:")
    print(f"  -> 1. Access premium market ($15-16/kg) for profitability")
    print(f"  -> 2. Implement cost reductions: E. coli contracts ($46.9k), Labor automation ($39k)")
    print(f"  -> 3. Combined approach enables $10.28/kg breakeven")

# ============================================================================
# 6. 상세 CAPEX 분석
# ============================================================================

print("\n" + "="*80)
print("[CAPEX DETAIL ANALYSIS]")
print("="*80)

capex_detail = econ.calculate_capex()
total_equipment = capex_detail['Equipment Cost']
indirect = capex_detail['Indirect Cost (40%)']
working = capex_detail['Working Capital (15%)']
total = capex_detail['Total CAPEX']

print(f"\nEquipment Cost:        ${total_equipment:>12,.0f}  ({total_equipment/total*100:.1f}%)")
print(f"  (Reactors, separators, evaporators, compressors, etc.)")
print(f"\nIndirect Cost (40%):   ${indirect:>12,.0f}  ({indirect/total*100:.1f}%)")
print(f"  (Engineering, installation, contingency)")
print(f"\nWorking Capital (15%): ${working:>12,.0f}  ({working/total*100:.1f}%)")
print(f"  (Operating inventory, cash flow)")
print(f"\n{'-'*50}")
print(f"TOTAL CAPEX:           ${total:>12,.0f}  (100%)")

# ============================================================================
# 7. 상세 OPEX 분석
# ============================================================================

print("\n" + "="*80)
print("[OPEX DETAIL ANALYSIS - Annual]")
print("="*80)

opex_detail = econ.calculate_opex_annual()
total_opex = opex_detail['Total Annual OPEX']

print(f"\nRaw Materials:")
# v2 parameters: 110 kg Galactose per batch, 24 hr cycle, 312.5 batches/year
batches_per_year_v2 = econ.production_hours_per_year / 24  # 24 hr batch time in v2
gal_per_batch_v2 = 110  # kg, v2 optimized (was 75 in v0/v1)
formate_per_batch_v2 = 44  # kg, v2 optimized (5% molar excess, was 29.75 in v0/v1)
gal_cost = gal_per_batch_v2 * econ.glucose_cost * batches_per_year_v2
formate_cost = formate_per_batch_v2 * econ.formate_cost * batches_per_year_v2
print(f"  D-Galactose:         ${gal_cost:>12,.0f}  ({gal_cost/total_opex*100:.1f}%)")
print(f"  Sodium Formate:      ${formate_cost:>12,.0f}  ({formate_cost/total_opex*100:.1f}%)")

print(f"\nUtilities:")
print(f"  Electricity:         ${opex_detail['Electricity']:>12,.0f}  ({opex_detail['Electricity']/total_opex*100:.1f}%)")
print(f"  Water:               ${opex_detail['Water']:>12,.0f}  ({opex_detail['Water']/total_opex*100:.1f}%)")

print(f"\nLabor & Operations:")
print(f"  Labor:               ${opex_detail['Labor']:>12,.0f}  ({opex_detail['Labor']/total_opex*100:.1f}%)")
print(f"  Maintenance (4%):    ${opex_detail['Maintenance']:>12,.0f}  ({opex_detail['Maintenance']/total_opex*100:.1f}%)")
print(f"  Miscellaneous (2%):  ${opex_detail['Miscellaneous']:>12,.0f}  ({opex_detail['Miscellaneous']/total_opex*100:.1f}%)")

print(f"\n{'-'*50}")
print(f"TOTAL ANNUAL OPEX:     ${total_opex:>12,.0f}  (100%)")
print(f"OPEX per kg tagatose:  ${total_opex / econ.calculate_revenue_annual()['Annual Tagatose (kg)']:>12,.2f}/kg")

# ============================================================================
# 8. 핵심 성과 지표
# ============================================================================

print("\n" + "="*80)
print("[KEY PERFORMANCE INDICATORS - KPI]")
print("="*80)

batches_per_year = econ.production_hours_per_year / 24  # v2: 24 hr batch time
annual_tagatose = batches_per_year * 110  # v2: 110 kg per batch (1000L × 110 g/L)

print(f"\nProduction Metrics (v2 Optimized):")
print(f"  Operating Hours/Year:      {econ.production_hours_per_year:.0f} hrs")
print(f"  Batch Duration:            24 hrs (16h anaerobic + 8h aerobic, integrated stages)")
print(f"  Batches per Year:          {batches_per_year:.0f}")
print(f"  Tagatose per Batch:        110 kg (1000L reactor × 110 g/L)")
print(f"  Annual Production:         {annual_tagatose:,.0f} kg (v2: +100% vs v0)")
print(f"  Capacity Utilization:      {econ.plant_capacity_factor*100:.0f}%")

print(f"\nFinancial Metrics:")
capex = econ.calculate_capex()['Total CAPEX']
revenue = econ.calculate_revenue_annual()['Total Annual Revenue ($)']
print(f"  CAPEX:                     ${capex:,.0f}")
print(f"  Annual Revenue:            ${revenue:,.0f}")
print(f"  Revenue/CAPEX Ratio:       {revenue/capex:.2f}x")

print(f"\nProfitability (at ${econ.tagatose_price:.0f}/kg):")
profit = econ.calculate_profitability()
print(f"  Annual Profit:             ${profit['Annual Profit ($)']:,.0f}")
print(f"  ROI:                       {profit['ROI (Annual %)']:.1f}%")
print(f"  Payback Period:            {profit['Payback Period (years)']:.1f} years")
print(f"  NPV (20yr @ 10%):          ${profit['NPV (20 years, 10% discount rate) ($)']:,.0f}")

print("\n" + "="*80)
print("END OF ANALYSIS")
print("="*80)
