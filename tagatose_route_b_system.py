#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Route B System: Red Algae Biomass + Step 2.5 (Step 1-7)

Process flow:
  Red Algae (in) → [Step 1-7] → D-Tagatose powder (out)

  Step 1: AcidHydrolysis (algae → D-Galactose, 85% yield)
  Step 2: Neutralization (acidic sol → neutral sol, 92% recovery)
  Step 2.5: AnionExchange (remove SO4²⁻ byproducts)
  Step 3: BiocatalysisReactor (D-Gal → D-Tag, 98% conversion)
  Step 4: CellSeparator (remove E. coli)
  Step 5: Decolorization (remove color)
  Step 6: Desalting (remove Na+)
  Step 7: Dryer (solution → powder)

Production target:
  - Batch: 141 kg Red Algae → 110 kg D-Gal → 80 kg D-Tagatose
  - Annual: 22,575 kg/year (at $10/kg = $225k revenue)
  - Breakeven: $42.30/kg (OPEX only)
  - Step 1-2 yield: 78.2% (85% × 92%)

Author: Claude AI
Date: 2026-02-12
"""

import sys
sys.path.insert(0, r'C:\Users\Jahyun\PycharmProjects\biosteam')

# Set thermo
import thermosteam as tmo
try:
    from biosteam.thermo.tagatose_thermo import tagatose_thermo
    tmo.settings.set_thermo(tagatose_thermo)
except:
    print("Warning: Could not load tagatose_thermo, using default")
    tmo.settings.set_thermo(tmo.Thermo(['Water', 'Glucose', 'H2SO4', 'NaOH'], cache=True))

from biosteam import System, Stream
from biosteam.units.tagatose_process_units import (
    AcidHydrolysis, Neutralization, AnionExchange,
    BiocatalysisReactor, CellSeparator, Decolorization, Desalting, Dryer
)

# ============================================================================
# 1. Define Input Streams
# ============================================================================

# Step 1 Input: Red algae biomass
# TODO: 사용자가 확인/수정할 사항
#   - 홍조류 141 kg/hr이 맞는가? (110 kg D-Gal ÷ 0.782 yield)
feed_algae = Stream(
    'AlgaeBiomass',
    # Algae=141.0,  # Thermo DB에 추가되면 활성화
    Water=0.0,       # 보충
    price=0.75,      # $/kg
)

# Step 1 Input: Sulfuric acid
feed_acid = Stream(
    'H2SO4_for_hydrolysis',
    H2SO4=14.1,      # kg/hr (141 kg 홍조류 × 0.1)
    price=0.05,      # $/kg
)

# Step 2 Input: Sodium hydroxide
feed_base = Stream(
    'NaOH_for_neutralization',
    NaOH=8.81,       # kg/hr
    price=0.50,      # $/kg
)

# Step 3 Input: E. coli cells
feed_cells = Stream(
    'E.coli_cells',
    # E.coli=20.0,  # Thermo DB에 추가되면 활성화
    price=50.0,      # $/kg DCW
)

# Step 3 Input: Sodium formate
feed_formate = Stream(
    'SodiumFormate',
    # SodiumFormate=44.0,  # Thermo DB에 추가되면 활성화
    price=0.25,      # $/kg
)

# ============================================================================
# 2. Create Units - Step 1-2 (Route B specific)
# ============================================================================

# Step 1: Acid Hydrolysis
U201 = AcidHydrolysis(
    ID='U201_AcidHydrolysis',
    ins=(feed_algae, feed_acid),
    outs='U201_outlet',
)

# Step 2: Neutralization
U202 = Neutralization(
    ID='U202_Neutralization',
    ins=U201-0,
    outs='U202_outlet',
)

# Step 2.5: Anion Exchange
U2_5 = AnionExchange(
    ID='U2_5_AnionExchange',
    ins=U202-0,
    outs='U2_5_outlet',
)

# ============================================================================
# 3. Create Units - Step 3-7 (Common with Route A)
# ============================================================================

# Simple mixer to combine streams before biocatalysis
# (In actual BioSTEAM, would use biosteam.units.Mixer)
# For simplicity, assume U2_5 outlet has D-Galactose from algae processing

# Step 3: Biocatalysis
U301 = BiocatalysisReactor(
    ID='U301_Biocatalysis',
    ins=(U2_5-0, feed_cells, feed_formate),
    outs='U301_outlet',
)

# Step 4: Cell Separator
U302 = CellSeparator(
    ID='U302_CellSeparator',
    ins=U301-0,
    outs='U302_outlet',
)

# Step 5: Decolorization
U303 = Decolorization(
    ID='U303_Decolorization',
    ins=U302-0,
    outs='U303_outlet',
)

# Step 6: Desalting
U304 = Desalting(
    ID='U304_Desalting',
    ins=U303-0,
    outs='U304_outlet',
    route='B',  # Route B: Step 2.5에서 음이온 제거됨, 양이온만
)

# Step 7: Dryer
U305 = Dryer(
    ID='U305_Dryer',
    ins=U304-0,
    outs='D-Tagatose_powder',
)

# Final product
product = U305-0
product.price = 10.0  # $/kg

# ============================================================================
# 4. Create System
# ============================================================================

route_b_system = System(
    ID='Route_B_System',
    units=(U201, U202, U2_5, U301, U302, U303, U304, U305),
)

# ============================================================================
# 5. Run Simulation & Report
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("ROUTE B SYSTEM: RED ALGAE BIOMASS + STEP 2.5 (Step 1-7)")
    print("=" * 80)

    try:
        # Run simulation
        route_b_system.simulate()

        print("\n[INPUT STREAMS]")
        print(f"  Red algae: {feed_algae.F_mass:.1f} kg/hr (expected 141)")
        print(f"  H2SO4: {feed_acid.F_mass:.1f} kg/hr")
        print(f"  NaOH: {feed_base.F_mass:.1f} kg/hr")
        if feed_cells.F_mass > 0:
            print(f"  E. coli: {feed_cells.F_mass:.1f} kg/hr")
        if feed_formate.F_mass > 0:
            print(f"  Sodium Formate: {feed_formate.F_mass:.1f} kg/hr")

        print("\n[PROCESS UNITS]")
        for i, unit in enumerate(route_b_system.units):
            if unit.outs:
                outlet = unit.outs[0]
                print(f"\n  Step {i+1} - {unit.ID}:")
                print(f"    Outlet mass: {outlet.F_mass:.1f} kg/hr")
                if hasattr(unit, 'power_utility'):
                    print(f"    Power: {unit.power_utility.power:.2f} kW")
                if hasattr(unit, 'purchase_cost'):
                    print(f"    Capital cost: ${unit.purchase_cost:,.0f}")

        print("\n[FINAL PRODUCT]")
        if product.F_mass > 0:
            print(f"  D-Tagatose powder: {product.F_mass:.1f} kg/hr")
            print(f"  Price: ${product.price:.2f}/kg")
            print(f"  Revenue: ${product.F_mass * product.price:,.0f}/hr")
        else:
            print("  No product (스트림 연결 문제 확인 필요)")

        print("\n[SYSTEM SUMMARY]")
        total_capex = sum(u.purchase_cost for u in route_b_system.units if hasattr(u, 'purchase_cost'))
        total_power = sum(u.power_utility.power for u in route_b_system.units if hasattr(u, 'power_utility'))

        print(f"  Total units: {len(route_b_system.units)}")
        print(f"  Total capital cost: ${total_capex:,.0f}")
        print(f"  Total power: {total_power:.2f} kW")

        print("\n[EXPECTED vs ACTUAL]")
        print(f"  Expected algae input: 141 kg/hr")
        print(f"  Actual algae input: {feed_algae.F_mass:.1f} kg/hr")
        print(f"  Expected D-Galactose after Step 1-2: ~110 kg/hr (78.2% yield)")
        print(f"  Expected final product: ~80 kg/hr (Step 3-7 수율 ~75%)")
        if product.F_mass > 0:
            print(f"  Actual product: {product.F_mass:.1f} kg/hr")

    except Exception as e:
        print(f"\nError during simulation: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("END OF SIMULATION")
    print("=" * 80)

    print("\n[ROUTE A vs ROUTE B 비교 예상]")
    print("Route A (정제 D-Galactose):")
    print("  - 연간 생산: 27,500 kg/year")
    print("  - 손익분기점: $31.57/kg")
    print("  - 프로세스: Step 3-7만 (간단함)")
    print("\nRoute B (홍조류 원물):")
    print("  - 연간 생산: 22,575 kg/year (-17.9%)")
    print("  - 손익분기점: $42.30/kg")
    print("  - 프로세스: Step 1-7 (복잡함, 비용 증가)")

    print("\n[TODO: 사용자가 수정해야 할 항목]")
    print("1. 홍조류 입력값 (141 kg/hr) 검증")
    print("2. Step 1-2 수율 (78.2%) 확인")
    print("3. 최종 생성물이 예상값과 일치하는지 확인")
    print("4. Route A와의 CAPEX 차이 분석")
