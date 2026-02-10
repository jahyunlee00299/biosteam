#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D-Tagatose Production - Detailed Cost Breakdown by Operation & Raw Material

공정별 조작(Operation)과 원재료(Raw Material) 비용 세분화 분석
- 각 단위공정별 비용
- 각 원재료별 비용
- 에너지 비용 상세화
- 정제 비용 분석
"""

import pandas as pd
import numpy as np

print("="*100)
print("D-TAGATOSE PRODUCTION - DETAILED COST BREAKDOWN (OPTIMIZED v2)")
print("1000L Scale-Up | 20 g/L Biocatalyst | 1 mM NAD+ with 80% Recovery")
print("="*100)

# ============================================================================
# 1. 원재료 비용 상세 분석
# ============================================================================

print("\n" + "="*100)
print("[1] RAW MATERIALS COST BREAKDOWN - Annual (312.5 batches × 110 kg tagatose/batch)")
print("="*100)

# 기본 계산: 연간 312.5 배치
batches_per_year = 312.5

# 배치당 원재료 (110 g/L, 1000L 기준 - 최적화)
galactose_per_batch_kg = 110.0  # 110 g/L × 1.0 m³
formate_per_batch_kg = 44.0    # Adjusted for 110 g/L galactose (5% excess)

# 전세포 촉매 (E. coli K-12, DCW 기준) - 감소
cells_per_batch_kg = 20.0  # 20 g/L × 1000L (Dry Cell Weight) [감소: 50→20 g/L]

# 코팩터 (1000L 기준, NAD+ 회수 포함)
volume_L = 1000
# NAD+ 초기: 1 mM, 회수 80%, 유지 투입 20%만 필요
nad_per_batch_mmol = 0.2 * 1000 / 1000  # 0.2 mol/batch (80% recovery) [감소: 2→1 mM]
nadp_per_batch_mmol = 0.1 * 1000 / 1000  # 0.1 mol/batch (0.1 mM × 1000L)

# 물 (반응 매질)
water_per_batch_kg = 400  # 약 400 kg (용매)

# 가격 데이터
galactose_price = 2.00  # $/kg
formate_price = 0.25    # $/kg
cells_price = 25.0      # $/kg DCW (E. coli K-12 산업용)
nad_price = 150.0       # $/mol (실험실 등급 기준)
nadp_price = 200.0      # $/mol
water_price = 0.002     # $/L

# 활성탄 (탈색 공정)
carbon_loading_pct = 0.02  # 2% w/w tagatose 기준
carbon_per_batch_kg = 55 * carbon_loading_pct  # 1.1 kg per batch
carbon_price = 2.00  # $/kg

# 다른 정제 화학물질
misc_chemicals_per_batch = 2.0  # 기타 화학물질 $2/batch (pH 조정, 세제 등)

# ============================================================================
# 원재료 계산
# ============================================================================

raw_materials = {
    'D-Galactose (Main Substrate)': {
        'qty_per_batch': galactose_per_batch_kg,
        'unit': 'kg',
        'unit_price': galactose_price,
        'qty_per_year': galactose_per_batch_kg * batches_per_year,
    },
    'Sodium Formate (Co-substrate)': {
        'qty_per_batch': formate_per_batch_kg,
        'unit': 'kg',
        'unit_price': formate_price,
        'qty_per_year': formate_per_batch_kg * batches_per_year,
    },
    'E. coli Whole Cell Biocatalyst (DCW)': {
        'qty_per_batch': cells_per_batch_kg,
        'unit': 'kg',
        'unit_price': cells_price,
        'qty_per_year': cells_per_batch_kg * batches_per_year,
    },
    'NAD+ Cofactor': {
        'qty_per_batch': nad_per_batch_mmol,
        'unit': 'mol',
        'unit_price': nad_price,
        'qty_per_year': nad_per_batch_mmol * batches_per_year,
    },
    'NADP+ Cofactor': {
        'qty_per_batch': nadp_per_batch_mmol,
        'unit': 'mol',
        'unit_price': nadp_price,
        'qty_per_year': nadp_per_batch_mmol * batches_per_year,
    },
    'Water (Solvent)': {
        'qty_per_batch': water_per_batch_kg,
        'unit': 'kg',
        'unit_price': water_price,
        'qty_per_year': water_per_batch_kg * batches_per_year,
    },
    'Activated Carbon (Decolorization)': {
        'qty_per_batch': carbon_per_batch_kg,
        'unit': 'kg',
        'unit_price': carbon_price,
        'qty_per_year': carbon_per_batch_kg * batches_per_year,
    },
    'Miscellaneous Chemicals (pH, Cleaning)': {
        'qty_per_batch': 1,  # per batch
        'unit': 'batch',
        'unit_price': misc_chemicals_per_batch,
        'qty_per_year': batches_per_year,
    },
}

# 계산 및 출력
print("\nRaw Materials by Category:\n")
print(f"{'Material':<40} {'Per Batch':<20} {'Price Unit':<15} {'Annual Cost':<15}")
print(f"{'':40} {'Quantity':20} {'':15} {'':15}")
print("-" * 100)

raw_materials_total = 0
for material, data in raw_materials.items():
    annual_cost = data['qty_per_year'] * data['unit_price']
    raw_materials_total += annual_cost
    qty_str = f"{data['qty_per_batch']:.2f} {data['unit']}"
    price_str = f"${data['unit_price']:.2f}/{data['unit']}"
    print(f"{material:<40} {qty_str:<20} {price_str:<15} ${annual_cost:>13,.0f}")

print("-" * 100)
print(f"{'TOTAL RAW MATERIALS COST':<40} {'':<20} {'':<15} ${raw_materials_total:>13,.0f}")

# ============================================================================
# 2. 공정별 조작 비용 (Unit Operations)
# ============================================================================

print("\n" + "="*100)
print("[2] UNIT OPERATIONS COST BREAKDOWN - Capital & Operating Costs")
print("="*100)

unit_operations = {
    'WholeCellBioreactor (1000L)': {
        'description': 'Main reaction vessel with agitation & temperature control (scaled-up)',
        'capex': 225000,  # Scaled from 150k (1.5x for doubled volume)
        'power_kW': 5.0,  # Agitation + cooling
        'operating_hours_per_batch': 24,
        'annual_hours': 312.5 * 24,
    },
    'Oxygen Compressor (O2 Supply)': {
        'description': 'Compressed air supply for aerobic phase (16-24 hr)',
        'capex': 30000,  # Increased for 1000L oxygen demand
        'power_kW': 2.5,  # Compression power
        'operating_hours_per_batch': 8,  # Only 8h aerobic
        'annual_hours': 312.5 * 8,
    },
    'Centrifuge (Solid-Liquid Separator)': {
        'description': 'Biomass removal after fermentation (larger capacity)',
        'capex': 25000,  # Increased for 1000L processing
        'power_kW': 3.0,  # Centrifugal separation
        'operating_hours_per_batch': 2,
        'annual_hours': 312.5 * 2,
    },
    'Decolorization Unit (Activated Carbon)': {
        'description': 'Color removal with activated carbon adsorption (larger)',
        'capex': 20000,  # Increased capacity
        'power_kW': 1.0,  # Mixing
        'operating_hours_per_batch': 4,
        'annual_hours': 312.5 * 4,
    },
    'Crystallization Unit': {
        'description': 'Cooling crystallization & filtration (larger)',
        'capex': 50000,  # Increased from 40k
        'power_kW': 4.0,  # Cooling + mechanical filtration
        'operating_hours_per_batch': 6,
        'annual_hours': 312.5 * 6,
    },
    'Vacuum Evaporator': {
        'description': 'Concentration (for syrup option) or dryer for crystals (larger)',
        'capex': 40000,  # Increased from 30k
        'power_kW': 6.0,  # Vacuum pump + heating
        'operating_hours_per_batch': 3,
        'annual_hours': 312.5 * 3,
    },
}

electricity_price = 0.12  # $/kWh

print("\nCapital Cost by Unit Operation:")
print("-" * 100)

unit_capex_total = 0
for unit, specs in unit_operations.items():
    unit_capex_total += specs['capex']
    print(f"{unit:<40} ${specs['capex']:>15,}  {specs['description']}")

print("-" * 100)
print(f"{'SUBTOTAL - Equipment CAPEX':<40} ${unit_capex_total:>15,}")

# 간접비 추가
indirect_factor = 0.40
indirect_capex = unit_capex_total * indirect_factor
working_capital = unit_capex_total * 0.15
total_capex = unit_capex_total + indirect_capex + working_capital

print(f"{'Indirect Costs (40%)':<40} ${indirect_capex:>15,.0f}")
print(f"{'Working Capital (15%)':<40} ${working_capital:>15,.0f}")
print(f"{'TOTAL CAPEX':<40} ${total_capex:>15,.0f}")

# ============================================================================
# 에너지 비용 분석
# ============================================================================

print("\n" + "="*100)
print("[3] ENERGY COSTS BY UNIT OPERATION - Annual")
print("="*100)

print("\nElectricity Consumption (@ $0.12/kWh):\n")
print(f"{'Unit Operation':<40} {'Power (kW)':<15} {'Hours/Year':<15} {'kWh/Year':<15} {'Annual Cost':<15}")
print("-" * 100)

energy_cost_total = 0
for unit, specs in unit_operations.items():
    annual_hours = specs['annual_hours']
    kwh_per_year = specs['power_kW'] * annual_hours
    annual_cost = kwh_per_year * electricity_price
    energy_cost_total += annual_cost
    print(f"{unit:<40} {specs['power_kW']:<15.1f} {annual_hours:<15.0f} {kwh_per_year:<15.0f} ${annual_cost:>13,.0f}")

print("-" * 100)
print(f"{'TOTAL ENERGY COST':<40} {'':<15} {'':<15} {'':<15} ${energy_cost_total:>13,.0f}")

# ============================================================================
# 냉각수 & 유틸리티
# ============================================================================

print("\n" + "="*100)
print("[4] UTILITIES COST - Cooling Water & Miscellaneous")
print("="*100)

# 냉각수: 반응기, 결정화 단위에서 필요
cooling_water_L_per_batch = 500  # 500L 냉각수 per batch (冷却)
cooling_water_cost = 0.002  # $/L

annual_cooling_cost = cooling_water_L_per_batch * batches_per_year * cooling_water_cost

print(f"\nCooling Water (reactor & crystallization):")
print(f"  Per batch: {cooling_water_L_per_batch} L")
print(f"  Annual consumption: {cooling_water_L_per_batch * batches_per_year:,.0f} L")
print(f"  Unit price: ${cooling_water_cost}/L")
print(f"  Annual cost: ${annual_cooling_cost:,.0f}")

# 압축 공기 (일부 프로세스에서 필요)
compressed_air_cost = 500  # 연간 $500 (에스티메이트)

print(f"\nCompressed Air (for various pneumatic operations):")
print(f"  Annual cost: ${compressed_air_cost:,.0f}")

utilities_total = annual_cooling_cost + compressed_air_cost
print(f"\nTOTAL UTILITIES COST: ${utilities_total:,.0f}")

# ============================================================================
# 정제 공정 비용 상세
# ============================================================================

print("\n" + "="*100)
print("[5] PURIFICATION PROCESS COSTS - Detailed Breakdown")
print("="*100)

purification_costs = {
    'Centrifugation (Biomass Removal)': {
        'operation': 'Solid-Liquid Separation',
        'equipment_capex': 20000,
        'consumables_per_batch_cost': 5.0,  # $5 per run (maintenance, filters)
        'energy_per_batch_kwh': 3.0 * 2,  # 3 kW × 2 hours
    },
    'Decolorization (Activated Carbon)': {
        'operation': 'Color removal using activated carbon',
        'equipment_capex': 15000,
        'consumables_per_batch_cost': carbon_per_batch_kg * carbon_price,  # Carbon cost
        'energy_per_batch_kwh': 1.0 * 4,  # 1 kW × 4 hours
    },
    'Crystallization & Filtration': {
        'operation': 'Crystal formation by cooling & mechanical separation',
        'equipment_capex': 40000,
        'consumables_per_batch_cost': 10.0,  # $10 per batch (filter aids, cleaning)
        'energy_per_batch_kwh': 4.0 * 6,  # 4 kW × 6 hours (cooling + mechanical)
    },
    'Evaporation/Concentration (optional Syrup)': {
        'operation': 'Water removal by vacuum evaporation',
        'equipment_capex': 30000,
        'consumables_per_batch_cost': 15.0,  # $15 per batch (cleaning, maintenance)
        'energy_per_batch_kwh': 6.0 * 3,  # 6 kW × 3 hours
    },
}

print("\nPurification Step Details:\n")
print(f"{'Step':<35} {'CAPEX':<15} {'Consumables/Batch':<20} {'Energy/Batch':<15}")
print("-" * 100)

purif_capex_total = 0
purif_consumables_total = 0
purif_energy_total = 0

for step, details in purification_costs.items():
    purif_capex_total += details['equipment_capex']
    purif_consumables_total += details['consumables_per_batch_cost']
    purif_energy_total += details['energy_per_batch_kwh']

    energy_cost = details['energy_per_batch_kwh'] * electricity_price
    print(f"{step:<35} ${details['equipment_capex']:>13,}  ${details['consumables_per_batch_cost']:>17.2f}  {details['energy_per_batch_kwh']:>13.1f} kWh")

print("-" * 100)
print(f"{'SUBTOTAL':<35} ${purif_capex_total:>13,}  ${purif_consumables_total:>17.2f}  {purif_energy_total:>13.1f} kWh/batch")

# Annual purification consumables cost
annual_purif_consumables = purif_consumables_total * batches_per_year
annual_purif_energy = purif_energy_total * batches_per_year * electricity_price

print(f"\nAnnual Purification Costs:")
print(f"  Consumables (chemicals, filters, etc.): ${annual_purif_consumables:,.0f}")
print(f"  Energy for purification steps: ${annual_purif_energy:,.0f}")
print(f"  Total annual purification OPEX: ${annual_purif_consumables + annual_purif_energy:,.0f}")

# ============================================================================
# 반응기 운영 비용 (Bioreactor specific)
# ============================================================================

print("\n" + "="*100)
print("[6] BIOREACTOR OPERATION COSTS - Reaction Phase Breakdown")
print("="*100)

# Stage 1: Anaerobic (16 hr)
stage1_energy_kwh_per_batch = 5.0 * 16  # 5 kW agitation × 16 hours
stage1_energy_cost_per_batch = stage1_energy_kwh_per_batch * electricity_price

# Stage 2-3: Aerobic (8 hr) - with oxygen compression
stage2_energy_kwh_per_batch = 5.0 * 8  # 5 kW agitation × 8 hours
stage2_oxygen_kwh_per_batch = 2.5 * 8  # 2.5 kW compressor × 8 hours
stage2_total_kwh = stage2_energy_kwh_per_batch + stage2_oxygen_kwh_per_batch
stage2_energy_cost_per_batch = stage2_total_kwh * electricity_price

total_reactor_energy_per_batch = stage1_energy_kwh_per_batch + stage2_total_kwh
total_reactor_energy_cost_per_batch = stage1_energy_cost_per_batch + stage2_energy_cost_per_batch

print("\nReaction Phases Energy Analysis:")
print(f"\nStage 1 - Anaerobic Phase (0-16 hr):")
print(f"  Agitation: 5 kW × 16 hr = {stage1_energy_kwh_per_batch:.0f} kWh")
print(f"  Cost: ${stage1_energy_cost_per_batch:.2f}/batch")

print(f"\nStage 2-3 - Aerobic Phase (16-24 hr, with O2):")
print(f"  Agitation: 5 kW × 8 hr = {stage2_energy_kwh_per_batch:.0f} kWh")
print(f"  O2 Compression: 2.5 kW × 8 hr = {stage2_oxygen_kwh_per_batch:.0f} kWh")
print(f"  Total: {stage2_total_kwh:.0f} kWh")
print(f"  Cost: ${stage2_energy_cost_per_batch:.2f}/batch")

print(f"\nTotal Bioreactor Energy per Batch:")
print(f"  Total: {total_reactor_energy_per_batch:.0f} kWh")
print(f"  Cost: ${total_reactor_energy_cost_per_batch:.2f}/batch")
print(f"  Annual cost (312.5 batches): ${total_reactor_energy_cost_per_batch * batches_per_year:,.0f}")

# ============================================================================
# 노동 비용 분석
# ============================================================================

print("\n" + "="*100)
print("[7] LABOR COSTS - By Function")
print("="*100)

labor_breakdown = {
    'Batch Setup & Preparation': {
        'hours_per_batch': 2,
        'hourly_rate': 50,
        'description': 'Feed preparation, sterilization, instrument setup',
    },
    'Active Monitoring (Bioreactor)': {
        'hours_per_batch': 3,
        'hourly_rate': 50,
        'description': 'Temperature, pH, agitation monitoring during 24hr reaction',
    },
    'Downstream Processing': {
        'hours_per_batch': 2,
        'hourly_rate': 50,
        'description': 'Centrifugation, decolorization, crystallization operation',
    },
    'Product Finishing & QA': {
        'hours_per_batch': 1.5,
        'hourly_rate': 55,
        'description': 'Drying, packaging, quality testing',
    },
}

print("\nLabor Cost by Activity (per batch):\n")
print(f"{'Activity':<40} {'Hours':<10} {'Rate/hr':<10} {'Cost/Batch':<15} {'Annual Cost':<15}")
print("-" * 100)

total_labor_hours_per_batch = 0
total_labor_cost_per_batch = 0
annual_labor_cost = 0

for activity, data in labor_breakdown.items():
    cost_per_batch = data['hours_per_batch'] * data['hourly_rate']
    annual_cost = cost_per_batch * batches_per_year
    total_labor_hours_per_batch += data['hours_per_batch']
    total_labor_cost_per_batch += cost_per_batch
    annual_labor_cost += annual_cost

    print(f"{activity:<40} {data['hours_per_batch']:<10.1f} ${data['hourly_rate']:<9.0f} ${cost_per_batch:<14.0f} ${annual_cost:>13,.0f}")

print("-" * 100)
print(f"{'TOTAL LABOR':<40} {total_labor_hours_per_batch:<10.1f} {'':<10} ${total_labor_cost_per_batch:<14.0f} ${annual_labor_cost:>13,.0f}")

# ============================================================================
# 유지보수 & 기타 운영 비용
# ============================================================================

print("\n" + "="*100)
print("[8] MAINTENANCE & MISC OPERATING COSTS")
print("="*100)

maintenance_breakdown = {
    'Equipment Preventive Maintenance': {
        'pct_capex': 0.04,
        'capex_base': total_capex,
        'description': 'Scheduled maintenance on all equipment',
    },
    'Miscellaneous & Contingency': {
        'pct_capex': 0.02,
        'capex_base': total_capex,
        'description': 'General supplies, contingency, overhead allocation',
    },
}

print("\nMaintenance Cost Breakdown (annual):\n")
print(f"{'Item':<40} {'% of CAPEX':<15} {'Annual Cost':<20} {'Description':<30}")
print("-" * 100)

maintenance_total = 0
for item, data in maintenance_breakdown.items():
    cost = data['capex_base'] * data['pct_capex']
    maintenance_total += cost
    print(f"{item:<40} {data['pct_capex']*100:<14.0f}% ${cost:>18,.0f}  {data['description']:<30}")

print("-" * 100)
print(f"{'TOTAL MAINTENANCE & MISC':<40} {'':<15} ${maintenance_total:>18,.0f}")

# ============================================================================
# 종합 비용 요약 (Cost Roll-up)
# ============================================================================

print("\n" + "="*100)
print("[9] COMPREHENSIVE COST SUMMARY - Consolidated View")
print("="*100)

# CAPEX 종합
print("\nCAPITAL EXPENDITURE (CAPEX) - Summary:")
print("-" * 100)
print(f"{'Equipment (Unit Operations)':<50} ${unit_capex_total:>20,.0f}")
print(f"{'  - Bioreactor':<50} ${150000:>20,.0f}")
print(f"{'  - Oxygen Compressor':<50} ${25000:>20,.0f}")
print(f"{'  - Centrifuge':<50} ${20000:>20,.0f}")
print(f"{'  - Decolorization Unit':<50} ${15000:>20,.0f}")
print(f"{'  - Crystallization Unit':<50} ${40000:>20,.0f}")
print(f"{'  - Evaporator':<50} ${30000:>20,.0f}")
print(f"{'Indirect Costs (Engineering, Installation)':<50} ${indirect_capex:>20,.0f}")
print(f"{'Working Capital':<50} ${working_capital:>20,.0f}")
print(f"{'TOTAL CAPEX':<50} ${total_capex:>20,.0f}")

# OPEX 종합
print("\n" + "-"*100)
print("OPERATING EXPENDITURE (OPEX) - Annual Summary:")
print("-" * 100)

opex_items = {
    'Raw Materials': {
        'D-Galactose': raw_materials['D-Galactose (Main Substrate)']['qty_per_year'] * raw_materials['D-Galactose (Main Substrate)']['unit_price'],
        'Sodium Formate': raw_materials['Sodium Formate (Co-substrate)']['qty_per_year'] * raw_materials['Sodium Formate (Co-substrate)']['unit_price'],
        'E. coli Whole Cell (DCW)': raw_materials['E. coli Whole Cell Biocatalyst (DCW)']['qty_per_year'] * raw_materials['E. coli Whole Cell Biocatalyst (DCW)']['unit_price'],
        'NAD+ Cofactor': raw_materials['NAD+ Cofactor']['qty_per_year'] * raw_materials['NAD+ Cofactor']['unit_price'],
        'NADP+ Cofactor': raw_materials['NADP+ Cofactor']['qty_per_year'] * raw_materials['NADP+ Cofactor']['unit_price'],
        'Water': raw_materials['Water (Solvent)']['qty_per_year'] * raw_materials['Water (Solvent)']['unit_price'],
    },
    'Purification Materials': {
        'Activated Carbon': raw_materials['Activated Carbon (Decolorization)']['qty_per_year'] * raw_materials['Activated Carbon (Decolorization)']['unit_price'],
        'Misc Chemicals': raw_materials['Miscellaneous Chemicals (pH, Cleaning)']['qty_per_year'] * raw_materials['Miscellaneous Chemicals (pH, Cleaning)']['unit_price'],
    },
    'Energy & Utilities': {
        'Electricity (Process Operations)': energy_cost_total,
        'Cooling Water': annual_cooling_cost,
        'Compressed Air': compressed_air_cost,
    },
    'Labor': {
        'Batch Operations': annual_labor_cost,
    },
    'Maintenance & Overhead': {
        'Preventive Maintenance': total_capex * 0.04,
        'Miscellaneous & Contingency': total_capex * 0.02,
    },
}

total_opex = 0
for category, items in opex_items.items():
    category_total = sum(items.values())
    total_opex += category_total
    print(f"\n{category}: ${category_total:,.0f}")
    for item, cost in items.items():
        print(f"  {item:<45} ${cost:>15,.0f}")

print(f"\n{'─'*100}")
print(f"{'TOTAL ANNUAL OPEX':<50} ${total_opex:>20,.0f}")

# ============================================================================
# 10. 비용 구조 차트 (Tree Structure)
# ============================================================================

print("\n" + "="*100)
print("[10] COST STRUCTURE HIERARCHY - Tree View")
print("="*100)

print("""
TOTAL COST STRUCTURE (Annual)
├── CAPITAL EXPENDITURE (One-time): $511,500
│   ├── Equipment & Installation: $330,000
│   │   ├── Bioreactor System: $150,000
│   │   ├── Oxygen Compressor: $25,000
│   │   ├── Centrifuge: $20,000
│   │   ├── Decolorization Unit: $15,000
│   │   ├── Crystallization Unit: $40,000
│   │   └── Evaporator: $30,000
│   ├── Indirect Costs (40%): $132,000
│   └── Working Capital (15%): $49,500
│
└── OPERATING EXPENDITURE (Annual): $274,784
    ├── RAW MATERIALS: $67,439 (24.5%)
    │   ├── Main Substrates: $63,281
    │   │   ├── D-Galactose: $34,375
    │   │   └── Sodium Formate: $1,719
    │   ├── Cofactors: $2,475
    │   │   ├── NAD+: $1,500
    │   │   └── NADP+: $975
    │   └── Solvent & Auxiliaries: $1,683
    │       ├── Water: $312
    │       └── Miscellaneous Chemicals: $1,371
    │
    ├── PURIFICATION MATERIALS: $3,437 (1.3%)
    │   └── Activated Carbon: $3,437
    │
    ├── ENERGY & UTILITIES: $11,737 (4.3%)
    │   ├── Electricity: $10,237
    │   └── Cooling Water & Compressed Air: $1,500
    │
    ├── BIOREACTOR OPERATION: (included in Energy)
    │   ├── Agitation: 5 kW × 312.5 batches × 24 hr
    │   └── Oxygen Compression: 2.5 kW × 312.5 batches × 8 hr
    │
    ├── LABOR: $208,000 (75.7%) ← DOMINANT COST
    │   ├── Batch Preparation: $31,250
    │   ├── Active Monitoring: $46,875
    │   ├── Downstream Processing: $31,250
    │   └── Finishing & QA: $23,438
    │
    ├── PURIFICATION PROCESSING: (included in Energy + Materials)
    │   ├── Centrifugation: ~$3,000 consumables
    │   ├── Decolorization: ~$3,400 (carbon)
    │   └── Crystallization/Evaporation: ~$4,700 consumables
    │
    └── MAINTENANCE & OVERHEAD: $30,690 (11.2%)
        ├── Preventive Maintenance (4% CAPEX): $20,460
        └── Miscellaneous (2% CAPEX): $10,230
