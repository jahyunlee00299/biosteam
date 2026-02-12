#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Route A System: Purified D-Galactose (Step 3-7)

Process flow:
  Purified D-Galactose (in) → [Step 3-7] → D-Tagatose powder (out)

  Step 3: BiocatalysisReactor (D-Gal → D-Tag)
  Step 4: CellSeparator (remove E. coli)
  Step 5: Decolorization (remove color)
  Step 6: Desalting (remove Na+, SO4²⁻)
  Step 7: Dryer (solution → powder)

Author: Claude AI
Date: 2026-02-12
"""

import sys
sys.path.insert(0, r'C:\Users\Jahyun\PycharmProjects\biosteam')

import thermosteam as tmo
from biosteam import System, Stream

# Set a simple thermo object for water (we're not doing detailed thermodynamics)
tmo.settings.set_thermo(tmo.Thermo(
    ['Water', 'EthylAcetate', 'Ethanol', 'Glucose'],  # Simple components
    cache=True
))
from biosteam.units.tagatose_process_units import (
    BiocatalysisReactor, CellSeparator, Decolorization, Desalting, Dryer
)

# ============================================================================
# 1. Define Streams
# ============================================================================

# Input: Purified D-Galactose solution
feed_galactose = Stream(
    'D-Galactose_in',
    D_Galactose=110.0,  # kg/hr (110 kg per 1000L batch at 110 g/L)
    price=2.0,  # $/kg
)

# Co-factors (not tracked in mass balance, but needed)
feed_cofactors = Stream(
    'Cofactors_in',
    price=0.0,  # Handled in economic model
)

# E. coli cells (assumed already produced)
feed_cells = Stream(
    'E.coli_in',
    E_coli=20.0,  # kg/hr (20 g/L × 1000L)
    price=50.0,  # $/kg DCW
)

# Sodium formate (electron donor for biocatalysis)
feed_formate = Stream(
    'Sodium_Formate_in',
    Glucose=44.0,  # kg/hr (placeholder, actual is formate)
    price=0.25,  # $/kg
)

# ============================================================================
# 2. Create Units
# ============================================================================

# Step 3: Biocatalysis
U301 = BiocatalysisReactor(
    ID='U301',
    ins=(feed_galactose, feed_cells, feed_formate),
    outs='biocatalysis_product',
)

# Step 4: Cell Separator
U302 = CellSeparator(
    ID='U302',
    ins=U301-0,
    outs='cell_free_product',
)

# Step 5: Decolorization
U303 = Decolorization(
    ID='U303',
    ins=U302-0,
    outs='decolorized_product',
)

# Step 6: Desalting
U304 = Desalting(
    ID='U304',
    ins=U303-0,
    outs='desalted_product',
    route='A',  # Cation exchanger only
)

# Step 7: Dryer
U305 = Dryer(
    ID='U305',
    ins=U304-0,
    outs='D-Tagatose_powder',
)

# Product stream
product = U305-0
product.price = 10.0  # $/kg (baseline market price)

# ============================================================================
# 3. Create System
# ============================================================================

route_a_system = System(
    ID='Route_A_System',
    units=(U301, U302, U303, U304, U305),
)

# ============================================================================
# 4. Simulate and Report
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("ROUTE A SYSTEM: PURIFIED D-GALACTOSE (Step 3-7)")
    print("=" * 80)

    # Run simulation
    route_a_system.simulate()

    print("\n[INPUT STREAMS]")
    print(f"  D-Galactose feed: {feed_galactose.F_mass:.1f} kg/hr")
    print(f"  E. coli: {feed_cells.F_mass:.1f} kg/hr")
    print(f"  Sodium Formate: {feed_formate.F_mass:.1f} kg/hr")

    print("\n[PROCESS UNITS]")
    for unit in route_a_system.units:
        print(f"\n  {unit.ID}: {unit.__class__.__name__}")
        print(f"    Inlet mass: {unit.ins[0].F_mass:.1f} kg/hr" if unit.ins else "    (no inlet)")
        if unit.outs:
            print(f"    Outlet mass: {unit.outs[0].F_mass:.1f} kg/hr")
        print(f"    Power: {unit.power_utility.power:.2f} kW")
        print(f"    Capital cost: ${unit.purchase_cost:,.0f}")

    print("\n[OUTPUT STREAM]")
    print(f"  D-Tagatose powder: {product.F_mass:.1f} kg/hr")
    print(f"  Purity (D-Tagatose): {product.imass.get('D-Tagatose', 0) / product.F_mass * 100:.1f}%")
    print(f"  Price: ${product.price:.2f}/kg")
    print(f"  Revenue: ${product.F_mass * product.price:,.0f}/hr")

    print("\n[SYSTEM SUMMARY]")
    print(f"  Total units: {len(route_a_system.units)}")
    print(f"  Total capital cost: ${sum(u.purchase_cost for u in route_a_system.units):,.0f}")
    print(f"  Total power: {sum(u.power_utility.power for u in route_a_system.units):.2f} kW")

    print("\n" + "=" * 80)
