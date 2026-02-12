# BioSTEAM Unit Implementation Requirements

## Overview

Complete implementation of D-Tagatose production process units in BioSTEAM with full thermodynamic and economic modeling.

**Current Status**: Unit structure defined, Thermo setup incomplete
**Target**: Fully functional Route A/B systems with simulation and economic analysis

---

## 1. Thermodynamic Setup (Required)

### 1.1 Create Custom Thermo Database

**File**: `biosteam/thermo/tagatose_thermo.py`

```python
import thermosteam as tmo

# Define all chemicals needed for D-Tagatose process
chemicals = [
    # Water & solvents
    'Water',

    # Sugars & products
    'D-Glucose',      # 180.16 g/mol
    'D-Galactose',    # 180.16 g/mol
    'D-Tagatose',     # 180.16 g/mol (same MW as galactose)
    'Glucose',        # Alias for D-Glucose

    # Process chemicals
    'H2SO4',          # Sulfuric acid (for hydrolysis)
    'NaOH',           # Sodium hydroxide (for neutralization)
    'Na2SO4',         # Sodium sulfate (product of neutralization)

    # Byproducts & impurities
    'LevulinicAcid',  # C5H8O3, 116.12 g/mol (hydrolysis byproduct)
    'FormicAcid',     # CH2O2, 46.03 g/mol (hydrolysis byproduct)
    'HCl',            # Hydrochloric acid (trace)
    'NaCl',           # Sodium chloride (trace)

    # Biocatalyst & cofactors
    'E.coli',         # Whole cells (dry cell weight)
    'NADplus',        # NAD+ cofactor (nicotinamide)
    'NADPplus',       # NADP+ cofactor

    # Other materials
    'SodiumFormate',  # CHO2Na, 68.01 g/mol (electron donor)
    'ActivatedCarbon', # For decolorization
]

# Create Thermo object
def get_tagatose_thermo():
    """Get D-Tagatose production thermo object"""
    thermo = tmo.Thermo(chemicals, cache=True)

    # Set properties for key compounds (can be estimated or literature-based)
    # For simplicity, use water-like properties for aqueous solutions
    # In production, use NIST/ASPEN data

    return thermo

# Export
tagatose_thermo = get_tagatose_thermo()
tmo.settings.set_thermo(tagatose_thermo)
```

### 1.2 Chemical Properties Required

For each chemical, need:
- **Molecular weight** (g/mol)
- **Density** (kg/m³)
- **Heat capacity** (J/kg·K)
- **Enthalpy of formation** (J/mol)
- **Solubility** in water

**Data Sources**:
- NIST Chemistry WebBook
- PubChem
- ChemSpider
- Aspen Plus Property Packages

**Simplified Approach** (for this implementation):
- Use water properties for aqueous sugars
- Assume constant density 1000-1100 kg/m³
- Assume constant heat capacity 4.18 kJ/kg·K (like water)

---

## 2. Stream Definition (Required)

### 2.1 Route A Input Streams

```python
import thermosteam as tmo
from biosteam import Stream

# 1. Purified D-Galactose feed
feed_galactose = Stream(
    'D-Galactose_feed',
    D_Galactose=110.0,  # kg/hr (110 g/L × 1000 L)
    price=2.0,          # $/kg
    units='kg/hr',
)

# 2. E. coli cells
feed_cells = Stream(
    'E.coli_cells',
    E_coli=20.0,        # kg/hr DCW
    price=50.0,         # $/kg
)

# 3. Sodium formate (electron donor)
feed_formate = Stream(
    'SodiumFormate',
    SodiumFormate=44.0, # kg/hr
    price=0.25,         # $/kg
)

# 4. Cofactors (traced separately if needed)
feed_cofactors = Stream(
    'Cofactors',
    NADplus=1.0,        # mol/hr (1 mM × 1000 L)
    NADPplus=0.1,       # mol/hr (0.1 mM × 1000 L)
    price=0.0,          # Handled in economic model
)
```

### 2.2 Route B Input Streams

```python
# 1. Red algae biomass
feed_algae = Stream(
    'AlgaeBiomass',
    Algae=141.0,        # kg/hr (need custom chemical)
    price=0.75,         # $/kg
)

# 2. Sulfuric acid (for hydrolysis)
feed_acid = Stream(
    'H2SO4_hydrolysis',
    H2SO4=14.1,         # kg/hr
    price=0.05,         # $/kg
)

# 3. Sodium hydroxide (for neutralization)
feed_base = Stream(
    'NaOH_neutralization',
    NaOH=8.81,          # kg/hr
    price=0.50,         # $/kg
)

# 4-6. Same as Route A (cells, formate, cofactors)
```

---

## 3. Unit Implementation Details (Required)

### 3.1 BiocatalysisReactor (Step 3) - Priority 1

**Key Methods to Implement**:

