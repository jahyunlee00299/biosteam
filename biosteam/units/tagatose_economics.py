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

        # 경제 파라미터
        self.tagatose_price = 5.0  # $/kg (현재 상업 가격: $4-8/kg)
        self.glucose_cost = 0.5    # $/kg (원료)
        self.formate_cost = 0.3    # $/kg (원료)
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
            return {}

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
            opex_breakdown['Electricity'] = 0
            opex_breakdown['Water'] = 0

        # 2. 원료비
        galactose_cost = 75 * self.glucose_cost  # 75 kg/batch
        formate_cost = 29.75 * self.formate_cost  # 29.75 kg/batch

        # 연간 배치 수 (생산 시간 / 배치 시간)
        batches_per_year = self.production_hours_per_year / 36  # 36시간/배치
        annual_galactose = galactose_cost * batches_per_year
        annual_formate = formate_cost * batches_per_year

        opex_breakdown['D-Galactose'] = annual_galactose
        opex_breakdown['Sodium Formate'] = annual_formate

        # 3. 노동비 (시간제 근로자 2-3명)
        labor_hrs_per_year = self.production_hours_per_year
        annual_labor = labor_hrs_per_year * self.labor_cost
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
            생성물 농도 (기본값: 75kg 타가토스/배치)

        Returns
        -------
        dict: 수익 분석
        """
        if product_concentration is None:
            product_concentration = 75  # kg/배치 (500L 기준)

        # 연간 배치 수
        batches_per_year = self.production_hours_per_year / 36  # 36시간/배치

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

        # 4. IRR (Internal Rate of Return) - 간단 근사
        # IRR은 NPV = 0인 할인율
        # 단순 근사: (Annual Profit / Avg CAPEX) * 100
        irr_approx = (annual_profit / (capex / 2)) * 100

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
