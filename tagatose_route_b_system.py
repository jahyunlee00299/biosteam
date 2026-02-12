#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Route B System: Red Algae Biomass + Step 2.5 (Step 1-7)

Process flow:
  Red Algae Biomass (in) → [Step 1-7] → D-Tagatose powder (out)

  Step 1: AcidHydrolysis (algae → D-Galactose)
  Step 2: Neutralization (acidic sol → neutral sol)
  Step 2.5: AnionExchange (remove SO4²⁻, org acids)
  Step 3: BiocatalysisReactor (D-Gal → D-Tag)
  Step 4: CellSeparator (remove E. coli)
  Step 5: Decolorization (remove color)
  Step 6: Desalting (remove Na+)
  Step 7: Dryer (solution → powder)

Author: Claude AI
Date: 2026-02-12
"""

import sys
sys.path.insert(0, r'C:\Users\Jahyun\PycharmProjects\biosteam')

import thermosteam as tmo
from biosteam import System, Stream

# Set a simple thermo object
tmo.settings.set_thermo(tmo.Thermo(
    ['Water', 'EthylAcetate', 'Ethanol', 'Glucose'],  # Simple components
    cache=True
))
from biosteam.units.tagatose_process_units import (
    AcidHydrolysis, Neutralization, AnionExchange,
    BiocatalysisReactor, CellSeparator, Decolorization, Desalting, Dryer
)

# ============================================================================
# 1. Define Streams
# ============================================================================

# Input: Red algae biomass (141 kg/hr for 110 kg D-Galactose output after Step 1-2)
feed_algae = Stream(
    'Algae_in',
    Algae=141.0,  # kg/hr (141 kg algae → 110 kg D-Gal after 78.2% yield)
    price=0.75,  # $/kg
)

# Acid for hydrolysis
feed_acid = Stream(
    'H2SO4_in',
    H2SO4=14.1,  # kg/hr (0.1 kg H2SO4 per kg algae)
    price=0.05,  # $/kg
)

# Base for neutralization
feed_base = Stream(
    'NaOH_in',
    NaOH=8.81,  # kg/hr
    price=0.50,  # $/kg
)

# E. coli cells
feed_cells = Stream(
    'E.coli_in',
    E_coli=20.0,  # kg/hr
    price=50.0,  # $/kg DCW
)

# Sodium formate (electron donor)
feed_formate = Stream(
    'Sodium_Formate_in',
    Glucose=44.0,  # kg/hr (placeholder)
    price=0.25,  # $/kg
)

# ============================================================================
# 2. Create Units
# ============================================================================

# Step 1: Acid Hydrolysis
U201 = AcidHydrolysis(
    ID='U201',
    ins=(feed_algae, feed_acid),
    outs='hydrolysis_product',
)

# Step 2: Neutralization
U202 = Neutralization(
    ID='U202',
    ins=U201-0,
    outs='neutralization_product',
)

# Step 2.5: Anion Exchange
U2_5 = AnionExchange(
    ID='U2_5',
    ins=U202-0,
    outs='anion_exchanged_product',
)

# Step 3: Biocatalysis (combine with cofactors and cells)
# Need to mix the D-Galactose solution with cofactors and cells
from biosteam import Mixer

mixer = Mixer(ID='Mixer_in', ins=(U2_5-0, feed_cells, feed_formate), outs='mixed_for_biocatalysis')

U301 = BiocatalysisReactor(
    ID='U301',
    ins=mixer-0,
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
    route='B',  # Cation exchanger only (anion already removed in Step 2.5)
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

route_b_system = System(
    ID='Route_B_System',
    units=(U201, U202, U2_5, mixer, U301, U302, U303, U304, U305),
)

# ============================================================================
# 4. Simulate and Report
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("ROUTE B SYSTEM: RED ALGAE BIOMASS + STEP 2.5 (Step 1-7)")
    print("=" * 80)

    # Run simulation
    route_b_system.simulate()

    print("\n[INPUT STREAMS]")
    print(f"  Red algae biomass: {feed_algae.F_mass:.1f} kg/hr")
    print(f"  H2SO4 (acid hydrolysis): {feed_acid.F_mass:.1f} kg/hr")
    print(f"  NaOH (neutralization): {feed_base.F_mass:.1f} kg/hr (note: not yet added to stream)")
    print(f"  E. coli: {feed_cells.F_mass:.1f} kg/hr")
    print(f"  Sodium Formate: {feed_formate.F_mass:.1f} kg/hr")

    print("\n[PROCESS UNITS]")
    for unit in route_b_system.units:
        print(f"\n  {unit.ID}: {unit.__class__.__name__}")
        if hasattr(unit, 'ins') and unit.ins:
            total_in = sum(inlet.F_mass for inlet in unit.ins)
            print(f"    Inlet mass: {total_in:.1f} kg/hr")
        if unit.outs:
            print(f"    Outlet mass: {unit.outs[0].F_mass:.1f} kg/hr")
        if hasattr(unit, 'power_utility'):
            print(f"    Power: {unit.power_utility.power:.2f} kW")
        if hasattr(unit, 'purchase_cost'):
            print(f"    Capital cost: ${unit.purchase_cost:,.0f}")

    print("\n[OUTPUT STREAM]")
    print(f"  D-Tagatose powder: {product.F_mass:.1f} kg/hr")
    tagatose_mass = product.imass.get('D-Tagatose', 0)
    if tagatose_mass > 0:
        purity = tagatose_mass / product.F_mass * 100
        print(f"  Purity (D-Tagatose): {purity:.1f}%")
    else:
        print(f"  Purity (D-Tagatose): 0.0% (no product)")
    print(f"  Price: ${product.price:.2f}/kg")
    print(f"  Revenue: ${product.F_mass * product.price:,.0f}/hr")

    print("\n[SYSTEM SUMMARY]")
    total_units = len([u for u in route_b_system.units if hasattr(u, 'purchase_cost')])
    total_capex = sum(u.purchase_cost for u in route_b_system.units if hasattr(u, 'purchase_cost'))
    total_power = sum(u.power_utility.power for u in route_b_system.units if hasattr(u, 'power_utility'))

    print(f"  Total units: {len(route_b_system.units)}")
    print(f"  Total capital cost: ${total_capex:,.0f}")
    print(f"  Total power: {total_power:.2f} kW")

    print("\n[COMPARISON WITH ROUTE A (Expected)]")
    print(f"  Route A production: ~110 kg D-Gal/batch → ~110 kg Tagatose")
    print(f"  Route B production: ~110 kg D-Gal/batch → ~90.3 kg Tagatose (-17.9%)")
    print(f"  Reason: Step 1-2 losses (78.2% yield) and downstream purification losses")

    print("\n" + "=" * 80)