#### `_run()` - Material Balance
```python
def _run(self):
    """
    Calculate outlet streams based on inlet streams and conversion

    Key equation:
    D-Galactose → D-Tagatose (98% conversion)

    Stoichiometry:
    - 1 mol D-Galactose → 1 mol D-Tagatose
    - MW same (180.16 g/mol)
    - Mass balance: In_galactose × 0.98 = Out_tagatose
    """

    feed = self.ins[0]  # D-Galactose solution

    # Extract inlet masses
    galactose_in = feed.imass['D-Galactose']  # kg/hr
    water_in = feed.imass['Water']

    # Product calculation
    tagatose_out = galactose_in * self.conversion  # 98%
    galactose_unreacted = galactose_in * (1 - self.conversion)  # 2%

    # Set outlet stream
    product = self.outs[0]
    product.imass['D-Tagatose'] = tagatose_out
    product.imass['D-Galactose'] = galactose_unreacted
    product.imass['Water'] = water_in

    # Cofactors and cells pass through (simplified)
    product.imass['E.coli'] = feed.imass.get('E.coli', 0)
```

#### `_design()` - Equipment Sizing
```python
def _design(self):
    """
    Size equipment based on production requirements

    Key parameters:
    - Volume: 1000 L (standard batch)
    - Power: agitation (3 kW) + aeration (2 kW) + cooling (2 kW)
    - Residence time: 16 hrs (anaerobic) + 8 hrs (aerobic)
    - Temperature: 37°C (maintained)
    """

    # Batch volume
    self.volume = 1000  # L

    # Power consumption
    agitation_power = 3.0  # kW
    aeration_power = 2.0   # kW
    cooling_power = 2.0    # kW

    self.power_utility.consume(agitation_power + aeration_power + cooling_power)

    # Calculate capital cost based on volume
    # Cost correlation: C = base_cost × (V / V_ref)^0.6
    base_cost = 150000  # $ for 500L
    volume_ratio = self.volume / 500
    self.cost_scaled = base_cost * (volume_ratio ** 0.6)
```

#### `_cost()` - Capital & Operating Costs
```python
def _cost(self):
    """
    Estimate equipment purchase cost

    Breakdown:
    - 1000L bioreactor vessel: $150k
    - Agitation/control: $50k
    - Temperature/pH control: $25k
    - Total: $225k
    """

    self.purchase_cost = 225000  # $

    # Utility costs handled in tagatose_route_economics.py
    # (E. coli, cofactors, utilities)
```

---

### 3.2 Other Units (Priority 2-5)

#### CellSeparator (Step 4)
```python
Required calculations:
- Cell removal efficiency: 98%
- Product loss: ~2% (absorbed on cells, residual liquid)
- Power: centrifugation 2 kW
- Equipment cost: $25k (centrifuge)

Equation:
  outlet_mass = inlet_mass × 0.98
```

#### Decolorization (Step 5)
```python
Required calculations:
- Carbon adsorption capacity: ~10 g/L
- Recovery: 96% (4% loss on carbon)
- Power: 0.5 kW (mixing)
- Equipment cost: $20k

Equation:
  outlet_mass = inlet_mass × 0.96
```

#### Desalting (Step 6)
```python
Required calculations:
- Ion removal: 94% (Na+ and SO4²⁻)
- Product recovery: 94%
- Resin regeneration cost: Handled in economic model
- Power: 1 kW (pumping through resin)
- Equipment cost: $50k

Equations:
  outlet_tagatose = inlet_tagatose × 0.94
  outlet_salts = inlet_salts × 0.05  (95% removal)
```

#### Dryer (Step 7)
```python
Required calculations:
- Moisture content: 3% final (wet basis)
- Recovery: 95% (5% loss in dryer)
- Drying time: 20 hrs at 65°C
- Power: 3 kW heating
- Equipment cost: $80k

Energy balance:
  Heat_required = mass_water × latent_heat_vaporization
  = (inlet_mass × water_fraction) × 2256 kJ/kg

Equation:
  outlet_powder = inlet_liquid × recovery × (1 / (1 - moisture_final))
```

---

## 4. System Integration (Required)

### 4.1 Route A System

**File**: `tagatose_route_a_system.py` (UPDATED)

```python
# Components needed:
1. Thermo setup (import from tagatose_thermo.py)
2. Stream definitions (Route A inputs)
3. Unit instantiation (U301-U305, 5 units)
4. System creation
5. Simulation call
6. Results reporting

# Key integration points:
- U301.outs[0] → U302.ins[0]  (stream connection)
- All units share same thermo object
- Each unit updates outlet T, P, composition
```

### 4.2 Route B System

**File**: `tagatose_route_b_system.py` (UPDATED)

```python
# Additional components:
1. Step 1: AcidHydrolysis (U201)
2. Step 2: Neutralization (U202)
3. Step 2.5: AnionExchange (U2_5)
4. Mixer: Combine D-Galactose + cells + formate before U301

# Stream connections:
Feed_algae → U201 → U202 → U2_5 → Mixer → U301 → ... → U305
```

