# -*- coding: utf-8 -*-
# BioSTEAM: The Biorefinery Simulation and Techno-Economic Analysis Modules
# Copyright (C) 2020-2024, Yoel Cortes-Pena <yoelcortes@gmail.com>
#
# This module is under the UIUC open-source license. See
# github.com/BioSTEAMDevelopmentGroup/biosteam/blob/master/LICENSE.txt
# for license details.
"""
Oxygen Compressor for Aerobic Bioreactors

Simple compressor model for supplying compressed air/oxygen to aerobic bioreactors.
Calculates power requirement based on oxygen demand and compression ratio.

Author: Claude AI
"""

from biosteam import Unit
from biosteam.units.compressor import IsothermalCompressor

__all__ = ('OxygenCompressor',)


class OxygenCompressor(Unit):
    """
    산소 압축기 - 배치 생물 반응기용

    산소를 포함한 압축 공기를 공급합니다.
    필요한 산소량에 기반하여 공기 흐름을 계산하고 압축 동력을 산출합니다.

    **용도:**
    - 혐기성 반응 후 호기성 재생성 단계에서 산소 공급
    - 예: WholeCellBioreactor의 Stage 3 (NAD+ 재생성)

    **입출구:**

    입구:
        [0] Ambient air: 주변 공기 (21% O2, 79% N2, 대기압)

    출구:
        [0] Compressed air: 압축된 공기 (높은 압력)

    Parameters
    ----------
    oxygen_demand : float, optional
        필요 산소량 (mol). 기본값: 0
    compression_ratio : float, optional
        압축 비율 (출구 압력 / 입구 압력). 기본값: 2.0
    efficiency : float, optional
        압축기 효율 (0~1). 기본값: 0.75 (75%)
    operation_mode : str, optional
        운영 모드. 'on_demand' (필요시만) 또는 'continuous' (지속). 기본값: 'on_demand'

    Attributes
    ----------
    air_requirement : float
        필요 공기량 (kg/hr)
    oxygen_concentration : float
        공기 중 산소 농도 (%). 기본값: 0.21 (21%)
    """

    line = 'Oxygen Compressor (Compressed Air Supply)'

    # ========================================================================
    # 입출구 정의
    # ========================================================================

    _N_ins = 1   # Ambient air
    _N_outs = 1  # Compressed air

    # ========================================================================
    # 기본 파라미터
    # ========================================================================

    #: float: 필요 산소량 (mol)
    oxygen_demand = 0

    #: float: 압축 비율 (P_out / P_in)
    compression_ratio = 2.0

    #: float: 압축기 효율 (0~1)
    efficiency = 0.75

    #: str: 운영 모드 ('on_demand' 또는 'continuous')
    operation_mode = 'on_demand'

    #: float: 공기 중 산소 농도
    oxygen_concentration = 0.21

    #: float: 산소 분자량 (g/mol)
    MW_O2 = 32.0

    #: float: 질소 분자량 (g/mol)
    MW_N2 = 28.0

    #: float: 공기 평균 분자량 (g/mol)
    MW_AIR = 28.97

    # ========================================================================
    # 초기화
    # ========================================================================

    def _init(self, oxygen_demand=None, compression_ratio=None,
              efficiency=None, operation_mode='on_demand'):
        """
        압축기 초기화

        Parameters
        ----------
        oxygen_demand : float, optional
            필요 산소량 (mol)
        compression_ratio : float, optional
            압축 비율 (기본값: 2.0)
        efficiency : float, optional
            압축 효율 (기본값: 0.75)
        operation_mode : str
            운영 모드: 'on_demand' (필요시) 또는 'continuous' (지속)
        """
        if oxygen_demand is not None:
            self.oxygen_demand = oxygen_demand

        if compression_ratio is not None:
            if compression_ratio < 1.0:
                raise ValueError("압축 비율은 1.0 이상이어야 합니다")
            self.compression_ratio = compression_ratio

        if efficiency is not None:
            if not (0 < efficiency <= 1):
                raise ValueError("효율은 0~1 범위여야 합니다")
            self.efficiency = efficiency

        if operation_mode not in ('on_demand', 'continuous'):
            raise ValueError("operation_mode는 'on_demand' 또는 'continuous'여야 합니다")
        self.operation_mode = operation_mode

    # ========================================================================
    # 계산 메서드
    # ========================================================================

    def _calculate_air_requirement(self):
        """
        필요 공기량 계산

        산소량(mol) → 산소 질량 → 공기량 계산

        Returns
        -------
        tuple: (air_kg_hr, oxygen_kg_hr)
        """
        # 산소 질량 계산 (kg/hr)
        oxygen_kg_hr = self.oxygen_demand * self.MW_O2 / 1000

        # 공기 중 산소 농도 기반 필요 공기량
        # air_kg = oxygen_kg / oxygen_concentration
        air_kg_hr = oxygen_kg_hr / self.oxygen_concentration

        return air_kg_hr, oxygen_kg_hr

    def _calculate_compression_power(self, air_flow_kg_hr):
        """
        압축 동력 계산 (등온 압축 가정)

        동력 = (체적 유량 × 압축 일) / 효율

        Returns
        -------
        float: 필요 동력 (kW)
        """
        if air_flow_kg_hr == 0:
            return 0

        # 공기 밀도 (kg/m³) @ 25°C, 1 atm
        rho_air = 1.184  # kg/m³

        # 체적 유량 (m³/hr)
        volumetric_flow = air_flow_kg_hr / rho_air

        # 등온 압축 일
        # W = n × R × T × ln(P2/P1) = Q × P × ln(r)
        # 근사: P1 = 101.325 kPa
        # 동력 (W) = 체적 유량 (m³/s) × 압력 (Pa) × ln(압축비)
        volumetric_flow_m3_s = volumetric_flow / 3600

        P_in = 101325  # Pa (1 atm)
        compression_work = volumetric_flow_m3_s * P_in * np.log(self.compression_ratio)

        # 효율 고려
        power_kW = compression_work / (self.efficiency * 1000)

        return power_kW

    # ========================================================================
    # 시뮬레이션 메서드
    # ========================================================================

    def _run(self):
        """
        압축기 시뮬레이션

        1. 필요 공기량 계산
        2. 입구 공기 스트림 설정
        3. 압축된 공기 출구 설정
        4. 압축 동력 계산
        """
        # 입출구 스트림
        inlet = self.ins[0]
        outlet = self.outs[0]

        # 필요 공기량 계산
        air_requirement_kg_hr, oxygen_requirement_kg_hr = self._calculate_air_requirement()

        # 입구 스트림 설정 (주변 공기)
        # 입구가 없으면 생성
        if inlet is None or inlet.F_mass == 0:
            # 기본 공기 스트림 설정
            # O2 : N2 = 21 : 79
            inlet = self.ins[0]
            if inlet:
                inlet.empty()
            else:
                # 입력 없으면 주변 공기로 자동 설정
                pass

        # 출구 설정 (압축된 공기)
        outlet.copy_like(inlet)

        # 필요한 공기량을 입력에 반영
        # 대기 공기 성분
        try:
            o2_idx = outlet.chemicals.index('O2')
            n2_idx = outlet.chemicals.index('N2')

            # 필요량 기반으로 O2/N2 설정
            o2_kg = oxygen_requirement_kg_hr
            n2_kg = air_requirement_kg_hr - o2_kg

            outlet.imass[o2_idx] = o2_kg
            outlet.imass[n2_idx] = n2_kg

        except (ValueError, IndexError):
            # 화학물질 없으면 전체 공기로 처리
            outlet.F_mass = air_requirement_kg_hr

        # 압축 동력 계산
        power_kW = self._calculate_compression_power(air_requirement_kg_hr)
        self.power_utility(power_kW)

    # ========================================================================
    # 설계 메서드
    # ========================================================================

    def _design(self):
        """압축기 설계 및 성능 계산"""
        Design = self.design_results

        # 필요 공기량
        air_kg_hr, o2_kg_hr = self._calculate_air_requirement()

        # 압축 동력
        power_kW = self._calculate_compression_power(air_kg_hr)

        # 설계 결과 저장
        Design['Oxygen demand'] = f"{self.oxygen_demand:.1f} mol"
        Design['Air requirement'] = f"{air_kg_hr:.1f} kg/hr"
        Design['Oxygen requirement'] = f"{o2_kg_hr:.2f} kg/hr"
        Design['Compression ratio'] = f"{self.compression_ratio:.1f}"
        Design['Compression power'] = f"{power_kW:.2f} kW"
        Design['Efficiency'] = f"{self.efficiency*100:.1f}%"
        Design['Operation mode'] = self.operation_mode

    # ========================================================================
    # 비용 메서드
    # ========================================================================

    def _cost(self):
        """압축기 비용 추정"""
        Design = self.design_results

        # 압축 동력에 기반한 비용 추정
        # 소형 압축기: $300-500/kW (설치 비용 포함)
        power_kW = float(Design.get('Compression power', '0').split()[0])

        if power_kW > 0:
            # 기본 비용 (NREL 참고)
            cost_per_kW = 350  # $/kW
            base_cost = power_kW * cost_per_kW

            # 스케일 팩터 (규모의 경제)
            # Cost = base × (kW / reference_kW) ^ n
            reference_kW = 50
            scale_factor = 0.6

            if power_kW > 0:
                scaled_cost = base_cost * ((power_kW / reference_kW) ** scale_factor)
            else:
                scaled_cost = 0

            self.baseline_purchase_costs['Compressor'] = scaled_cost

    # ========================================================================
    # 정보 표시
    # ========================================================================

    def _get_design_info(self):
        """설계 정보"""
        return (
            ('Oxygen demand', f"{self.oxygen_demand:.1f}", 'mol'),
            ('Compression ratio', f"{self.compression_ratio:.1f}", ''),
            ('Efficiency', f"{self.efficiency*100:.0f}", '%'),
            ('Operation mode', self.operation_mode, ''),
        )


# ============================================================================
# 수입 (numpy 추가)
# ============================================================================

import numpy as np
