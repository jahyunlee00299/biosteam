# -*- coding: utf-8 -*-
"""
D-Tagatose Production Process Units

Simple process unit implementations for D-Tagatose production.
Uses experimental/literature-based conversion rates with economic analysis.

Units:
- Step 1: AcidHydrolysis (Route B only)
- Step 2: Neutralization (Route B only)
- Step 2.5: AnionExchange (Route B only)
- Step 3: BiocatalysisReactor (both routes)
- Step 4: CellSeparator
- Step 5: Decolorization
- Step 6: Desalting
- Step 7: Dryer

Author: Claude AI
Date: 2026-02-12
"""

from biosteam import Unit, Stream

__all__ = (
    'AcidHydrolysis',
    'Neutralization',
    'AnionExchange',
    'BiocatalysisReactor',
    'CellSeparator',
    'Decolorization',
    'Desalting',
    'Dryer',
)


class AcidHydrolysis(Unit):
    """
    Step 1: Acid Hydrolysis of Algae Biomass (Route B only)

    Converts polysaccharides in algae biomass to D-Galactose using H2SO4.

    Inlet: Algae biomass + water + H2SO4
    Outlet: D-Galactose solution (acidic)
    """

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        # Process parameters (from D_TAGATOSE_PROCESS_OVERVIEW.md)
        self.conversion = 0.85  # 85% yield (algae → D-Galactose)
        self.temperature = 130  # °C
        self.time = 0.5  # hrs
        self.acid_cost_per_batch = 0.40  # $/kg algae

    def _run(self):
        """Material balance: Algae → D-Galactose"""
        # Input: Algae biomass
        feed = self.ins[0]
        algae_mass = feed.imass['Algae']  # kg/hr

        # Output: D-Galactose solution (85% conversion)
        product = self.outs[0]
        product.imass['D-Galactose'] = algae_mass * 0.70 * self.conversion  # 70% galactose in algae
        product.imass['Glucose'] = algae_mass * 0.115 * self.conversion  # 11.5% glucose
        product.imass['LevulinicAcid'] = algae_mass * 0.13 * (1 - self.conversion)  # Byproduct
        product.imass['FormicAcid'] = algae_mass * 0.05 * (1 - self.conversion)  # Byproduct
        product.imass['H2SO4'] = feed.imass.get('H2SO4', 0)  # Acid passthrough

    def _design(self):
        """Equipment sizing"""
        self.volume = 1000  # L (standard batch)
        self.power_utility.consume(0.5)  # kW (heating)

    def _cost(self):
        """Capital and operating costs"""
        # Equipment cost (acid hydrolysis reactor)
        self.purchase_cost = 80000  # $ (1000L reactor with heating)

        # Operating cost is handled in tagatose_route_economics.py


class Neutralization(Unit):
    """
    Step 2: Neutralization and Filtration (Route B only)

    Neutralizes excess H2SO4 with NaOH and removes solid residues.

    Inlet: Acidic D-Galactose solution
    Outlet: Neutral D-Galactose solution (pH 6-7)
    """

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        self.conversion = 0.92  # 92% recovery (acid solution → neutral solution)
        self.temperature = 25  # °C
        self.neutralization_cost_per_batch = 0.25  # $/kg algae

    def _run(self):
        """Material balance: Acidic solution → Neutral solution"""
        feed = self.ins[0]

        # Main product: D-Galactose (92% recovery)
        product = self.outs[0]
        product.imass['D-Galactose'] = feed.imass.get('D-Galactose', 0) * self.conversion
        product.imass['Glucose'] = feed.imass.get('Glucose', 0) * self.conversion

        # Some organic acids remain (to be removed in Step 2.5)
        product.imass['LevulinicAcid'] = feed.imass.get('LevulinicAcid', 0) * 0.9  # 90% remain
        product.imass['FormicAcid'] = feed.imass.get('FormicAcid', 0) * 0.9
        product.imass['SO4'] = feed.imass.get('H2SO4', 0) * 0.5  # SO4²⁻ remains as salt
        product.imass['Na'] = feed.imass.get('H2SO4', 0) * 0.3  # Na⁺ from NaOH

    def _design(self):
        """Equipment sizing"""
        self.volume = 1000  # L
        self.power_utility.consume(0.3)  # kW (filtration)

    def _cost(self):
        """Capital and operating costs"""
        self.purchase_cost = 50000  # $ (filtration unit)