---

## 5. Validation & Testing (Required)

### 5.1 Unit Tests

```python
# File: tests/test_tagatose_units.py

def test_biocatalysis_reactor():
    """Test BiocatalysisReactor material balance"""

    # Create inlet stream
    feed = Stream('feed', D_Galactose=100, Water=900)

    # Create unit
    reactor = BiocatalysisReactor(
        ID='test_reactor',
        ins=feed,
        outs='product',
        conversion=0.98
    )

    # Simulate
    reactor._run()

    # Assert
    assert reactor.outs[0].imass['D-Tagatose'] == 98  # kg/hr
    assert reactor.outs[0].imass['D-Galactose'] == 2   # kg/hr
    assert abs(reactor.outs[0].F_mass - 902) < 0.1    # Mass conservation
```

### 5.2 System Tests

```python
def test_route_a_system():
    """Test complete Route A system"""

    # Create and simulate
    sys = create_route_a_system()
    sys.simulate()

    # Check results
    product = sys.streams['D-Tagatose_powder']

    # Assert expected production
    assert product.F_mass > 0  # Has product
    assert product.imass['D-Tagatose'] / product.F_mass > 0.95  # >95% purity

    # Check energy balance
    total_power = sum(u.power_utility.power for u in sys.units)
    assert total_power < 15  # <15 kW total

    # Check cost
    total_capex = sum(u.purchase_cost for u in sys.units)
    assert total_capex > 500000  # >$500k
```

### 5.3 Economics Validation

```python
def test_economics_integration():
    """Verify Unit costs match RouteAEconomics"""

    # Run system
    sys = create_route_a_system()
    sys.simulate()
    system_capex = sum(u.purchase_cost for u in sys.units)

    # Run economics model
    route_a = RouteAEconomics()
    model_capex = route_a.calculate_capex()['Equipment Cost']

    # Should be similar (within 5%)
    assert abs(system_capex - model_capex) / model_capex < 0.05
```

---

## 6. Documentation Required

### 6.1 Code Documentation

- Docstrings for all Unit classes (parameters, equations, assumptions)
- Process flow diagrams (ASCII art in docstrings)
- Material balance examples
- Literature references for conversion rates

### 6.2 User Guide

- How to create Route A/B systems
- How to modify parameters (conversion, temperature, etc.)
- How to interpret results
- How to extend for other scenarios (Scale-up, Route C, etc.)

---

## 7. Timeline & Effort Estimate

| Task | Effort | Days |
|------|--------|------|
| 7.1 Thermo setup & chemicals | 2 hrs | 0.25 |
| 7.2 Stream definitions | 1 hr | 0.1 |
| 7.3 Unit implementation (5 units) | 8 hrs | 1 |
| 7.4 System integration (A + B) | 4 hrs | 0.5 |
| 7.5 Testing & validation | 4 hrs | 0.5 |
| 7.6 Documentation | 3 hrs | 0.4 |
| **Total** | **22 hrs** | **~3 days** |

---

## 8. Risks & Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Thermo DB incomplete | High | Use simplified properties (water-like) |
| Unit power calculation inaccurate | Medium | Use literature values + validation tests |
| Stream connections fail | Medium | Start with single unit, add sequentially |
| BioSTEAM API changes | Low | Use version pinning |
| Economic model mismatch | Medium | Add unit tests comparing to RouteAEconomics |

---

## 9. Success Criteria

✅ **Must Have**:
1. All 8 units implemented and tested
2. Route A system simulates without errors
3. Route B system simulates without errors
4. Material balance conserved (inlet = outlet ±1%)
5. Production matches economic model (±5%)
6. CAPEX matches economic model (±10%)

✅ **Should Have**:
7. Power consumption realistic (<15 kW)
8. Energy balance validated
9. Complete documentation
10. Example outputs and use cases

✅ **Nice to Have**:
11. Sensitivity analysis within BioSTEAM
12. Optimization for max production
13. Integration with biosteam.evaluation

---

## 10. Next Steps

1. **Create `biosteam/thermo/tagatose_thermo.py`**
   - Define chemicals list
   - Test with simple stream
   - Validate molecular weights

2. **Implement BiocatalysisReactor in detail**
   - Code all three methods (_run, _design, _cost)
   - Unit test
   - Document equations

3. **Implement remaining 4 units**
   - CellSeparator, Decolorization, Desalting, Dryer
   - Sequential testing

4. **Create Route A/B systems**
   - Connect units
   - Simulate
   - Compare with economic model

5. **Full documentation & deployment**

---

## References

- **BioSTEAM Documentation**: https://biosteam.readthedocs.io/
- **Thermosteam**: https://github.com/yoelcortes/thermosteam
- **D-Tagatose Process**: D_TAGATOSE_PROCESS_OVERVIEW.md
- **Economic Model**: tagatose_route_economics.py

---

**Author**: Claude AI
**Date**: 2026-02-12
**Status**: Requirements Document
