# -*- coding: utf-8 -*-
# BioSTEAM: The Biorefinery Simulation and Techno-Economic Analysis Modules
# Copyright (C) 2020-2024, Yoel Cortes-Pena <yoelcortes@gmail.com>
#
# This module is under the UIUC open-source license. See
# github.com/BioSTEAMDevelopmentGroup/biosteam/blob/master/LICENSE.txt
# for license details.
"""
Tagatose Downstream Processing & Purification Module

Multi-stage food-grade purification process:
1. Solid-Liquid Separation (Centrifuge/Filter)
2. Decolorization (Active Carbon Adsorption)
3. Concentration & Crystallization or Syrup Production
4. Final Product (Crystal or Syrup)

Author: Claude AI
"""

from biosteam import Unit
import numpy as np

__all__ = ('SolidLiquidSeparator', 'DecolorationUnit', 'CrystallizationUnit',
           'SyrupConcentrationUnit')


# ============================================================================
# 고액분리 (Solid-Liquid Separation)
# ============================================================================

class SolidLiquidSeparator(Unit):
    """
    고액분리기 - Centrifuge or Filter Press

    반응기 출구의 액체(Tagatose)와 고체(바이오매스)를 분리합니다.
    """

    line = 'Solid-Liquid Separator (Centrifuge)'

    _N_ins = 1   # Bioreactor effluent
    _N_outs = 2  # Liquid (Tagatose solution) + Solid (Biocatalyst)

    def _init(self, recovery_tagatose=None, equipment_type='centrifuge'):
        """
        Parameters
        ----------
        recovery_tagatose : float, optional
            타가토스 회수율 (0~1). 기본값: 0.98 (98%)
        equipment_type : str, optional
            장비 타입: 'centrifuge' 또는 'filter'. 기본값: 'centrifuge'
        """
        self.recovery_tagatose = recovery_tagatose or 0.98
        self.equipment_type = equipment_type

    def _run(self):
        """액체와 고체 분리"""
        inlet = self.ins[0]
        liquid_outlet, solid_outlet = self.outs

        # 액체 출구: 타가토스 + 미반응물 + 물
        liquid_outlet.copy_like(inlet)

        # 고체 출구: 바이오매스 (버림)
        solid_outlet.empty()

        # 분리 효율 적용
        try:
            tag_idx = liquid_outlet.chemicals.index('Tagatose')
            tag_mol = liquid_outlet.imol[tag_idx]
            # 회수되지 않은 양 제거
            liquid_outlet.imol[tag_idx] *= self.recovery_tagatose
        except:
            pass

    def _design(self):
        """분리기 설계"""
        inlet = self.ins[0]
        Design = self.design_results

        Design['Equipment type'] = self.equipment_type
        Design['Recovery rate'] = f"{self.recovery_tagatose*100:.1f}%"
        Design['Feed volume'] = f"{inlet.F_vol*1000:.1f} L"

    def _cost(self):
        """분리기 비용"""
        inlet = self.ins[0]
        feed_L = inlet.F_vol * 1000

        if self.equipment_type == 'centrifuge':
            # Centrifuge: $500-2000 (용량에 따라)
            base_cost = 1500
            scale_factor = 0.5
        else:  # filter
            base_cost = 800
            scale_factor = 0.4

        # 스케일 팩터 적용 (100L 기준)
        reference_L = 100
        cost = base_cost * ((feed_L / reference_L) ** scale_factor)

        self.baseline_purchase_costs['Separator'] = cost


# ============================================================================
# 탈색 (Decolorization)
# ============================================================================

