# -*- coding: utf-8 -*-
# BioSTEAM: The Biorefinery Simulation and Techno-Economic Analysis Modules
# Copyright (C) 2020-2024, Yoel Cortes-Pena <yoelcortes@gmail.com>
#
# This module is under the UIUC open-source license. See
# github.com/BioSTEAMDevelopmentGroup/biosteam/blob/master/LICENSE.txt
# for license details.
"""
Tagatose Production - Techno-Economic Analysis Module

Comprehensive economic analysis for D-Tagatose production:
- Capital expenditure (CAPEX)
- Operating expenditure (OPEX)
- Revenue analysis
- Profitability metrics (ROI, NPV, IRR, Payback period)

Author: Claude AI
"""

__all__ = ('TagatoseEconomicAnalysis',)


class TagatoseEconomicAnalysis:
    """
    타가토스 생산 공정 경제성 분석

    전체 공정의 자본 및 운영 비용, 수익성을 분석합니다.
    """

    def __init__(self, system=None, product_stream=None):
        """
        Parameters
        ----------
        system : System
            BioSTEAM System 객체
        product_stream : Stream
            최종 생성물 스트림
        """
        self.system = system
        self.product_stream = product_stream

        # 경제 파라미터 (2024-2025 시장 가격 기준)
        # D-Tagatose: $10/kg (bulk, 100-200+ MT), market range $8-10/kg
        self.tagatose_price = 10.0  # $/kg (2024-2025 실시장 가격)
        # D-Galactose: ~$2.0/kg (estimated from chemical supplier pricing)
        self.glucose_cost = 2.0    # $/kg (원료, D-Galactose)
        # Sodium Formate: ~$0.25/kg (industrial grade, Sept 2024: $250/MT)
        self.formate_cost = 0.25   # $/kg (원료, Sodium Formate)
        # E. coli Whole Cell Biocatalyst: ~$50/kg DCW (revised estimate)
        self.biocatalyst_cost = 50.0  # $/kg DCW (원료, E. coli 전세포 촉매)
        # Cofactors (NAD+/NADP+) - Tufvesson et al. (2011) Org. Process Res. Dev. bulk pricing
        self.nad_cost = 710.0      # $/mol (NAD+ 코팩터, bulk industrial)
        self.nadp_cost = 5000.0    # $/mol (NADP+ 코팩터, bulk industrial)
        self.electricity_price = 0.12  # $/kWh
        self.water_cost = 0.002    # $/L
        self.labor_cost = 50       # $/hr (운영 근로자)
        self.maintenance_factor = 0.04  # 4% of CAPEX/년

        # 프로젝트 파라미터
        self.project_life = 20     # 년
        self.discount_rate = 0.1   # 10% 할인율
        self.plant_capacity_factor = 0.85  # 85% 가동률
        self.production_hours_per_year = 7500  # hrs (85% × 365 × 24)

        # 결과 저장
        self.results = {}

    def calculate_capex(self):
        """
        자본 지출 (CAPEX) 계산

        각 유닛의 purchase_cost 합산 + 간접비

        Returns
        -------
        dict: 상세 CAPEX 분석
        """
        if not self.system:
            # System이 없을 경우 1000L 배치 반응기 기준 비용 추정 (optimized scale)
            # Equipment costs (NREL reference for scaled-up biorefinery)
            capex_breakdown = {}

            # Equipment costs (1000L bioreactor with downstream processing)
            # Scale-up factor: 1000L/500L = 2x volume, ~1.5x cost (power law 0.6)
            reactor_cost = 225000      # 1000L bioreactor + agitation (scaled from 150k)
            separator_cost = 25000     # Centrifuge (larger capacity)
            decolorization_cost = 20000  # Activated carbon unit (larger)
            crystallization_cost = 50000 # Crystallization unit (larger)
            evaporator_cost = 40000    # Vacuum evaporator (larger capacity)
            compressor_cost = 30000    # Oxygen compressor (higher flow for 1000L)
            piping_utilities = 60000   # Piping, utilities, instrumentation (scaled)

            total_equipment = (reactor_cost + separator_cost + decolorization_cost +
                             crystallization_cost + evaporator_cost + compressor_cost + piping_utilities)

            # Indirect costs (40% of equipment)
            indirect_factor = 0.4
            indirect_cost = total_equipment * indirect_factor

            # Working capital (15% of equipment)
            working_capital_factor = 0.15
            working_capital = total_equipment * working_capital_factor

            total_capex = total_equipment + indirect_cost + working_capital

            capex_breakdown['Equipment Cost'] = total_equipment
            capex_breakdown['Indirect Cost (40%)'] = indirect_cost
            capex_breakdown['Working Capital (15%)'] = working_capital
            capex_breakdown['Total CAPEX'] = total_capex

            return capex_breakdown

        capex_breakdown = {}
        total_purchase_cost = 0

        # 각 유닛의 구매 비용 합산
        for unit in self.system.units:
            unit_cost = unit.purchase_cost
            capex_breakdown[unit.ID] = unit_cost
            total_purchase_cost += unit_cost

        # 간접비 (설치, 엔지니어링, 예비 등)
        # 일반적 : 30-50% of equipment cost
        indirect_factor = 0.4
        indirect_cost = total_purchase_cost * indirect_factor

        # 자본 비용
        working_capital_factor = 0.15
        working_capital = total_purchase_cost * working_capital_factor

        total_capex = total_purchase_cost + indirect_cost + working_capital

        capex_breakdown['Equipment Cost'] = total_purchase_cost
        capex_breakdown['Indirect Cost (40%)'] = indirect_cost
        capex_breakdown['Working Capital (15%)'] = working_capital
        capex_breakdown['Total CAPEX'] = total_capex

        return capex_breakdown

    def calculate_opex_annual(self):
        """
        연간 운영 비용 (OPEX) 계산

        Returns
        -------
        dict: 상세 OPEX 분석
        """
        opex_breakdown = {}

        if self.system:
            # 1. 유틸리티 비용
            electricity_kWh_per_year = 0
            for unit in self.system.units:
                if hasattr(unit, 'power_utility'):
                    # 대략적 전력 소비 추정
                    pass

            # 추정: 반응기 공정 기본 전력
            # 교반, 냉각, 압축기 등
            estimated_electricity = 500  # kWh/년 (보수적 추정)
            electricity_cost = estimated_electricity * self.electricity_price
            opex_breakdown['Electricity'] = electricity_cost

            # 물 사용비 (500L 반응기, 냉각, 세척 등)
            water_consumption = 10000  # L/년 (추정)
            water_cost = water_consumption * self.water_cost
            opex_breakdown['Water'] = water_cost
        else:
            # system=None: 1000L 스케일 기준 유틸리티 추정
            # 교반기 (~3 kW) + 산소압축기 (~2 kW) + 냉각/가열 (~2 kW) + 다운스트림 (~3 kW) = ~10 kW 평균
            # 연간: 10 kW × 7500 hr/yr × 0.7 부하율 = 52,500 kWh/yr
            estimated_electricity_kWh = 10.0 * self.production_hours_per_year * 0.7
            electricity_cost = estimated_electricity_kWh * self.electricity_price
            opex_breakdown['Electricity'] = electricity_cost

            # 물 사용: 반응기 충진 (~1000L/batch) + 냉각수 (~500L/batch) + 세척 (~200L/batch)
            # 총 ~1700 L/batch × 312.5 batches/yr = 531,250 L/yr
            batches_per_year_util = self.production_hours_per_year / 24
            water_consumption_L = 1700 * batches_per_year_util
            water_cost = water_consumption_L * self.water_cost
            opex_breakdown['Water'] = water_cost

        # 2. 원료비
        # 1000L, 24hr 배치 기준 (보고서 기준)
        galactose_cost = 110 * self.glucose_cost  # 110 kg/batch (110 g/L × 1000L)
        formate_cost = 44.0 * self.formate_cost  # 44 kg/batch (5% 과량 adjusted)
        biocatalyst_cost = 20.0 * self.biocatalyst_cost  # 20 kg DCW/batch (20 g/L × 1000L, reduced from 50)
        # NAD+ NO RECOVERY: Complete consumption (100% makeup per batch)
        nad_cost = 1.0 * self.nad_cost  # 1.0 mol/batch (1 mM × 1000L), 회수 불가능하므로 100% 새로 추가
        nadp_cost = 0.1 * self.nadp_cost  # 0.1 mol/batch (0.1 mM × 1000L)

        # 연간 배치 수 (생산 시간 / 배치 시간)
        batches_per_year = self.production_hours_per_year / 24  # 24시간/배치 (16h 혐기성 + 8h 호기성)
        annual_galactose = galactose_cost * batches_per_year
        annual_formate = formate_cost * batches_per_year
        annual_biocatalyst = biocatalyst_cost * batches_per_year
        annual_nad = nad_cost * batches_per_year
        annual_nadp = nadp_cost * batches_per_year

        opex_breakdown['D-Galactose'] = annual_galactose
        opex_breakdown['Sodium Formate'] = annual_formate
        opex_breakdown['E. coli Whole Cell (DCW)'] = annual_biocatalyst
        opex_breakdown['NAD+ Cofactor (NO recovery - discarded)'] = annual_nad
        opex_breakdown['NADP+ Cofactor (NO recovery - discarded)'] = annual_nadp

        # 3. 노동비 (시간제 근로자 2명 FTE)
        # 실제 운영 시간: production_hours_per_year (7500 hr/yr)
        # 배치당 실제 개입 시간: ~2-4 시간 (모니터링 및 유지)
        # 2 FTE operators × 2080 hr/yr = 4160 operational hours
        actual_labor_hours_per_year = 2 * 2080  # 2 full-time operators
        annual_labor = actual_labor_hours_per_year * self.labor_cost
        opex_breakdown['Labor'] = annual_labor

        # 4. 유지보수비 (CAPEX의 4%)
        capex = self.calculate_capex().get('Total CAPEX', 1000000)
        maintenance = capex * self.maintenance_factor
        opex_breakdown['Maintenance'] = maintenance

        # 5. 기타 비용 (라이센스, 보험, 일반관리비 등)
        misc_cost = capex * 0.02  # 2% of CAPEX
        opex_breakdown['Miscellaneous'] = misc_cost

        total_opex = sum(v for k, v in opex_breakdown.items() if k != 'Total OPEX')
        opex_breakdown['Total Annual OPEX'] = total_opex

        return opex_breakdown

    def calculate_revenue_annual(self, product_concentration=None):
        """
        연간 판매 수익 계산

        Parameters
        ----------
        product_concentration : float, optional
            생성물 농도 (기본값: 34.375kg 타가토스/배치)

        Returns
        -------
        dict: 수익 분석
        """
        if product_concentration is None:
            product_concentration = 110.0  # kg/배치 (1000L 기준, 110 g/L × 1000L = 110kg galactose → 110kg tagatose, 100% theoretical yield)

        # 연간 배치 수
        batches_per_year = self.production_hours_per_year / 24  # 24시간/배치

        # 연간 타가토스 생산량
        annual_tagatose_kg = product_concentration * batches_per_year

        # 판매 수익
        # 두 가지 제품 옵션: 결정체 vs 시럽
        crystal_selling_price = self.tagatose_price * 1.2  # 결정체: 20% 프리미엄
        syrup_selling_price = self.tagatose_price * 0.95  # 시럽: 5% 할인

        # 50:50 판매 믹스 가정
        crystal_yield = annual_tagatose_kg * 0.5
        syrup_yield = annual_tagatose_kg * 0.5

        crystal_revenue = crystal_yield * crystal_selling_price
        syrup_revenue = syrup_yield * syrup_selling_price

        total_revenue = crystal_revenue + syrup_revenue

        return {
            'Annual Tagatose (kg)': annual_tagatose_kg,
            'Crystal Yield (kg)': crystal_yield,
            'Syrup Yield (kg)': syrup_yield,
            'Crystal Price ($/kg)': crystal_selling_price,
            'Syrup Price ($/kg)': syrup_selling_price,
            'Crystal Revenue ($)': crystal_revenue,
            'Syrup Revenue ($)': syrup_revenue,
            'Total Annual Revenue ($)': total_revenue,
        }

    def calculate_profitability(self):
        """
        수익성 지표 계산

        Returns
        -------
        dict: ROI, Payback period, NPV 등
        """
        capex = self.calculate_capex().get('Total CAPEX', 1000000)
        opex_annual = self.calculate_opex_annual().get('Total Annual OPEX', 100000)
        revenue_annual = self.calculate_revenue_annual().get('Total Annual Revenue ($)', 200000)

        # 연간 순이익
        annual_profit = revenue_annual - opex_annual

        # 1. ROI (Return on Investment)
        roi_annual = annual_profit / capex if capex > 0 else 0
        roi_percent = roi_annual * 100

        # 2. Payback Period (회수 기간)
        if annual_profit > 0:
            payback_years = capex / annual_profit
        else:
            payback_years = float('inf')

        # 3. NPV (Net Present Value) - 20년 프로젝트 기준
        npv = -capex
        for year in range(1, self.project_life + 1):
            discounted_profit = annual_profit / ((1 + self.discount_rate) ** year)
            npv += discounted_profit

        # 4. IRR (Internal Rate of Return) - bisection method
        # IRR은 NPV = 0을 만족하는 할인율, bisection으로 수렴
        def npv_at_rate(rate):
            if rate <= -1:
                return float('inf')
            return -capex + sum(
                annual_profit / ((1 + rate) ** yr)
                for yr in range(1, self.project_life + 1)
            )

        irr_approx = 0.0
        if annual_profit > 0:
            low, high = 0.0, 10.0  # 0% ~ 1000%
            for _ in range(100):  # 최대 100회 반복으로 수렴
                mid = (low + high) / 2
                if npv_at_rate(mid) > 0:
                    low = mid
                else:
                    high = mid
                if high - low < 1e-6:
                    break
            irr_approx = (low + high) / 2 * 100
        elif annual_profit == 0:
            irr_approx = 0.0
        else:
            irr_approx = float('-inf')  # 손실 → IRR 없음

        # 5. Break-even analysis
        break_even_price = opex_annual / self.calculate_revenue_annual().get('Annual Tagatose (kg)', 1)

        return {
            'CAPEX ($)': capex,
            'Annual OPEX ($)': opex_annual,
            'Annual Revenue ($)': revenue_annual,
            'Annual Profit ($)': annual_profit,
            'ROI (Annual %)': roi_percent,
            'Payback Period (years)': payback_years,
            'NPV (20 years, 10% discount rate) ($)': npv,
            'IRR (approx %)': irr_approx,
            'Break-even Price ($/kg)': break_even_price,
        }

    def print_analysis(self):
        """경제성 분석 결과 출력"""
        print("\n" + "="*70)
        print("TAGATOSE PRODUCTION - TECHNO-ECONOMIC ANALYSIS")
        print("="*70)

        # CAPEX
        print("\n[1] CAPITAL EXPENDITURE (CAPEX)")
        print("-" * 70)
        capex_data = self.calculate_capex()
        for key, value in capex_data.items():
            print(f"  {key:<40} ${value:>15,.0f}")

        # OPEX
        print("\n[2] OPERATING EXPENDITURE (OPEX) - Annual")
        print("-" * 70)
        opex_data = self.calculate_opex_annual()
        for key, value in opex_data.items():
            print(f"  {key:<40} ${value:>15,.0f}")

        # Revenue
        print("\n[3] REVENUE - Annual")
        print("-" * 70)
        revenue_data = self.calculate_revenue_annual()
        for key, value in revenue_data.items():
            if 'Price' in key:
                print(f"  {key:<40} ${value:>15.2f}")
            elif 'kg' in key or 'Yield' in key:
                print(f"  {key:<40} {value:>15,.0f} kg")
            else:
                print(f"  {key:<40} ${value:>15,.0f}")

        # Profitability
        print("\n[4] PROFITABILITY METRICS")
        print("-" * 70)
        profit_data = self.calculate_profitability()
        for key, value in profit_data.items():
            if 'IRR' in key or 'ROI' in key:
                print(f"  {key:<40} {value:>15.1f}%")
            elif 'years' in key:
                print(f"  {key:<40} {value:>15.2f}")
            elif 'Break-even' in key:
                print(f"  {key:<40} ${value:>15.2f}")
            else:
                print(f"  {key:<40} ${value:>15,.0f}")

        # Market Price Sensitivity
        print("\n[5] SENSITIVITY ANALYSIS - Tagatose Price")
        print("-" * 70)
        print("  Price ($/kg)  Annual Profit ($)  ROI (%)  Payback (yr)")
        print("  " + "-" * 65)
        for price in [3.0, 4.0, 5.0, 6.0, 7.0, 8.0]:
            original_price = self.tagatose_price
            self.tagatose_price = price
            profit_data = self.calculate_profitability()
            annual_profit = profit_data.get('Annual Profit ($)', 0)
            roi = profit_data.get('ROI (Annual %)', 0)
            payback = profit_data.get('Payback Period (years)', 999)
            print(f"  {price:>6.1f}         {annual_profit:>15,.0f}  {roi:>7.1f}  {payback:>9.1f}")
            self.tagatose_price = original_price

        print("\n" + "="*70 + "\n")

    def calculate_breakeven_analysis(self):
        """
        손익분기점 상세 분석

        어떤 판매 가격에서 손익분기점이 되는지 계산

        Returns
        -------
        dict: 손익분기점 분석 데이터
        """
        opex_annual = self.calculate_opex_annual().get('Total Annual OPEX', 100000)
        revenue_data = self.calculate_revenue_annual()
        annual_tagatose = revenue_data.get('Annual Tagatose (kg)', 15600)

        # 기본 손익분기점 가격 (OPEX만 충당)
        breakeven_opex_price = opex_annual / annual_tagatose

        # CAPEX 회수 포함 손익분기점 (연간)
        capex = self.calculate_capex().get('Total CAPEX', 1000000)
        annual_capex_recovery = capex / self.project_life
        breakeven_with_capex = (opex_annual + annual_capex_recovery) / annual_tagatose

        # 목표 ROI를 위한 필요 가격 (연 15% 수익률)
        target_annual_profit = capex * 0.15
        required_revenue = opex_annual + target_annual_profit
        price_for_15pct_roi = required_revenue / annual_tagatose

        return {
            'Annual OPEX ($)': opex_annual,
            'CAPEX ($)': capex,
            'Annual Tagatose (kg)': annual_tagatose,
            'Breakeven Price (OPEX only) ($/kg)': breakeven_opex_price,
            'Breakeven Price (w/ CAPEX recovery) ($/kg)': breakeven_with_capex,
            'Price for 15% Annual ROI ($/kg)': price_for_15pct_roi,
            'Current Market Price ($/kg)': self.tagatose_price,
            'Margin above Breakeven (%)': ((self.tagatose_price - breakeven_with_capex) / breakeven_with_capex * 100) if breakeven_with_capex > 0 else 0,
        }

    def print_detailed_economic_report(self):
        """상세 경제성 보고서 출력"""
        print("\n" + "="*80)
        print("TAGATOSE PRODUCTION - COMPREHENSIVE ECONOMIC ANALYSIS REPORT")
        print("(Based on 2024-2025 Market Prices)")
        print("="*80)

        # 1. 시장 가격 기준
        print("\n[0] MARKET PRICING INFORMATION")
        print("-" * 80)
        print(f"  D-Tagatose Market Price (2024-2025): ${self.tagatose_price:.2f}/kg")
        print(f"    (Bulk range: $8-10/kg for 100-200+ metric tons)")
        print(f"  D-Galactose Cost: ${self.glucose_cost:.2f}/kg")
        print(f"  Sodium Formate Cost: ${self.formate_cost:.2f}/kg (industrial grade)")
        print(f"  Electricity: ${self.electricity_price:.2f}/kWh")

        # 2. CAPEX
        print("\n[1] CAPITAL EXPENDITURE (CAPEX)")
        print("-" * 80)
        capex_data = self.calculate_capex()
        for key, value in capex_data.items():
            if key != 'Total CAPEX':
                print(f"  {key:<45} ${value:>15,.0f}")
        print(f"  {'-'*60}")
        print(f"  {'TOTAL CAPEX':<45} ${capex_data['Total CAPEX']:>15,.0f}")

        # 3. OPEX
        print("\n[2] OPERATING EXPENDITURE (OPEX) - Annual")
        print("-" * 80)
        opex_data = self.calculate_opex_annual()
        total_opex = opex_data.pop('Total Annual OPEX')

        # 분류별 OPEX - v2 파라미터 기준 (calculate_opex_annual()과 동기화)
        batch_time_hr = 24          # 24hr/batch (16h 혐기성 + 8h 호기성)
        galactose_per_batch = 110   # kg/batch (110 g/L × 1000L)
        formate_per_batch = 44.0    # kg/batch (5% 과량)
        batches_report = self.production_hours_per_year / batch_time_hr

        print("\n  Raw Materials:")
        print(f"    D-Galactose: {galactose_per_batch} kg/batch x ${self.glucose_cost:.2f}/kg x {batches_report:.0f} batches/yr")
        print(f"      = ${galactose_per_batch * self.glucose_cost * batches_report:,.0f}/yr")
        print(f"    Sodium Formate: {formate_per_batch} kg/batch x ${self.formate_cost:.2f}/kg x {batches_report:.0f} batches/yr")
        print(f"      = ${formate_per_batch * self.formate_cost * batches_report:,.0f}/yr")

        print("\n  Utilities & Operations:")
        for key in ['Electricity', 'Water', 'Labor']:
            if key in opex_data:
                print(f"    {key}: ${opex_data[key]:,.0f}")

        print("\n  Maintenance & Overhead:")
        for key in ['Maintenance', 'Miscellaneous']:
            if key in opex_data:
                print(f"    {key}: ${opex_data[key]:,.0f}")

        print(f"\n  {'-'*60}")
        print(f"  TOTAL ANNUAL OPEX: ${total_opex:,.0f}")

        # 4. Revenue & Production
        print("\n[3] PRODUCTION & REVENUE - Annual")
        print("-" * 80)
        revenue_data = self.calculate_revenue_annual()
        tagatose_per_batch = revenue_data['Annual Tagatose (kg)'] / (self.production_hours_per_year / 24)
        batches_per_year = self.production_hours_per_year / 24
        print(f"  Production Batches per Year: {batches_per_year:.0f} batches")
        print(f"  Tagatose per Batch: {tagatose_per_batch:.0f} kg (100% yield, 1000L reactor, 24 hr cycle)")
        print(f"  Annual Tagatose Production: {revenue_data['Annual Tagatose (kg)']:,.0f} kg")
        print(f"\n  Product Mix & Pricing:")
        print(f"    Crystals (50% of production): {revenue_data['Crystal Yield (kg)']:,.0f} kg @ ${revenue_data['Crystal Price ($/kg)']:.2f}/kg")
        print(f"      Revenue: ${revenue_data['Crystal Revenue ($)']:,.0f}")
        print(f"    Syrup (50% of production): {revenue_data['Syrup Yield (kg)']:,.0f} kg @ ${revenue_data['Syrup Price ($/kg)']:.2f}/kg")
        print(f"      Revenue: ${revenue_data['Syrup Revenue ($)']:,.0f}")
        print(f"\n  TOTAL ANNUAL REVENUE: ${revenue_data['Total Annual Revenue ($)']:,.0f}")

        # 5. Break-Even Analysis
        print("\n[4] BREAK-EVEN ANALYSIS")
        print("-" * 80)
        breakeven_data = self.calculate_breakeven_analysis()
        print(f"  Breakeven Price (OPEX only): ${breakeven_data['Breakeven Price (OPEX only) ($/kg)']:.2f}/kg")
        print(f"    → Covers operating costs but not capital investment")
        print(f"\n  Breakeven Price (with CAPEX recovery): ${breakeven_data['Breakeven Price (w/ CAPEX recovery) ($/kg)']:.2f}/kg")
        print(f"    → Covers all costs over {self.project_life}-year project life")
        print(f"\n  Price for 15% Annual ROI: ${breakeven_data['Price for 15% Annual ROI ($/kg)']:.2f}/kg")
        print(f"    → Target return for investors")
        print(f"\n  Current Market Price: ${self.tagatose_price:.2f}/kg")
        if breakeven_data['Margin above Breakeven (%)'] >= 0:
            print(f"  Safety Margin: {breakeven_data['Margin above Breakeven (%)']:.1f}% above breakeven")
        else:
            print(f"  WARNING: Price is {abs(breakeven_data['Margin above Breakeven (%)']):.1f}% BELOW breakeven!")

        # 6. Profitability Metrics
        print("\n[5] PROFITABILITY METRICS")
        print("-" * 80)
        profit_data = self.calculate_profitability()
        annual_profit = profit_data['Annual Profit ($)']
        print(f"  Annual Profit: ${annual_profit:,.0f}")
        print(f"  ROI (Annual): {profit_data['ROI (Annual %)']:.1f}%")
        print(f"  Payback Period: {profit_data['Payback Period (years)']:.1f} years")
        print(f"  NPV (20 years @ 10% discount): ${profit_data['NPV (20 years, 10% discount rate) ($)']:,.0f}")
        print(f"  IRR (Approximate): {profit_data['IRR (approx %)']:.1f}%")

        # 7. Price Sensitivity
        print("\n[6] PRICE SENSITIVITY ANALYSIS")
        print("-" * 80)
        print("  Impact of Tagatose Price Changes on Economics:\n")
        print("  Price ($/kg)  Annual Profit ($)  ROI (%)  Payback (yr)  Economic Viability")
        print("  " + "-" * 75)

        for price in [6, 8, 9, 10, 11, 12, 14]:
            original_price = self.tagatose_price
            self.tagatose_price = price
            profit_data = self.calculate_profitability()
            annual_profit = profit_data.get('Annual Profit ($)', 0)
            roi = profit_data.get('ROI (Annual %)', 0)
            payback = profit_data.get('Payback Period (years)', 999)

            # Viability assessment
            if annual_profit > 0 and roi > 15:
                viability = "HIGHLY VIABLE [OK]"
            elif annual_profit > 0 and roi > 10:
                viability = "VIABLE [OK]"
            elif annual_profit > 0:
                viability = "MARGINAL [?]"
            else:
                viability = "NOT VIABLE [X]"

            payback_str = f"{payback:.1f}" if payback < 999 else "∞"
            print(f"  {price:>6.1f}         {annual_profit:>15,.0f}  {roi:>7.1f}  {payback_str:>10}   {viability}")

            self.tagatose_price = original_price

        # 8. Cost Sensitivity
        print("\n[7] FEEDSTOCK COST SENSITIVITY")
        print("-" * 80)
        print("  Impact of D-Galactose Cost Changes (most significant raw material):\n")
        print("  Galactose Cost ($/kg)  Annual Profit ($)  ROI (%)  Breakeven Tagatose Price ($/kg)")
        print("  " + "-" * 75)

        for gal_cost in [1.0, 1.5, 2.0, 2.5, 3.0]:
            original_cost = self.glucose_cost
            self.glucose_cost = gal_cost
            profit_data = self.calculate_profitability()
            breakeven_data_temp = self.calculate_breakeven_analysis()
            annual_profit = profit_data.get('Annual Profit ($)', 0)
            roi = profit_data.get('ROI (Annual %)', 0)
            breakeven = breakeven_data_temp.get('Breakeven Price (w/ CAPEX recovery) ($/kg)', 0)

            print(f"  {gal_cost:>6.2f}               {annual_profit:>15,.0f}  {roi:>7.1f}  {breakeven:>24.2f}")

            self.glucose_cost = original_cost

        # 9. Economic Viability Summary
        print("\n[8] ECONOMIC VIABILITY ASSESSMENT")
        print("-" * 80)

        breakeven_with_capex = self.calculate_breakeven_analysis()['Breakeven Price (w/ CAPEX recovery) ($/kg)']
        current_market_price = self.tagatose_price

        if current_market_price >= breakeven_with_capex * 1.2:
            print("  [OK] ECONOMICALLY VIABLE")
            print(f"\n  Market Price (${current_market_price:.2f}/kg) is ${current_market_price - breakeven_with_capex:.2f}/kg")
            print(f"  ({(current_market_price - breakeven_with_capex) / breakeven_with_capex * 100:.1f}%) above breakeven.")
            print("\n  Recommendation: PROCEED with commercialization")

            profit_data = self.calculate_profitability()
            if profit_data['Annual Profit ($)'] > 0:
                payback = profit_data['Payback Period (years)']
                print(f"  Investment payback in ~{payback:.1f} years")
                print(f"  Annual profit: ${profit_data['Annual Profit ($)']:,.0f}")
        elif current_market_price >= breakeven_with_capex:
            print("  [?] MARGINALLY VIABLE")
            print(f"\n  Market Price (${current_market_price:.2f}/kg) is only slightly above breakeven.")
            print("  Recommendation: CONDITIONAL - Proceed only with optimized operations")
        else:
            print("  [X] NOT ECONOMICALLY VIABLE AT CURRENT PRICES")
            print(f"\n  Market Price (${current_market_price:.2f}/kg) is below breakeven")
            print(f"  (${breakeven_with_capex:.2f}/kg)")
            print(f"  Gap to close: ${breakeven_with_capex - current_market_price:.2f}/kg")
            print("\n  Options to improve viability:")
            print(f"    1. Increase selling price to >$10.40/kg")
            print(f"    2. Reduce CAPEX through process optimization")
            print(f"    3. Reduce raw material costs (focus on D-Galactose source)")
            print(f"    4. Increase production scale (improve equipment utilization)")

        print("\n" + "="*80 + "\n")

    def save_results(self, filename='tagatose_economics.txt'):
        """결과를 파일로 저장"""
        with open(filename, 'w') as f:
            f.write("TAGATOSE PRODUCTION - ECONOMIC ANALYSIS\n")
            f.write("="*70 + "\n\n")

            capex_data = self.calculate_capex()
            f.write("CAPEX Breakdown:\n")
            for k, v in capex_data.items():
                f.write(f"  {k}: ${v:,.0f}\n")

            opex_data = self.calculate_opex_annual()
            f.write("\nAnnual OPEX Breakdown:\n")
            for k, v in opex_data.items():
                f.write(f"  {k}: ${v:,.0f}\n")

            profit_data = self.calculate_profitability()
            f.write("\nProfitability Metrics:\n")
            for k, v in profit_data.items():
                f.write(f"  {k}: {v}\n")