class AnionExchange(Unit):
    """
    Step 2.5: Anion Exchange Resin Treatment (Route B only)

    Removes SO4²⁻, levulinic acid, formic acid byproducts.
    Improves downstream biocatalysis efficiency.

    Inlet: Neutral D-Galactose solution (with anion byproducts)
    Outlet: Clean D-Galactose solution (SO4²⁻ < 1%)
    """

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        self.removal_efficiency = 0.99  # 99% removal of SO4²⁻, org acids
        self.resin_cost_per_batch = 370.0  # $ (from route economics)

    def _run(self):
        """Material balance: Remove anion byproducts"""
        feed = self.ins[0]

        product = self.outs[0]

        # Main products pass through
        product.imass['D-Galactose'] = feed.imass.get('D-Galactose', 0)
        product.imass['Glucose'] = feed.imass.get('Glucose', 0)
        product.imass['Na'] = feed.imass.get('Na', 0)

        # Anion byproducts removed (90% efficiency in this model)
        product.imass['SO4'] = feed.imass.get('SO4', 0) * (1 - self.removal_efficiency)
        product.imass['LevulinicAcid'] = feed.imass.get('LevulinicAcid', 0) * (1 - self.removal_efficiency)
        product.imass['FormicAcid'] = feed.imass.get('FormicAcid', 0) * (1 - self.removal_efficiency)

    def _design(self):
        """Equipment sizing"""
        self.volume = 1000  # L
        self.power_utility.consume(0.2)  # kW

    def _cost(self):
        """Capital and operating costs"""
        self.purchase_cost = 50000  # $ (anion exchange column)


class BiocatalysisReactor(Unit):
    """
    Step 3: Whole Cell Biocatalysis

    Converts D-Galactose to D-Tagatose using E. coli whole cells.
    Core reaction: D-Galactose → D-Tagatose (via L-ribulose isomerase)

    Inlet: D-Galactose solution + E. coli cells + cofactors (NAD+/NADP+)
    Outlet: D-Tagatose solution + residual D-Galactose + E. coli cells

    Key assumptions:
    - 98% conversion rate (experimental/literature based)
    - Cofactors are recycled (not tracked here)
    - No complex kinetic modeling
    """

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        # Process parameters
        self.conversion = 0.98  # 98% conversion (experimental)
        self.temperature = 37  # °C
        self.time = 16  # hrs (16h anaerobic + 8h aerobic + overhead)
        self.cell_loading = 20  # g/L (20 kg DCW per 1000L)

        # Equipment cost (from tagatose_economics.py)
        self._reactor_cost = 225000  # $ for 1000L bioreactor
        self._agitation_power = 3.0  # kW

    def _run(self):
        """Material balance: D-Galactose → D-Tagatose"""
        feed = self.ins[0]

        # Input D-Galactose
        galactose_in = feed.imass.get('D-Galactose', 0)  # kg/hr

        # Main product: D-Tagatose (98% conversion)
        product = self.outs[0]
        product.imass['D-Tagatose'] = galactose_in * self.conversion
        product.imass['D-Galactose'] = galactose_in * (1 - self.conversion)  # Unreacted

        # Byproducts and other components pass through
        product.imass['Glucose'] = feed.imass.get('Glucose', 0)
        product.imass['E.coli'] = feed.imass.get('E.coli', 0)
        product.imass['Na'] = feed.imass.get('Na', 0)
        product.imass['SO4'] = feed.imass.get('SO4', 0)

        # Cofactors consumed (not tracked in mass balance, handled separately)
        # This is simplified: actual cofactor recovery would be more complex

    def _design(self):
        """Equipment sizing"""
        self.volume = 1000  # L (standard batch)

        # Agitation, aeration, cooling
        self.power_utility.consume(self._agitation_power)  # kW

    def _cost(self):
        """Capital and operating costs"""
        self.purchase_cost = self._reactor_cost

        # Operating costs (E. coli, cofactors) handled in tagatose_route_economics.py


class CellSeparator(Unit):
    """
    Step 4: Cell Removal

    Removes E. coli cells via centrifugation or microfiltration.

    Inlet: D-Tagatose solution + E. coli cells
    Outlet: Cell-free D-Tagatose solution
    """

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        self.removal_efficiency = 0.98  # 98% cell removal
        self.separation_cost = 0.001  # $/kg product

    def _run(self):
        """Material balance: Remove cells"""
        feed = self.ins[0]

        product = self.outs[0]

        # Main products pass through
        product.imass['D-Tagatose'] = feed.imass.get('D-Tagatose', 0)
        product.imass['D-Galactose'] = feed.imass.get('D-Galactose', 0)
        product.imass['Glucose'] = feed.imass.get('Glucose', 0)
        product.imass['Na'] = feed.imass.get('Na', 0)
        product.imass['SO4'] = feed.imass.get('SO4', 0)

        # E. coli cells removed (98% removal)
        product.imass['E.coli'] = feed.imass.get('E.coli', 0) * (1 - self.removal_efficiency)

    def _design(self):
        """Equipment sizing"""
        self.power_utility.consume(2.0)  # kW (centrifuge)

    def _cost(self):
        """Capital and operating costs"""
        self.purchase_cost = 25000  # $ (centrifuge)