class DecolorationUnit(Unit):
    """
    탈색 장치 - Active Carbon Adsorption

    활성탄을 사용하여 발효액의 색도를 제거합니다 (식품 그레이드).
    """

    line = 'Decolorization (Activated Carbon Adsorption)'

    _N_ins = 1   # Liquid from separator
    _N_outs = 1  # Decolorized liquid

    def _init(self, carbon_loading=None, decolorization_efficiency=None):
        """
        Parameters
        ----------
        carbon_loading : float, optional
            활성탄 투입량 (% w/w). 기본값: 2% (타가토스 기준)
        decolorization_efficiency : float, optional
            탈색 효율 (0~1). 기본값: 0.85 (85%)
        """
        self.carbon_loading = carbon_loading or 0.02  # 2%
        self.decolorization_efficiency = decolorization_efficiency or 0.85

    def _run(self):
        """활성탄 흡착 처리"""
        inlet = self.ins[0]
        outlet = self.outs[0]

        outlet.copy_like(inlet)
        # 색도 제거 (여기서는 성분 변화 없음, 색만 제거)
        # 실제로는 색상 지수 감소로 모델링 가능

    def _design(self):
        """활성탄 필요량 계산"""
        inlet = self.ins[0]
        Design = self.design_results

        # 타가토스 기준 활성탄 투입량
        try:
            tag_idx = inlet.chemicals.index('Tagatose')
            tagatose_kg = inlet.imass[tag_idx] / 1000
        except:
            tagatose_kg = inlet.F_mass / 1000

        carbon_required_kg = tagatose_kg * self.carbon_loading

        Design['Tagatose input'] = f"{tagatose_kg:.1f} kg"
        Design['Carbon loading'] = f"{self.carbon_loading*100:.1f}%"
        Design['Carbon required'] = f"{carbon_required_kg:.1f} kg"
        Design['Decolorization efficiency'] = f"{self.decolorization_efficiency*100:.0f}%"

    def _cost(self):
        """활성탄 비용"""
        inlet = self.ins[0]

        try:
            tag_idx = inlet.chemicals.index('Tagatose')
            tagatose_kg = inlet.imass[tag_idx] / 1000
        except:
            tagatose_kg = inlet.F_mass / 1000

        carbon_kg = tagatose_kg * self.carbon_loading

        # 활성탄 비용: $1.5-3/kg (품질에 따라)
        carbon_cost_per_kg = 2.0
        carbon_cost = carbon_kg * carbon_cost_per_kg

        # 탈색 장치 (tank + 여과): $5000-15000
        equipment_cost = 10000

        self.baseline_purchase_costs['Activated Carbon'] = carbon_cost
        self.baseline_purchase_costs['Decolorization Equipment'] = equipment_cost


# ============================================================================
# 결정화 (Crystallization)
# ============================================================================

class CrystallizationUnit(Unit):
    """
    결정화 장치 - 타가토스 결정 생산

    농축된 타가토스를 냉각하여 결정을 생성합니다.
    (식품 그레이드 정제 설탕과 유사)
    """

    line = 'Crystallization Unit (Tagatose Crystals)'

    _N_ins = 1   # Concentrated tagatose solution
    _N_outs = 2  # Crystals + Mother liquor

    def _init(self, crystal_recovery=None, crystal_purity=None):
        """
        Parameters
        ----------
        crystal_recovery : float, optional
            결정 회수율 (0~1). 기본값: 0.90 (90%)
        crystal_purity : float, optional
            결정 순도 (0~1). 기본값: 0.99 (99%)
        """
        self.crystal_recovery = crystal_recovery or 0.90
        self.crystal_purity = crystal_purity or 0.99

    def _run(self):
        """결정화 과정"""
        inlet = self.ins[0]
        crystals, mother_liquor = self.outs

        # 결정: 고순도 타가토스
        crystals.copy_like(inlet)

        # 모액: 미반응물 + 물
        mother_liquor.empty()

        try:
            tag_idx = inlet.chemicals.index('Tagatose')
            tag_mol = inlet.imol[tag_idx]

            # 회수된 결정량
            crystals.imol[tag_idx] = tag_mol * self.crystal_recovery
            mother_liquor.imol[tag_idx] = tag_mol * (1 - self.crystal_recovery)

        except:
            pass

    def _design(self):
        """결정화 설계"""
        inlet = self.ins[0]
        Design = self.design_results

        try:
            tag_idx = inlet.chemicals.index('Tagatose')
            tagatose_kg = inlet.imass[tag_idx] / 1000
            crystal_yield_kg = tagatose_kg * self.crystal_recovery
        except:
            crystal_yield_kg = inlet.F_mass * self.crystal_recovery / 1000

        Design['Feed volume'] = f"{inlet.F_vol*1000:.1f} L"
        Design['Tagatose input'] = f"{tagatose_kg:.1f} kg"
        Design['Crystal yield'] = f"{crystal_yield_kg:.1f} kg"
        Design['Crystal recovery'] = f"{self.crystal_recovery*100:.0f}%"
        Design['Crystal purity'] = f"{self.crystal_purity*100:.1f}%"

    def _cost(self):
        """결정화 장치 비용"""
        inlet = self.ins[0]

        try:
            tag_idx = inlet.chemicals.index('Tagatose')
            tagatose_kg = inlet.imass[tag_idx] / 1000
        except:
            tagatose_kg = inlet.F_mass / 1000

        crystal_yield_kg = tagatose_kg * self.crystal_recovery

        # 결정화 장치: 냉각 탱크, 여과, 건조
        # $20000-50000 (500L 스케일 기준)
        equipment_cost = 35000

        # 결정 건조 에너지 비용
        drying_energy_cost = crystal_yield_kg * 5  # $/kg

        self.baseline_purchase_costs['Crystallization Equipment'] = equipment_cost
        self.baseline_purchase_costs['Drying Operation'] = drying_energy_cost


