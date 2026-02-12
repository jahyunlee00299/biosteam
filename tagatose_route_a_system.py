#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Route A System: Purified D-Galactose (Step 3-7)

Process flow:
  Purified D-Galactose (in) → [Step 3-7] → D-Tagatose powder (out)

  Step 3: BiocatalysisReactor (D-Gal → D-Tag, 98% conversion)
  Step 4: CellSeparator (remove E. coli, 98% removal)
  Step 5: Decolorization (remove color, 96% recovery)
  Step 6: Desalting (remove Na+/SO4²⁻, 94% recovery)
  Step 7: Dryer (solution → powder, 95% recovery)

Production target:
  - Batch: 110 kg D-Galactose → 90 kg D-Tagatose
  - Annual: 27,500 kg/year (at $10/kg = $275k revenue)
  - Breakeven: $31.57/kg (OPEX only)

Author: Claude AI
Date: 2026-02-12
"""

import sys
sys.path.insert(0, r'C:\Users\Jahyun\PycharmProjects\biosteam')

# Set thermo (필요시 사용자가 수정)
import thermosteam as tmo
try:
    from biosteam.thermo.tagatose_thermo import tagatose_thermo
    tmo.settings.set_thermo(tagatose_thermo)
except:
    print("Warning: Could not load tagatose_thermo, using default")
    tmo.settings.set_thermo(tmo.Thermo(['Water', 'Glucose', 'H2SO4', 'NaOH'], cache=True))

from biosteam import System, Stream
from biosteam.units.tagatose_process_units import (
    BiocatalysisReactor, CellSeparator, Decolorization, Desalting, Dryer
)

# ============================================================================
# 1. Define Input Streams (값은 나중에 사용자가 수정 가능)
# ============================================================================

# Input 1: Purified D-Galactose (represented as Glucose in Thermo DB)
# NOTE: Using Glucose as proxy for D-Galactose due to Thermo DB limitations
feed_galactose = Stream(
    'D-Galactose_feed',
    Glucose=110.0,   # kg/hr - D-Galactose proxy
    Water=890.0,     # kg/hr - solvent
    price=2.0,       # $/kg
)

# Input 2: E. coli cells
# NOTE: Not tracked in Thermo DB, but included for system definition
feed_cells = Stream(
    'E.coli_cells',
    # E.coli not in Thermo DB - mass tracked separately in economics
    price=50.0,      # $/kg DCW
)

# Input 3: Sodium formate (electron donor)
# NOTE: Not tracked in Thermo DB, but included for system definition
feed_formate = Stream(
    'SodiumFormate',
    # SodiumFormate not in Thermo DB - mass tracked separately
    price=0.25,      # $/kg
)

# ============================================================================
# 2. Create Units (값은 tagatose_process_units.py에 하드코드됨)
# ============================================================================

# Step 3: Biocatalysis Reactor
U301 = BiocatalysisReactor(
    ID='U301_Biocatalysis',
    ins=(feed_galactose, feed_cells, feed_formate),
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

# Step 6: Desalting (이온교환)
U304 = Desalting(
    ID='U304_Desalting',
    ins=U303-0,
    outs='U304_outlet',
    route='A',  # Route A: 양이온만
)

# Step 7: Dryer
U305 = Dryer(
    ID='U305_Dryer',
    ins=U304-0,
    outs='D-Tagatose_powder',
)

# 최종 생성물
product = U305-0
product.price = 10.0  # $/kg (시장 가격 기본값)

# ============================================================================
# 3. Create System
# ============================================================================

route_a_system = System(
    ID='Route_A_System',
    path=(U301, U302, U303, U304, U305),
)

# ============================================================================
# 4. Run Simulation & Report
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("ROUTE A SYSTEM: PURIFIED D-GALACTOSE (Step 3-7)")
    print("=" * 80)

    try:
        # Run simulation
        route_a_system.simulate()

        print("\n[INPUT STREAMS]")
        print(f"  D-Galactose feed: {feed_galactose.F_mass:.1f} kg/hr")
        if feed_cells.F_mass > 0:
            print(f"  E. coli: {feed_cells.F_mass:.1f} kg/hr")
        if feed_formate.F_mass > 0:
            print(f"  Sodium Formate: {feed_formate.F_mass:.1f} kg/hr")

        print("\n[PROCESS UNITS & OUTLET]")
        for unit in route_a_system.units:
            if unit.outs:
                outlet = unit.outs[0]
                print(f"\n  {unit.ID}:")
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
        total_capex = sum(u.purchase_cost for u in route_a_system.units if hasattr(u, 'purchase_cost'))
        total_power = sum(u.power_utility.power for u in route_a_system.units if hasattr(u, 'power_utility'))

        print(f"  Total units: {len(route_a_system.units)}")
        print(f"  Total capital cost: ${total_capex:,.0f}")
        print(f"  Total power: {total_power:.2f} kW")

        print("\n[EXPECTED vs ACTUAL]")
        print(f"  Expected D-Galactose: 110 kg/hr")
        print(f"  Actual input: {feed_galactose.F_mass:.1f} kg/hr")
        print(f"  Expected final product: ~82 kg/hr (Step 3-7 수율 ~75%)")
        if product.F_mass > 0:
            print(f"  Actual product: {product.F_mass:.1f} kg/hr")

    except Exception as e:
        print(f"\nError during simulation: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("END OF SIMULATION")
    print("=" * 80)

    print("\n[TODO: 사용자가 수정해야 할 항목]")
    print("1. tagatose_thermo.py의 화학물질 이름이 Thermo DB와 일치하는지 확인")
    print("2. 스트림 입력값 (D-Galactose, E.coli, Sodium Formate) 검증")
    print("3. Unit의 기본값 (conversion, power, capex) 확인")
    print("4. 최종 생성물이 예상값과 일치하는지 확인")
