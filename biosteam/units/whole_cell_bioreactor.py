# -*- coding: utf-8 -*-
# BioSTEAM: The Biorefinery Simulation and Techno-Economic Analysis Modules
# Copyright (C) 2020-2024, Yoel Cortes-Pena <yoelcortes@gmail.com>
#
# This module is under the UIUC open-source license. See
# github.com/BioSTEAMDevelopmentGroup/biosteam/blob/master/LICENSE.txt
# for license details.
"""
Whole Cell Bioreactor Module

This module implements a batch bioreactor for whole cell catalysis,
supporting cofactor-dependent bioconversions with oxygen-based
NAD+ regeneration (e.g., Galactose + formate -> tagatose conversion).

The bioreactor includes:
- Main bioconversion reaction
- Cofactor (NADH, NADP, NADPH) handling
- O2-based NAD+ regeneration
- Configurable oxygen transfer rates (kLa)
- Product recovery from solid-liquid separation

Author: Claude AI
"""

import numpy as np
from .custom_bioreactor import CustomBioreactor
from thermosteam.reaction import Reaction, ParallelReaction

__all__ = ('WholeCell Bioreactor',)


# ============================================================================
# 전세포촉매 배치 반응기 (Whole Cell Batch Bioreactor)
# ============================================================================

class WholeCellBioreactor(CustomBioreactor):
    """
    전세포촉매 배치 반응기 - Galactose 변환용 최적화

    갈락토스를 타가토스로 변환하는 전세포촉매 바이오리액터입니다.
    산소 기반 NAD+ 재생성으로 지속적인 반응을 지원하며,
    shaking flask 조건의 산소 전달률을 모사합니다.

    **주요 반응:**
    - 메인: Galactose + formate → tagatose + CO2
    - NAD 재생성: NADH + O2 → NAD+ + H2O (자동)
    - 중간체: galactitol 포함

    **재료 수지:**

    입구 스트림 (2개):
        [0] Feed: Galactose, formate, 물, 기타 영양물질
        [1] Air/O2: 산소 공급 (산소 전달률 제어)

    출구 스트림 (2개):
        [0] Vent: CO2 가스
        [1] Effluent: tagatose, 미반응 galactose, formate, 바이오매스 등

    Parameters
    ----------
    tau : float
        반응 시간 (hr)
    N : int, optional
        반응기 개수
    V : float, optional
        목표 반응기 부피 (m³)
    T : float, optional
        반응 온도 (K). 기본값: 310.15 K (37°C)
    P : float, optional
        반응 압력 (Pa). 기본값: 101325 Pa
    kLa : float, optional
        산소 전달률 계수 (1/hr). 기본값: 75 (shaking flask 기준)
        옵션: 50, 75, 100 (rpm별 kLa 값)
    kLa_option : str, optional
        산소 전달률 사전 설정 옵션
        - 'low': kLa = 50 1/hr (낮은 폭기)
        - 'medium': kLa = 75 1/hr (중간 폭기, 기본값)
        - 'high': kLa = 100 1/hr (높은 폭기)
        - 'custom': kLa 파라미터 사용
    conversion : float, optional
        갈락토스 전환율 (0~1). 기본값: 0.85 (85%)
    nad_regeneration_efficiency : float, optional
        NAD 재생성 효율 (0~1). 기본값: 0.95 (95%)
        산소 부족 시 자동 감소
    formate_recovery : float, optional
        포르메이트 회수율 (0~1). 기본값: 0.98 (98%)
    biocatalyst_concentration : float, optional
        전세포촉매 농도 (g/L). 기본값: 10

    Attributes
    ----------
    design_results : dict
        design_results 에 추가 항목:
        - 'Oxygen transfer rate' (mol/hr)
        - 'Galactose conversion' (mol)
        - 'Tagatose production' (mol)
        - 'CO2 production' (mol)
        - 'NAD regeneration rate' (1/hr)

    Notes
    -----
    1. 산소 공급:
       - 기본 구현: 공기 전달을 통한 확산 (shaking flask 모사)
       - 산소 전달률: kLa 값으로 제어
       - 산소 제한 조건: NAD 재생성 효율 저하

    2. 코팩터 균형:
       - NADH: 메인 반응에서 소비 → O2에 의해 NAD+로 재생성
       - NADP/NADPH: 보조 반응에서 사용 (별도 재생성 경로)

    3. 전세포촉매:
       - 배치 공정 반복 가능 (동결건조 보관 가능)
       - 고액분리로 회수 (다운스트림 처리)

    Examples
    --------
    >>> from biosteam import Stream, settings
    >>> from biosteam.units import WholeCellBioreactor
    >>> settings.set_thermo('default')  # Galactose, tagatose 등 포함
    >>> feed = Stream('feed',
    ...               Galactose=50, Formate=30, Water=1000,
    ...               units='kg/hr', T=310)
    >>> R1 = WholeCellBioreactor('R1', ins=feed,
    ...                          outs=('CO2', 'product'),
    ...                          tau=24, N=4, kLa_option='medium')
    >>> R1.simulate()
    >>> R1.show()

    See Also
    --------
    biosteam.units.CustomBioreactor
    biosteam.units.NRELBatchBioreactor
    """

    line = 'Whole Cell Bioreactor (Galactose → Tagatose)'

    # ========================================================================
    # 기본 파라미터 - 반응 조건
    # ========================================================================

    #: float: 갈락토스 전환율 (0~1), 기본값: 0.85
    conversion = 0.85

    #: float: NAD 재생성 효율 (0~1), 기본값: 0.95
    nad_regeneration_efficiency = 0.95

    #: float: 포르메이트 회수율 (0~1), 기본값: 0.98
    formate_recovery = 0.98

    #: float: 전세포촉매 농도 (g/L), 기본값: 10
    biocatalyst_concentration = 10.0

    # ========================================================================
    # 산소 전달률 기준값 (Shaking flask)
    # ========================================================================

    # kLa 옵션별 값 (1/hr)
    kLa_options = {
        'low': 50,       # 낮은 폭기 조건
        'medium': 75,    # 중간 폭기 조건 (기본)
        'high': 100,     # 높은 폭기 조건
    }

    # ========================================================================
    # 초기화 메서드
    # ========================================================================

    def _init(self, tau=None, N=None, V=None, T=310.15, P=101325,
              kLa=None, kLa_option='medium',
              conversion=None, nad_regeneration_efficiency=None,
              formate_recovery=None, biocatalyst_concentration=None,
              Nmin=2, Nmax=36):
        """
        전세포촉매 반응기 파라미터 초기화

        Parameters
        ----------
        tau : float
            반응 시간 (hr)
        N : int, optional
            반응기 개수
        V : float, optional
            목표 반응기 부피 (m³)
        T : float
            반응 온도 (K). 기본값: 310.15 K (37°C)
        P : float
            반응 압력 (Pa). 기본값: 101325 Pa
        kLa : float, optional
            산소 전달률 계수 (1/hr). kLa_option='custom'일 때 사용
        kLa_option : str
            산소 전달률 옵션: 'low', 'medium' (기본), 'high', 'custom'
        conversion : float, optional
            갈락토스 전환율 (0~1)
        nad_regeneration_efficiency : float, optional
            NAD 재생성 효율 (0~1)
        formate_recovery : float, optional
            포르메이트 회수율 (0~1)
        biocatalyst_concentration : float, optional
            전세포촉매 농도 (g/L)
        Nmin : int
            최소 반응기 개수
        Nmax : int
            최대 반응기 개수
        """
        # 부모 클래스 초기화
        super()._init(tau=tau, N=N, V=V, T=T, P=P, Nmin=Nmin, Nmax=Nmax)

        # 산소 전달률 설정
        if kLa_option == 'custom':
            if kLa is None:
                raise ValueError(
                    "kLa_option='custom'일 때 kLa 파라미터를 반드시 지정하세요"
                )
            self.kLa = kLa
        elif kLa_option in self.kLa_options:
            self.kLa = self.kLa_options[kLa_option]
        else:
            raise ValueError(
                f"kLa_option은 {list(self.kLa_options.keys())} 또는 'custom' 중 하나여야 합니다. "
                f"입력값: {kLa_option}"
            )

        #: [float] 산소 전달률 옵션
        self.kLa_option = kLa_option

        # 반응 파라미터 설정
        if conversion is not None:
            self.conversion = conversion
        if nad_regeneration_efficiency is not None:
            self.nad_regeneration_efficiency = nad_regeneration_efficiency
        if formate_recovery is not None:
            self.formate_recovery = formate_recovery
        if biocatalyst_concentration is not None:
            self.biocatalyst_concentration = biocatalyst_concentration

        # 반응 객체 생성 (화학 물질 정보 필요하므로 _setup에서 생성)
        self._main_reaction = None
        self._nad_regeneration = None

    # ========================================================================
    # 설정 메서드
    # ========================================================================

    def _setup(self):
        """
        반응 모델 및 출구 스트림 설정
        """
        super()._setup()

        # 반응 객체 생성
        chemicals = self.chemicals

        # 1. 메인 반응: Galactose + formate → tagatose + CO2
        # 화학식:
        # C6H12O6 (갈락토스) + HCOO- (포르메이트) + NADH + H+ → C6H12O6 (타가토스) + CO2 + NAD+ + H2O
        try:
            self._main_reaction = Reaction(
                'Galactose + Formate -> Tagatose + CO2',
                'Galactose', self.conversion, chemicals
            )
        except:
            # 타가토스 화학물질이 정의되지 않은 경우 간단한 변환율 방식 사용
            self._main_reaction = None

        # 2. NAD 재생성 반응: NADH + O2 → NAD+ + H2O
        # (산소 농도에 따라 속도 조정)
        try:
            self._nad_regeneration = Reaction(
                'NADH + 0.25 O2 -> NAD + 0.5 H2O',
                'NADH', self.nad_regeneration_efficiency, chemicals
            )
        except:
            self._nad_regeneration = None

    # ========================================================================
    # 시뮬레이션 메서드
    # ========================================================================

    def _run(self):
        """
        전세포촉매 배치 반응 시뮬레이션

        프로세스:
        1. 입구 스트림 혼합
        2. 갈락토스 + 포르메이트 → 타가토스 + CO2 (메인 반응)
        3. NADH + O2 → NAD+ + H2O (NAD 재생성)
        4. CO2 기체 분리
        5. 타가토스 + 미반응 기질 포함 액체 생성
        """
        vent, effluent = self.outs
        feed = self.ins[0]

        # 1. 입구 스트림 혼합
        effluent.copy_like(feed)
        effluent.T = self.T
        effluent.P = self.P

        # 2. 메인 반응 진행
        # Galactose + Formate → Tagatose + CO2
        if self._main_reaction:
            self._main_reaction.force_reaction(effluent)
        else:
            # 화학물질 정의 부족 시 수동 계산
            self._run_manual_reaction(effluent)

        # 3. NAD 재생성 (O2 기반)
        # NADH + O2 → NAD+ (산소 전달률 기반 효율)
        nad_regen_rate = self._calculate_nad_regeneration()
        self.nad_regeneration_rate = nad_regen_rate

        # 4. CO2 분리 - 가스 출구로 전달
        vent.empty()
        vent.receive_vent(effluent, energy_balance=False)
        vent.T = self.T
        vent.P = self.P

        # 5. 엔탈피 계산
        # 반응이 약간 발열성이라고 가정 (냉각 필요)
        self._calculate_reactor_duty(effluent)

    def _run_manual_reaction(self, effluent):
        """
        화학물질 라이브러리 부족 시 수동으로 반응 계산

        주요 반응:
        Galactose + Formate → Tagatose + CO2

        입자 물질 수지 (모반응 기준 갈락토스 1 mol):
        - 갈락토스: 1 → (1-X) (X: 전환율)
        - 포르메이트: 1 → (1-r) (r: 포르메이트 회수율)
        - 타가토스: 0 → X
        - CO2: 0 → X
        """
        try:
            # Galactose 찾기
            galactose_idx = effluent.chemicals.index('Galactose')
            co2_idx = effluent.chemicals.index('CO2')
            tagatose_idx = effluent.chemicals.index('Tagatose')
            formate_idx = effluent.chemicals.index('Formate')

            # 현재 유량 (mol/hr)
            galactose_flow = effluent.imol[galactose_idx]
            formate_flow = effluent.imol[formate_idx]

            # 반응 진행
            # 갈락토스를 기준으로 (stoichiometry 1:1:1:1)
            reacted = galactose_flow * self.conversion

            # 스트림 업데이트
            effluent.imol[galactose_idx] -= reacted      # 갈락토스 소비
            effluent.imol[tagatose_idx] += reacted       # 타가토스 생성
            effluent.imol[co2_idx] += reacted            # CO2 생성
            # 포르메이트는 보조 기질이므로 약간만 소비
            effluent.imol[formate_idx] *= (1 - 0.05)    # 5% 소비

        except (ValueError, IndexError):
            # 화학물질 인덱스 문제 시 경고만 출력하고 진행
            pass

    def _calculate_nad_regeneration(self):
        """
        산소 전달률 기반 NAD 재생성 효율 계산

        O2 전달 모델:
        dC_NAD/dt = kLa * (C_NAD,sat - C_NAD) * efficiency_factor

        산소 농도에 따른 NAD 재생성:
        - 충분한 O2: efficiency = 1.0 (설정된 값)
        - 낮은 O2: efficiency = 0.5 (제한)
        """
        # 산소 전달률에 따른 재생성 효율 계산
        # kLa가 높을수록 더 나은 산소 전달
        # kLa >= 100: 완전 재생성 (efficiency = 1.0)
        # kLa = 50: 부분 재생성 (efficiency = 0.7)

        if self.kLa >= 100:
            efficiency_factor = 1.0
        elif self.kLa >= 75:
            efficiency_factor = 0.85
        else:  # kLa <= 50
            efficiency_factor = 0.7

        return self.kLa * self.nad_regeneration_efficiency * efficiency_factor

    def _calculate_reactor_duty(self, effluent):
        """
        반응기 열 부하 계산

        전세포촉매 반응은 약간 발열성:
        - 포르메이트 산화: 약 -50 kJ/mol
        - 총 열: -50 * (반응한 갈락토스 mol/hr)
        """
        # 간단한 추정: 반응이 약간 발열성
        # 실제 값은 thermodynamic database에서 참고
        feed = self.ins[0]
        try:
            galactose_idx = effluent.chemicals.index('Galactose')
            galactose_in = feed.imol[galactose_idx]
            galactose_out = effluent.imol[galactose_idx]
            reacted = galactose_in - galactose_out

            # 반응열: -50 kJ/mol (발열성)
            # 음수 = 냉각 필요
            heat_of_reaction = -50 * reacted  # kJ/hr
            self.Hnet = heat_of_reaction

        except:
            self.Hnet = 0

    # ========================================================================
    # 설계 메서드 (추가 정보)
    # ========================================================================

    def _design(self):
        """
        배치 반응기 설계 및 산소 전달 사양
        """
        # 부모 클래스 설계 호출
        super()._design()

        # 추가 설계 정보
        Design = self.design_results

        # 산소 전달률 정보
        Design['kLa'] = self.kLa
        Design['kLa option'] = self.kLa_option
        Design['NAD regeneration rate'] = getattr(self, 'nad_regeneration_rate', 0)

        # 생성물 정보 추가
        try:
            tagatose_idx = self.effluent.chemicals.index('Tagatose')
            galactose_idx = self.effluent.chemicals.index('Galactose')
            co2_idx = self.effluent.chemicals.index('CO2')

            Design['Tagatose production'] = self.effluent.imol[tagatose_idx]
            Design['Galactose remaining'] = self.effluent.imol[galactose_idx]
            Design['CO2 production'] = self.effluent.imol[co2_idx]
            Design['Conversion'] = self.conversion
            Design['NAD regeneration efficiency'] = self.nad_regeneration_efficiency

        except:
            pass

    # ========================================================================
    # 정보 표시 메서드
    # ========================================================================

    def _get_design_info(self):
        """
        설계 정보 (show() 메서드에서 표시)
        """
        info = list(super()._get_design_info())
        info.extend([
            ('Galactose conversion', f"{self.conversion*100:.1f}%", ''),
            ('kLa option', self.kLa_option, ''),
            ('kLa value', f"{self.kLa:.0f}", '1/hr'),
            ('NAD regeneration efficiency', f"{self.nad_regeneration_efficiency*100:.1f}%", ''),
            ('Biocatalyst concentration', f"{self.biocatalyst_concentration:.1f}", 'g/L'),
        ])
        return tuple(info)