class Decolorization(Unit):
    """
    Step 5: Decolorization

    Removes brown color and pigments using activated carbon.

    Inlet: D-Tagatose solution
    Outlet: Colorless D-Tagatose solution
    """

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        self.recovery = 0.96  # 96% product recovery (4% loss on carbon)
        self.carbon_cost = 0.01  # $/kg product

    def _run(self):
        """Material balance: Remove color"""
        feed = self.ins[0]

        product = self.outs[0]

        # Main products (96% recovery)
        product.imass['D-Tagatose'] = feed.imass.get('D-Tagatose', 0) * self.recovery
        product.imass['D-Galactose'] = feed.imass.get('D-Galactose', 0) * self.recovery
        product.imass['Na'] = feed.imass.get('Na', 0)
        product.imass['SO4'] = feed.imass.get('SO4', 0)

    def _design(self):
        """Equipment sizing"""
        self.power_utility.consume(0.5)  # kW (mixing, heating)

    def _cost(self):
        """Capital and operating costs"""
        self.purchase_cost = 20000  # $ (activated carbon unit)


class Desalting(Unit):
    """
    Step 6: Desalting (Ion Exchange)

    Removes Na⁺ and SO₄²⁻ ions using ion exchange resins.
    Route A: Cation exchanger only
    Route B: Cation exchanger (SO4²⁻ already removed in Step 2.5)

    Inlet: D-Tagatose solution + salts
    Outlet: High-purity D-Tagatose solution
    """

    def __init__(self, ID='', ins=None, outs=None, route='A', **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        self.route = route  # 'A' or 'B'
        self.removal_efficiency = 0.94  # 94% salt removal
        self.resin_cost_per_batch = 500.0  # $ (cation exchanger)

    def _run(self):
        """Material balance: Remove salts"""
        feed = self.ins[0]

        product = self.outs[0]

        # Main products (94% recovery after salt removal)
        product.imass['D-Tagatose'] = feed.imass.get('D-Tagatose', 0) * self.removal_efficiency
        product.imass['D-Galactose'] = feed.imass.get('D-Galactose', 0) * self.removal_efficiency

        # Salts largely removed
        product.imass['Na'] = feed.imass.get('Na', 0) * 0.05  # 95% removal
        product.imass['SO4'] = feed.imass.get('SO4', 0) * 0.05  # 95% removal

    def _design(self):
        """Equipment sizing"""
        self.power_utility.consume(1.0)  # kW (pumping through resins)

    def _cost(self):
        """Capital and operating costs"""
        self.purchase_cost = 50000  # $ (ion exchange columns)


class Dryer(Unit):
    """
    Step 7: Drying

    Converts D-Tagatose solution to solid powder via direct drying.
    Uses fluid bed dryer: 50-80°C, 12-30 hours.

    Inlet: D-Tagatose solution
    Outlet: D-Tagatose powder (>98% purity, <5% moisture)
    """

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        self.recovery = 0.95  # 95% solid recovery
        self.moisture_content = 0.03  # 3% final moisture
        self.temperature = 65  # °C
        self.drying_time = 20  # hrs

    def _run(self):
        """Material balance: Solution → Powder"""
        feed = self.ins[0]

        product = self.outs[0]

        # Main products: D-Tagatose powder (95% recovery)
        tagatose_solid = feed.imass.get('D-Tagatose', 0) * self.recovery

        # Final powder mass (account for moisture)
        product.imass['D-Tagatose'] = tagatose_solid / (1 - self.moisture_content)
        product.imass['Water'] = product.imass['D-Tagatose'] * self.moisture_content

        # Trace impurities
        product.imass['D-Galactose'] = feed.imass.get('D-Galactose', 0) * 0.01  # <1% unreacted

    def _design(self):
        """Equipment sizing"""
        # Fluid bed dryer
        self.power_utility.consume(3.0)  # kW (heating)

    def _cost(self):
        """Capital and operating costs"""
        self.purchase_cost = 80000  # $ (fluid bed dryer)