# ============================================================================
# 시럽 농축 (Syrup Concentration)
# ============================================================================

class SyrupConcentrationUnit(Unit):
    """
    시럽 농축 장치 - 타가토스 시럽 생산

    농축된 타가토스 용액을 더 짙은 시럽으로 가공합니다.
    (액상 설탕/고과당 유사)
    """

    line = 'Syrup Concentration Unit (Tagatose Syrup)'

    _N_ins = 1   # Decolorized tagatose solution
    _N_outs = 1  # Concentrated syrup

    def _init(self, target_concentration=None, evaporation_efficiency=None):
        """
        Parameters
        ----------
        target_concentration : float, optional
            목표 농축도 (% w/w). 기본값: 70% (물엿 스타일)
        evaporation_efficiency : float, optional
            증발 효율 (0~1). 기본값: 0.95 (95%)
        """
        self.target_concentration = target_concentration or 0.70
        self.evaporation_efficiency = evaporation_efficiency or 0.95

    def _run(self):
        """농축 과정"""
        inlet = self.ins[0]
        outlet = self.outs[0]

        outlet.copy_like(inlet)
        # 농축: 주로 물을 제거
        # 타가토스는 유지하고 물만 제거
        try:
            water_idx = outlet.chemicals.index('Water')
            # 물 함량 감소로 농축도 증가
            current_mass = outlet.F_mass
            target_solids_mass = current_mass * (1 - self.target_concentration)
            # 물은 감소하지만 여기서는 단순화
        except:
            pass

    def _design(self):
        """농축 설계"""
        inlet = self.ins[0]
        Design = self.design_results

        try:
            tag_idx = inlet.chemicals.index('Tagatose')
            tagatose_kg = inlet.imass[tag_idx] / 1000
        except:
            tagatose_kg = inlet.F_mass / 1000

        # 농축도 기반 최종 시럽 부피
        syrup_density = 1200  # kg/m³ (70% 설탕 용액)
        syrup_mass = tagatose_kg / (self.target_concentration * 1000)  # kg
        syrup_volume = syrup_mass / (syrup_density / 1000)  # L

        Design['Tagatose input'] = f"{tagatose_kg:.1f} kg"
        Design['Target concentration'] = f"{self.target_concentration*100:.0f}%"
        Design['Syrup volume'] = f"{syrup_volume:.1f} L"
        Design['Evaporation efficiency'] = f"{self.evaporation_efficiency*100:.0f}%"

    def _cost(self):
        """농축 장치 비용"""
        inlet = self.ins[0]

        # 진공 증발기: $15000-40000 (500L 스케일)
        evaporator_cost = 25000

        # 에너지 비용 (증발)
        try:
            tag_idx = inlet.chemicals.index('Tagatose')
            tagatose_kg = inlet.imass[tag_idx] / 1000
        except:
            tagatose_kg = inlet.F_mass / 1000

        # 물 증발량
        initial_water = inlet.imass[inlet.chemicals.index('Water')] / 1000 if 'Water' in inlet.chemicals else 0
        water_to_evaporate = initial_water * (1 - self.target_concentration)
        energy_cost = water_to_evaporate * 3  # $/kg (증발열)

        self.baseline_purchase_costs['Evaporator'] = evaporator_cost
        self.baseline_purchase_costs['Evaporation Energy'] = energy_cost
