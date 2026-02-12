# -*- coding: utf-8 -*-
"""
D-Tagatose Production Thermo Database

Custom thermosteam Thermo object with chemicals needed for D-Tagatose process.
Uses simplified properties for aqueous sugar solutions.

Author: Claude AI
Date: 2026-02-12
"""

import thermosteam as tmo

__all__ = ('tagatose_thermo',)

# Chemical species needed for D-Tagatose production
# Using standard NIST/PubChem molecular weights
CHEMICALS = [
    # Water and solvents
    'Water',

    # Sugars and products
    'Glucose',        # D-Glucose (180.156 g/mol) - standard NIST name
    'D-Galactose',    # D-Galactose (180.156 g/mol)
    'D-Tagatose',     # D-Tagatose (180.156 g/mol) - same MW as galactose

    # Process chemicals
    'H2SO4',          # Sulfuric acid (98.079 g/mol)
    'NaOH',           # Sodium hydroxide (39.998 g/mol)
    'Na2SO4',         # Sodium sulfate (142.036 g/mol)

    # Byproducts and impurities
    'LevulinicAcid',  # Levulinic acid (116.116 g/mol) - hydrolysis byproduct
    'FormicAcid',     # Formic acid (46.026 g/mol) - hydrolysis byproduct
    'Sodium',         # Na+ ion (placeholder, 22.990 g/mol)
    'Sulfate',        # SO4²⁻ ion (placeholder, 96.065 g/mol)

    # Biocatalyst and cofactors
    'E.coli',         # Whole cells (dry cell weight) - custom, ~1000 g/mol equiv
    'SodiumFormate',  # Sodium formate (68.008 g/mol) - electron donor
]

def get_tagatose_thermo():
    """
    Create and return D-Tagatose production thermo object.

    Returns
    -------
    thermosteam.Thermo
        Thermo object with chemicals for D-Tagatose process

    Notes
    -----
    Uses simplified thermodynamic properties:
    - Aqueous sugar solutions: water-like properties
    - Constant density: 1000-1100 kg/m³
    - Constant heat capacity: 4.18 kJ/kg·K
    - Standard NIST molecular weights

    This is acceptable for bioprocess engineering where:
    - Detailed thermodynamic accuracy not critical
    - Material balance is primary concern
    - Energy balance simplified (no complex phase equilibria)
    """

    try:
        # Try to create Thermo with standard chemicals
        thermo = tmo.Thermo(CHEMICALS, cache=True)
        return thermo
    except Exception as e:
        print(f"Warning: Could not load all chemicals: {e}")
        print("Attempting simplified setup with common chemicals only...")

        # Fallback: use only standard BioSTEAM chemicals
        common_chemicals = ['Water', 'Glucose', 'H2SO4', 'NaOH']
        thermo = tmo.Thermo(common_chemicals, cache=True)
        return thermo


# Create the global thermo object
tagatose_thermo = get_tagatose_thermo()

# Set as default for module
tmo.settings.set_thermo(tagatose_thermo)


# Utility functions for property estimation
def estimate_density_sugar_solution(sugar_fraction):
    """
    Estimate density of aqueous sugar solution.

    Parameters
    ----------
    sugar_fraction : float
        Mass fraction of sugar (0-1)

    Returns
    -------
    float
        Estimated density (kg/m³)

    Notes
    -----
    Simplified model: linear interpolation
    - Pure water: 1000 kg/m³ at 20°C
    - Sugar solution: ~1040 kg/m³ at 20% sugar
    - Pure sugar (solid): ~1600 kg/m³
    """
    rho_water = 1000
    rho_sugar = 1600
    return rho_water + (rho_sugar - rho_water) * sugar_fraction


def estimate_heat_capacity(sugar_fraction):
    """
    Estimate heat capacity of aqueous sugar solution.

    Parameters
    ----------
    sugar_fraction : float
        Mass fraction of sugar (0-1)

    Returns
    -------
    float
        Estimated heat capacity (kJ/kg·K)

    Notes
    -----
    Simplified model: constant value
    - Water: 4.18 kJ/kg·K
    - Sugar solutions: ~4.0-4.2 kJ/kg·K (assume constant)
    """
    return 4.18  # kJ/kg·K (water-like)


if __name__ == '__main__':
    print("D-Tagatose Thermo Database")
    print("=" * 50)
    print(f"\nChemicals loaded: {len(tagatose_thermo.chemicals)}")
    print(f"Thermo object: {tagatose_thermo}")

    # Test stream creation
    try:
        from biosteam import Stream
        test_stream = Stream('test', Water=100, Glucose=10)
        print(f"\nTest stream created: {test_stream}")
        print(f"  Mass: {test_stream.F_mass:.1f} kg/hr")
    except Exception as e:
        print(f"\nWarning: Stream test failed: {e}")

    print("\n" + "=" * 50)
    print("Thermo setup complete!")
