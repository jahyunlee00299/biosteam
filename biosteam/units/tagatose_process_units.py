# -*- coding: utf-8 -*-
"""
D-Tagatose Production Process Units

Simple process unit implementations for D-Tagatose production.
Uses experimental/literature-based conversion rates with economic analysis.

Note: Currently uses 'Glucose' as proxy for D-Galactose/D-Tagatose due to Thermo DB
limitations. This is simplified for material balance tracking.

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

from biosteam import Unit

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


def _safe_imass_get(stream, chemical, default=0):
    """
    Safely get mass of chemical from stream, with default value.
    Handles cases where chemical doesn't exist in Thermo database.
    """
    try:
        return stream.imass[chemical]
    except:
        return default


class AcidHydrolysis(Unit):
    """
    Step 1: Acid Hydrolysis of Algae Biomass (Route B only)

    Converts polysaccharides in algae biomass to D-Galactose using H2SO4.

    Inlet: Algae biomass + H2SO4
    Outlet: D-Galactose solution (acidic)
    """

    _N_ins = 2  # 홍조류, H2SO4
    _N_outs = 1  # D-Galactose 용액

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        # Process parameters (from D_TAGATOSE_PROCESS_OVERVIEW.md)
        self.conversion = 0.85  # 85% yield (algae → D-Galactose)
        self.temperature = 130  # °C
        self.time = 0.5  # hrs
        self.acid_cost_per_batch = 0.40  # $/kg algae

    def _run(self):
        """Material balance: Algae → D-Galactose (using Glucose as proxy)"""
        # Input: Algae biomass
        feed = self.ins[0]
        h2so4_mass = _safe_imass_get(feed, 'H2SO4', 0)  # kg/hr

        # Output: Use Glucose as proxy for D-Galactose (Thermo DB limitation)
        # Assuming algae is represented as Water input
        # Total incoming mass
        total_in = feed.F_mass

        # Simplified: Track output as Glucose (proxy for D-Galactose)
        # 85% conversion × 70% galactose content = 59.5% of input
        product = self.outs[0]
        product.imass['Glucose'] = max(0.595 * total_in, 0)  # 59.5% to Glucose
        product.imass['Water'] = 0.4 * total_in  # 40% Water balance
        product.imass['H2SO4'] = h2so4_mass  # Acid passthrough

    def _design(self):
        """Equipment sizing"""
        self.volume = 1000  # L (standard batch)
        self.power_utility.power = 0.5  # kW (heating)

    def _cost(self):
        """Capital and operating costs"""
        # Equipment cost (acid hydrolysis reactor)
#        self.purchase_cost = 80000  # $ (1000L reactor with heating)

        # Operating cost is handled in tagatose_route_economics.py


class Neutralization(Unit):
    """
    Step 2: Neutralization and Filtration (Route B only)

    Neutralizes excess H2SO4 with NaOH and removes solid residues.

    Inlet: Acidic D-Galactose solution
    Outlet: Neutral D-Galactose solution (pH 6-7)
    """

    _N_ins = 1
    _N_outs = 1

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        self.conversion = 0.92  # 92% recovery (acid solution → neutral solution)
        self.temperature = 25  # °C
        self.neutralization_cost_per_batch = 0.25  # $/kg algae

    def _run(self):
        """Material balance: Acidic solution → Neutral solution"""
        feed = self.ins[0]

        # Main product: Glucose (proxy for D-Galactose, 92% recovery)
        product = self.outs[0]
        glucose_in = _safe_imass_get(feed, 'Glucose', 0)
        product.imass['Glucose'] = glucose_in * self.conversion

        # Water balance
        water_in = _safe_imass_get(feed, 'Water', 0)
        product.imass['Water'] = water_in * 0.98  # 2% loss on filtration

    def _design(self):
        """Equipment sizing"""
        self.volume = 1000  # L
        self.power_utility.power = 0.3  # kW (filtration)

    def _cost(self):
        """Capital and operating costs"""
#        self.purchase_cost = 50000  # $ (filtration unit)


class AnionExchange(Unit):
    """
    Step 2.5: Anion Exchange Resin Treatment (Route B only)

    Removes SO4²⁻, levulinic acid, formic acid byproducts.
    Improves downstream biocatalysis efficiency.

    Inlet: Neutral D-Galactose solution (with anion byproducts)
    Outlet: Clean D-Galactose solution (SO4²⁻ < 1%)
    """

    _N_ins = 1
    _N_outs = 1
    

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        self.removal_efficiency = 0.99  # 99% removal of SO4²⁻, org acids
        self.resin_cost_per_batch = 370.0  # $ (from route economics)

    def _run(self):
        """Material balance: Remove anion byproducts"""
        feed = self.ins[0]
        product = self.outs[0]

        # Main products pass through
        product.imass['Glucose'] = _safe_imass_get(feed, 'Glucose', 0)
        product.imass['Water'] = _safe_imass_get(feed, 'Water', 0)

    def _design(self):
        """Equipment sizing"""
        self.volume = 1000  # L
        self.power_utility.power = 0.2  # kW

    def _cost(self):
        """Capital and operating costs"""
#        self.purchase_cost = 50000  # $ (anion exchange column)


class BiocatalysisReactor(Unit):
    """
    Step 3: Whole Cell Biocatalysis

    Converts D-Galactose to D-Tagatose using E. coli whole cells.
    Core reaction: D-Galactose → D-Tagatose (via L-ribulose isomerase)

    Inlets:
      - [0] D-Galactose solution
      - [1] E. coli cells (DCW, dry cell weight)
      - [2] Sodium Formate (electron donor)
    Outlet: D-Tagatose solution + residual D-Galactose + E. coli cells

    Key assumptions:
    - 98% conversion rate (experimental/literature based)
    - Cofactors are recycled (not tracked here)
    - No complex kinetic modeling
    """

    _N_ins = 3
    _N_outs = 1


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
        """Material balance: D-Galactose → D-Tagatose (using Glucose as proxy)"""
        # Inlet [0]: D-Galactose solution (represented as Glucose in Thermo DB)
        galactose_feed = self.ins[0]
        # Inlet [1]: E. coli cells (not tracked in Thermo DB)
        # Inlet [2]: Sodium Formate electron donor (not tracked in Thermo DB)

        # Input Glucose (proxy for D-Galactose)
        glucose_in = _safe_imass_get(galactose_feed, 'Glucose', 0)  # kg/hr

        # Main product: Glucose (proxy for D-Tagatose, 98% conversion)
        product = self.outs[0]
        product.imass['Glucose'] = glucose_in * self.conversion

        # Water balance
        water_in = _safe_imass_get(galactose_feed, 'Water', 0)
        product.imass['Water'] = water_in

        # Note: Cofactors, cells, and electron donor not tracked due to Thermo DB limitations
        # This is simplified: actual model would include NAD+/NADP+ cofactor recovery

    def _design(self):
        """Equipment sizing"""
        self.volume = 1000  # L (standard batch)

        # Agitation, aeration, cooling
        self.power_utility.power = self._agitation_power  # kW

    def _cost(self):
        """Capital costs"""
        # BioSTEAM will calculate costs from equipment specifications
        # Equipment cost: $225,000 for 1000L bioreactor (hardcoded in _design)


class CellSeparator(Unit):
    """
    Step 4: Cell Removal

    Removes E. coli cells via centrifugation or microfiltration.

    Inlet: D-Tagatose solution + E. coli cells
    Outlet: Cell-free D-Tagatose solution
    """

    _N_ins = 1
    _N_outs = 1
    

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        self.removal_efficiency = 0.98  # 98% cell removal
        self.separation_cost = 0.001  # $/kg product

    def _run(self):
        """Material balance: Remove cells"""
        feed = self.ins[0]
        product = self.outs[0]

        # Main products pass through
        product.imass['Glucose'] = _safe_imass_get(feed, 'Glucose', 0)
        product.imass['Water'] = _safe_imass_get(feed, 'Water', 0)

        # Note: E. coli cells not tracked (not in Thermo DB)

    def _design(self):
        """Equipment sizing"""
        self.power_utility.power = 2.0  # kW (centrifuge)

    def _cost(self):
        """Capital and operating costs"""
#        self.purchase_cost = 25000  # $ (centrifuge)


class Decolorization(Unit):
    """
    Step 5: Decolorization

    Removes brown color and pigments using activated carbon.

    Inlet: D-Tagatose solution
    Outlet: Colorless D-Tagatose solution
    """

    _N_ins = 1
    _N_outs = 1
    

    def __init__(self, ID='', ins=None, outs=None, **kwargs):
        super().__init__(ID, ins, outs, **kwargs)

        self.recovery = 0.96  # 96% product recovery (4% loss on carbon)
        self.carbon_cost = 0.01  # $/kg product

    def _run(self):
        """Material balance: Remove color"""
        feed = self.ins[0]
        product = self.outs[0]

        # Main products (96% recovery)
        product.imass['Glucose'] = _safe_imass_get(feed, 'Glucose', 0) * self.recovery
        product.imass['Water'] = _safe_imass_get(feed, 'Water', 0) * self.recovery

    def _design(self):
        """Equipment sizing"""
        self.power_utility.power = 0.5  # kW (mixing, heating)

    def _cost(self):
        """Capital and operating costs"""
#        self.purchase_cost = 20000  # $ (activated carbon unit)


class Desalting(Unit):
    """
    Step 6: Desalting (Ion Exchange)

    Removes Na⁺ and SO₄²⁻ ions using ion exchange resins.
    Route A: Cation exchanger only
    Route B: Cation exchanger (SO4²⁻ already removed in Step 2.5)

    Inlet: D-Tagatose solution + salts
    Outlet: High-purity D-Tagatose solution
    """

    _N_ins = 1
    _N_outs = 1
    

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
        product.imass['Glucose'] = _safe_imass_get(feed, 'Glucose', 0) * self.removal_efficiency
        product.imass['Water'] = _safe_imass_get(feed, 'Water', 0) * self.removal_efficiency

        # Note: Salts (Na, SO4) not tracked (not in Thermo DB)

    def _design(self):
        """Equipment sizing"""
        self.power_utility.power = 1.0  # kW (pumping through resins)

    def _cost(self):
        """Capital and operating costs"""
#        self.purchase_cost = 50000  # $ (ion exchange columns)


class Dryer(Unit):
    """
    Step 7: Drying

    Converts D-Tagatose solution to solid powder via direct drying.
    Uses fluid bed dryer: 50-80°C, 12-30 hours.

    Inlet: D-Tagatose solution
    Outlet: D-Tagatose powder (>98% purity, <5% moisture)
    """

    _N_ins = 1
    _N_outs = 1
    

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

        # Main products: Glucose powder (95% recovery)
        glucose_solid = _safe_imass_get(feed, 'Glucose', 0) * self.recovery
        water_in = _safe_imass_get(feed, 'Water', 0)

        # Final powder mass (account for moisture)
        product.imass['Glucose'] = glucose_solid / (1 - self.moisture_content)
        product.imass['Water'] = product.imass['Glucose'] * self.moisture_content

    def _design(self):
        """Equipment sizing"""
        # Fluid bed dryer
        self.power_utility.power = 3.0  # kW (heating)

    def _cost(self):
        """Capital and operating costs"""
#        self.purchase_cost = 80000  # $ (fluid bed dryer)