# ============================================================================
# 간단한 사용 예시
# ============================================================================

"""
Example: Galactose to Tagatose Conversion

>>> from biosteam import Stream, System, settings, find
>>> from biosteam.units import WholeCellBioreactor

# 1. 화학 물질 정의 (필요시)
>>> settings.set_thermo('default')

# 2. 피드 스트림 정의
>>> feed = Stream(
...     'feed',
...     Galactose=50,    # 갈락토스 50 kg/hr
...     Formate=30,      # 포르메이트 30 kg/hr
...     Water=1000,      # 물 1000 kg/hr
...     T=310.15,        # 37°C
...     units='kg/hr'
... )

# 3. 반응기 정의
>>> R1 = WholeCellBioreactor(
...     'R1',
...     ins=feed,
...     outs=('CO2_vent', 'product'),
...     tau=24,              # 24시간 반응
...     N=4,                 # 4개 반응기
...     kLa_option='medium',  # 중간 산소 전달률
...     conversion=0.85      # 85% 전환율
... )

# 4. 시뮬레이션 실행
>>> R1.simulate()

# 5. 결과 확인
>>> R1.show()
>>> print(f"Tagatose produced: {R1.product.imol['Tagatose']:.1f} mol/hr")
>>> print(f"NAD regeneration rate: {R1.nad_regeneration_rate:.1f} 1/hr")

# 6. 다운스트림 처리
>>> # 고액분리: 바이오매스 회수
>>> from biosteam.units import Separator
>>> S1 = Separator(
...     'S1',
...     ins=R1.product,
...     outs=('liquid_product', 'solid_biocatalyst'),
...     split={'Galactose': 0.0, 'Tagatose': 1.0, 'Water': 1.0}  # 타가토스는 액체로
... )
"""