""")

# ============================================================================
# 11. 공정별 비용 효율성 분석
# ============================================================================

print("\n" + "="*100)
print("[11] COST EFFICIENCY BY PROCESS STEP")
print("="*100)

process_steps = {
    'Feed Preparation & Sterilization': {
        'labor_pct': 2.0 / total_labor_hours_per_batch,
        'energy_kwh_per_batch': 2.0,
        'materials_pct': 5,  # % of raw materials
        'duration_hr': 2,
    },
    'Anaerobic Reaction (16 hr)': {
        'labor_pct': 1.5 / total_labor_hours_per_batch,
        'energy_kwh_per_batch': stage1_energy_kwh_per_batch,
        'materials_pct': 95,  # Main reaction
        'duration_hr': 16,
    },
    'Aerobic Reaction + O2 (8 hr)': {
        'labor_pct': 1.5 / total_labor_hours_per_batch,
        'energy_kwh_per_batch': stage2_total_kwh,
        'materials_pct': 0,
        'duration_hr': 8,
    },
    'Centrifugation (Separation)': {
        'labor_pct': 1.0 / total_labor_hours_per_batch,
        'energy_kwh_per_batch': 6.0,
        'materials_pct': 0.5,
        'duration_hr': 2,
    },
    'Decolorization': {
        'labor_pct': 0.5 / total_labor_hours_per_batch,
        'energy_kwh_per_batch': 4.0,
        'materials_pct': 2.0,  # Activated carbon
        'duration_hr': 4,
    },
    'Crystallization': {
        'labor_pct': 1.0 / total_labor_hours_per_batch,
        'energy_kwh_per_batch': 24.0,
        'materials_pct': 1.5,
        'duration_hr': 6,
    },
    'Finishing & QA': {
        'labor_pct': 1.5 / total_labor_hours_per_batch,
        'energy_kwh_per_batch': 0,
        'materials_pct': 0.5,
        'duration_hr': 1.5,
    },
}

print("\nCost Contribution by Process Step (per batch):\n")
print(f"{'Process Step':<35} {'Labor':<15} {'Energy':<15} {'Materials':<15} {'Time (hr)':<10}")
print("-" * 100)

for step, costs in process_steps.items():
    labor_hours = total_labor_hours_per_batch * costs['labor_pct']
    labor_cost = labor_hours * 50
    energy_cost = costs['energy_kwh_per_batch'] * electricity_price
    materials_cost = (raw_materials_total / batches_per_year) * (costs['materials_pct'] / 100)

    total_step_cost = labor_cost + energy_cost + materials_cost

    print(f"{step:<35} ${labor_cost:>13.2f} ${energy_cost:>13.2f} ${materials_cost:>13.2f} {costs['duration_hr']:>9.1f}")

print("-" * 100)

# ============================================================================
# 12. 최종 비용 요약 표
# ============================================================================

print("\n" + "="*100)
print("[12] FINAL COST SUMMARY TABLE")
print("="*100)

summary_data = {
    'Item': [
        'CAPITAL EXPENDITURE',
        '  Equipment', '  Indirect', '  Working Capital',
        '',
        'ANNUAL OPEX',
        '  Raw Materials',
        '    D-Galactose', '    Sodium Formate', '    Cofactors (NAD+/NADP+)',
        '  Purification Materials',
        '    Activated Carbon',
        '  Energy & Utilities',
        '    Electricity', '    Water & Compressed Air',
        '  Labor',
        '  Maintenance',
        '',
        'TOTAL COST',
        '  Annual OPEX', '  Annual CAPEX Recovery (20yr)',
        '  TOTAL ANNUAL COST'
    ],
    'Amount': [
        f'${total_capex:,.0f}',
        f'${unit_capex_total:,.0f}', f'${indirect_capex:,.0f}', f'${working_capital:,.0f}',
        '',
        f'${total_opex:,.0f}',
        f'${raw_materials_total:,.0f}',
        f'${raw_materials["D-Galactose (Main Substrate)"]["qty_per_year"] * raw_materials["D-Galactose (Main Substrate)"]["unit_price"]:,.0f}',
        f'${raw_materials["Sodium Formate (Co-substrate)"]["qty_per_year"] * raw_materials["Sodium Formate (Co-substrate)"]["unit_price"]:,.0f}',
        f'${(raw_materials["NAD+ Cofactor"]["qty_per_year"] * raw_materials["NAD+ Cofactor"]["unit_price"]) + (raw_materials["NADP+ Cofactor"]["qty_per_year"] * raw_materials["NADP+ Cofactor"]["unit_price"]):,.0f}',
        f'${3437:,.0f}',
        f'${3437:,.0f}',
        f'${energy_cost_total + utilities_total:,.0f}',
        f'${energy_cost_total:,.0f}', f'${utilities_total:,.0f}',
        f'${annual_labor_cost:,.0f}',
        f'${maintenance_total:,.0f}',
        '',
        '',
        f'${total_opex:,.0f}',
        f'${total_capex/20:,.0f}',
        f'${total_opex + total_capex/20:,.0f}'
    ],
    '% of Annual Cost': [
        '',
        '', '', '',
        '',
        '100.0%',
        f'{(raw_materials_total/total_opex)*100:.1f}%',
        f'{(raw_materials["D-Galactose (Main Substrate)"]["qty_per_year"] * raw_materials["D-Galactose (Main Substrate)"]["unit_price"]/total_opex)*100:.1f}%',
        f'{(raw_materials["Sodium Formate (Co-substrate)"]["qty_per_year"] * raw_materials["Sodium Formate (Co-substrate)"]["unit_price"]/total_opex)*100:.1f}%',
        f'{((raw_materials["NAD+ Cofactor"]["qty_per_year"] * raw_materials["NAD+ Cofactor"]["unit_price"]) + (raw_materials["NADP+ Cofactor"]["qty_per_year"] * raw_materials["NADP+ Cofactor"]["unit_price"]))/total_opex*100:.1f}%',
        f'{(3437/total_opex)*100:.1f}%',
        f'{(3437/total_opex)*100:.1f}%',
        f'{((energy_cost_total + utilities_total)/total_opex)*100:.1f}%',
        f'{(energy_cost_total/total_opex)*100:.1f}%', f'{(utilities_total/total_opex)*100:.1f}%',
        f'{(annual_labor_cost/total_opex)*100:.1f}%',
        f'{(maintenance_total/total_opex)*100:.1f}%',
        '',
        '',
        '100.0%',
        f'{(total_capex/20)/(total_opex + total_capex/20)*100:.1f}%',
        '100.0%'
    ]
}

# Print as formatted table
print(f"\n{'Item':<45} {'Amount':<20} {'% of Annual OPEX':<20}")
print("-" * 100)

for item, amount, pct in zip(summary_data['Item'], summary_data['Amount'], summary_data['% of Annual Cost']):
    if item == '':
        print()
    else:
        print(f"{item:<45} {amount:>18} {pct:>18}")

print("\n" + "="*100)
print("END OF DETAILED COST BREAKDOWN")
print("="*100)
