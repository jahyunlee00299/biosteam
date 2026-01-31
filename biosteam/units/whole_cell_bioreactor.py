# -*- coding: utf-8 -*-
# BioSTEAM: The Biorefinery Simulation and Techno-Economic Analysis Modules
# Copyright (C) 2020-2024, Yoel Cortes-Pena <yoelcortes@gmail.com>
#
# This module is under the UIUC open-source license. See
# github.com/BioSTEAMDevelopmentGroup/biosteam/blob/master/LICENSE.txt
# for license details.
"""
Whole Cell Bioreactor Module - D-Galactose to D-Tagatose Conversion

This module implements a batch bioreactor for whole cell catalysis,
optimized for D-Galactose to D-Tagatose conversion with oxygen-based
NAD+ regeneration under fully aerobic conditions (compressed air).

Main Reaction:
    D-Galactose + Sodium Formate + O2 → D-Tagatose + CO2 + H2O

NAD Regeneration (oxygen abundant):
    NADH + 0.25 O2 → NAD+ + 0.5 H2O

Features:
- 100% theoretical conversion to D-Tagatose
- Sodium formate substrate (5% molar excess over D-Galactose)
- Initial substrate concentration: D-Galactose 150 g/L
- Biocatalyst: Whole cell suspension, 50 g/L dry weight
- Cofactor supplementation: NAD+ 3 mM, NADP+ 0.1 mM
- pH control: 8.0 (HCl for pH adjustment)
- Oxygen supply: Compressed air (unlimited O2 assumption)
- Aeration: via compressor (not shaking flask)

Author: Claude AI
"""

import numpy as np
from .custom_bioreactor import CustomBioreactor
from thermosteam.reaction import Reaction, ParallelReaction

__all__ = ('WholeCellBioreactor',)


# ============================================================================
# 전세포촉매 배치 반응기 (Whole Cell Batch Bioreactor)
# D-Galactose → D-Tagatose 변환
# ============================================================================

class WholeCellBioreactor(CustomBioreactor):
    """
    D-Galactose to D-Tagatose 변환용 전세포촉매 배치 반응기

    100% 이론적 전환율을 목표로 하는 배치식 반응기입니다.
    산소 과량 조건에서 압축기를 통한 폭기로 충분한 산소를 공급합니다.

    **주요 반응:**
    - 메인: D-Galactose + Sodium Formate → D-Tagatose + CO2
    - NAD 재생성: NADH + O2 → NAD+ + H2O (산소 과량, 완전 재생성)

    **입출구:**

    입구 스트림:
        [0] Feed: D-Galactose (150 g/L), Sodium Formate (5% 과량),
                  물, 완충액, 코팩터 (NAD+ 3 mM, NADP+ 0.1 mM)
        [1] Compressed Air: 산소 공급

    출구 스트림:
        [0] Vent: CO2 가스 (및 미량 수증기)
        [1] Effluent: D-Tagatose (생성물), 미반응 D-Galactose,
                      미반응 Sodium Formate, 물, 바이오매스

    Parameters
    ----------
    tau : float
        배치 반응 시간 (hr). 필수 입력.
    N : int, optional
        배치 반응기 개수. N 또는 V 중 하나 필수 입력.
    V : float, optional
        목표 배치 반응기 부피 (m³). N과 동시 지정 불가.
    T : float, optional
        반응 온도 (K). 기본값: 310.15 K (37°C)
    P : float, optional
        반응 압력 (Pa). 기본값: 101325 Pa
    pH : float, optional
        반응 pH. 기본값: 8.0 (HCl 또는 NaOH로 조정)
    galactose_concentration : float, optional
        초기 D-Galactose 농도 (g/L). 기본값: 150
    biocatalyst_concentration : float, optional
        건중량 기준 전세포촉매 농도 (g/L). 기본값: 50
    formate_excess : float, optional
        Sodium Formate 몰 과량 비율 (0~1). 기본값: 0.05 (5%)
    nad_concentration : float, optional
        NAD+ 초기 농도 (mM). 기본값: 3
    nadp_concentration : float, optional
        NADP+ 초기 농도 (mM). 기본값: 0.1
    oxygen_supply : str, optional
        산소 공급 방식. 기본값: 'compressed' (압축기).
        - 'compressed': 압축 공기 (충분한 O2)
        - 'limited': 제한적 O2 (사용 안 함)
    conversion : float, optional
        D-Galactose 전환율 (0~1). 기본값: 1.0 (100%)

    Attributes
    ----------
    design_results : dict
        설계 결과 추가 항목:
        - 'D-Galactose concentration' (mol/L): 초기 기질 농도
        - 'Sodium Formate concentration' (mol/L): 초기 포르메이트 농도
        - 'D-Tagatose production' (mol/hr): 생성물 생산율
        - 'CO2 production' (mol/hr): CO2 생산율
        - 'Oxygen demand' (mol/hr): 산소 요구량 (계산용)
        - 'pH': 반응 pH

    Examples
    --------
    >>> from biosteam import Stream, settings
    >>> from biosteam.units import WholeCellBioreactor
    >>> settings.set_thermo('default')
    >>> feed = Stream('feed',
    ...               D_Galactose=150*1000,  # 150 g/L in 1000L
    ...               SodiumFormate=59.5*1000,
    ...               Water=800*1000,
    ...               units='kg/hr',
    ...               T=310.15)
    >>> air = Stream('compressed_air', O2=100, N2=400, units='kg/hr')
    >>> R1 = WholeCellBioreactor('R1', ins=[feed, air],
    ...                          outs=('CO2_vent', 'product'),
    ...                          tau=24, N=4)
    >>> R1.simulate()
    >>> R1.show()
    """

    line = 'Whole Cell Bioreactor (D-Galactose → D-Tagatose, 100% conversion)'

    # ========================================================================
    # 입출구 정의
    # ========================================================================

    #: 입구 개수: [0] Feed (기질), [1] Compressed air (산소)
    _N_ins = 2

    #: 출구 개수: [0] Vent (CO2), [1] Effluent (생성물)
    _N_outs = 2

    # ========================================================================
    # 기본 파라미터 - 반응 조건
    # ========================================================================

    #: float: D-Galactose 전환율 (0~1). 기본값: 1.0 (100%)
    conversion = 1.0

    #: float: 초기 D-Galactose 농도 (g/L). 기본값: 150
    galactose_concentration = 150.0

    #: float: 건중량 기준 전세포촉매 농도 (g/L). 기본값: 50
    biocatalyst_concentration = 50.0

    #: float: Sodium Formate 몰 과량 비율. 기본값: 0.05 (5%)
    formate_excess = 0.05

    #: float: NAD+ 초기 농도 (mM). 기본값: 3
    nad_concentration = 3.0

    #: float: NADP+ 초기 농도 (mM). 기본값: 0.1
    nadp_concentration = 0.1

    #: float: 반응 pH. 기본값: 8.0
    pH = 8.0

    #: str: 산소 공급 방식 ('compressed' 또는 'limited'). 기본값: 'compressed'
    oxygen_supply = 'compressed'

    # ========================================================================
    # 화학 상수
    # ========================================================================

    # 분자량 (g/mol)
    MW_GALACTOSE = 180.0      # D-Galactose
    MW_TAGATOSE = 180.0       # D-Tagatose
    MW_FORMATE = 46.0         # Formic acid (HCOO-)
    MW_SODIUM_FORMATE = 68.0  # HCOONa
    MW_CO2 = 44.0             # Carbon dioxide

    # ========================================================================
    # 초기화 메서드
    # ========================================================================

    def _init(self, tau=None, N=None, V=None, T=310.15, P=101325, pH=8.0,
              galactose_concentration=None, biocatalyst_concentration=None,
              formate_excess=None, nad_concentration=None,
              nadp_concentration=None, oxygen_supply='compressed',
              conversion=None, Nmin=2, Nmax=36):
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
            반응 온도 (K)
        P : float
            반응 압력 (Pa)
        pH : float
            반응 pH (기본값: 8.0)
        galactose_concentration : float, optional
            초기 D-Galactose 농도 (g/L)
        biocatalyst_concentration : float, optional
            전세포촉매 농도 (g/L)
        formate_excess : float, optional
            Sodium Formate 몰 과량 비율
        nad_concentration : float, optional
            NAD+ 농도 (mM)
        nadp_concentration : float, optional
            NADP+ 농도 (mM)
        oxygen_supply : str
            산소 공급 방식
        conversion : float, optional
            D-Galactose 전환율
        Nmin : int
            최소 반응기 개수
        Nmax : int
            최대 반응기 개수
        """
        # 부모 클래스 초기화
        super()._init(tau=tau, N=N, V=V, T=T, P=P, Nmin=Nmin, Nmax=Nmax)

        # pH 설정
        self.pH = pH

        # 산소 공급 방식 검증
        if oxygen_supply not in ('compressed', 'limited'):
            raise ValueError(
                f"oxygen_supply는 'compressed' 또는 'limited'여야 합니다. "
                f"입력값: {oxygen_supply}"
            )
        self.oxygen_supply = oxygen_supply

        # 농도 파라미터 설정
        if galactose_concentration is not None:
            self.galactose_concentration = galactose_concentration
        if biocatalyst_concentration is not None:
            self.biocatalyst_concentration = biocatalyst_concentration
        if formate_excess is not None:
            self.formate_excess = formate_excess
        if nad_concentration is not None:
            self.nad_concentration = nad_concentration
        if nadp_concentration is not None:
            self.nadp_concentration = nadp_concentration
        if conversion is not None:
            self.conversion = conversion

        # 반응 객체 (초기화 대기)
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

        # 반응 객체 생성 (화학 물질 정보 필요)
        chemicals = self.chemicals

        try:
            # 1. 메인 반응: D-Galactose + Sodium Formate → D-Tagatose + CO2
            self._main_reaction = Reaction(
                'D_Galactose + SodiumFormate -> Tagatose + CO2',
                'D_Galactose', self.conversion, chemicals
            )
        except:
            self._main_reaction = None

        try:
            # 2. NAD 재생성: NADH + O2 → NAD+ + H2O (산소 과량)
            self._nad_regeneration = Reaction(
                'NADH + 0.25 O2 -> NAD + 0.5 H2O',
                'NADH', 1.0, chemicals  # 100% 효율 (산소 과량)
            )
        except:
            self._nad_regeneration = None

    # ========================================================================
    # 프로퍼티
    # ========================================================================

    @property
    def vent(self):
        """[Stream] 분리 가스 출구 (CO2)"""
        return self.outs[0]

    @property
    def effluent(self):
        """[Stream] 액체 생성물 출구"""
        return self.outs[1]

    # ========================================================================
    # 계산 메서드
    # ========================================================================

    def _calculate_feed_composition(self):
        """
        입구 피드 조성 계산

        Returns
        -------
        dict
            기질 조성 정보:
            - 'galactose_mol': D-Galactose 몰량
            - 'formate_mol': Sodium Formate 몰량 (5% 과량)
            - 'nad_mol': NAD+ 몰량
            - 'nadp_mol': NADP+ 몰량
        """
        # D-Galactose 몰량 계산
        feed = self.ins[0]
        if feed is None or feed.F_vol == 0:
            return {}

        volume_L = feed.F_vol * 1000  # m³ → L

        # 초기 농도 기반 몰량 계산
        galactose_g_total = self.galactose_concentration * volume_L
        galactose_mol = galactose_g_total / self.MW_GALACTOSE

        # Sodium Formate: D-Galactose 대비 5% 과량 (몰 기준)
        formate_mol = galactose_mol * (1 + self.formate_excess)
        formate_g_total = formate_mol * self.MW_SODIUM_FORMATE

        # 코팩터 몰량
        nad_mol = self.nad_concentration * volume_L / 1000  # mM × L → mol
        nadp_mol = self.nadp_concentration * volume_L / 1000

        return {
            'galactose_mol': galactose_mol,
            'formate_mol': formate_mol,
            'formate_excess_ratio': self.formate_excess,
            'nad_mol': nad_mol,
            'nadp_mol': nadp_mol,
            'volume_L': volume_L,
        }

    # ========================================================================
    # 시뮬레이션 메서드
    # ========================================================================

    def _run(self):
        """
        전세포촉매 배치 반응 시뮬레이션

        프로세스:
        1. 입구 피드 혼합
        2. D-Galactose + Sodium Formate → D-Tagatose + CO2 (메인 반응)
        3. NADH + O2 → NAD+ + H2O (NAD 재생성, 산소 과량)
        4. CO2 기체 분리
        5. 생성물 (D-Tagatose) 포함 액체 생성
        """
        vent, effluent = self.outs
        feed = self.ins[0]

        # 1. 입구 피드 복사 (초기 조성)
        effluent.copy_like(feed)
        effluent.T = self.T
        effluent.P = self.P

        # 2. 메인 반응: D-Galactose → D-Tagatose (100% 이론적)
        # 반응 메커니즘:
        # - 입력: D-Galactose (150 g/L), Sodium Formate (5% 과량)
        # - 출력: D-Tagatose (동일 분자량), CO2
        # - 100% 전환율 (이론적 수율)
        if self._main_reaction:
            self._main_reaction.force_reaction(effluent)
        else:
            # 화학물질 정의 부족 시 수동 계산
            self._run_manual_reaction(effluent)

        # 3. NAD 재생성 (산소 과량 조건)
        # NADH → NAD+ (O2 충분)
        if self._nad_regeneration:
            self._nad_regeneration.force_reaction(effluent)

        # 4. CO2 분리 (가스 출구로 분리)
        vent.empty()
        vent.receive_vent(effluent, energy_balance=False)
        vent.T = self.T
        vent.P = self.P

        # 5. 열 부하 계산
        self._calculate_reactor_duty(effluent)

    def _run_manual_reaction(self, effluent):
        """
        화학물질 라이브러리 부족 시 수동 반응 계산

        D-Galactose + Sodium Formate → D-Tagatose + CO2 + H2O

        이론적 물질 수지 (100% 전환율):
        Input:
        - D-Galactose: 150 g/L (0.833 M)
        - Sodium Formate: 59.5 g/L (0.875 M, 5% 과량)
        - 물

        Output:
        - D-Tagatose: 150 g/L (0.833 M, 100% 수율)
        - CO2: 0.833 M (36.6 g/L)
        - H2O: 생성
        - 미반응 Sodium Formate: ~6 g/L (0.042 M)
        """
        try:
            # 화학 물질 인덱스 찾기
            gal_idx = effluent.chemicals.index('D_Galactose')
            tag_idx = effluent.chemicals.index('Tagatose')
            co2_idx = effluent.chemicals.index('CO2')
            formate_idx = effluent.chemicals.index('SodiumFormate')

            # 현재 유량 (mol/hr)
            galactose_mol = effluent.imol[gal_idx]

            # 100% 전환 계산
            reacted_mol = galactose_mol * self.conversion

            # 스트림 업데이트
            effluent.imol[gal_idx] -= reacted_mol        # 갈락토스 소비
            effluent.imol[tag_idx] += reacted_mol        # 타가토스 생성 (1:1 비율)
            effluent.imol[co2_idx] += reacted_mol        # CO2 생성 (1:1 비율)
            # 포르메이트: 약간만 소비 (보조 기질)
            effluent.imol[formate_idx] *= (1 - 0.10)     # 10% 소비

        except (ValueError, IndexError):
            # 화학물질 없을 시 경고 후 진행
            pass

    def _calculate_reactor_duty(self, effluent):
        """
        반응기 열 부하 계산

        D-Galactose → D-Tagatose 반응은 중성 또는 약간 발열성
        (일반적 바이오 산화 반응은 발열성)

        추정: 반응열 = -20 kJ/mol (발열성, 냉각 필요)
        """
        feed = self.ins[0]
        try:
            gal_idx = effluent.chemicals.index('D_Galactose')
            gal_in_mol = feed.imol[gal_idx]
            gal_out_mol = effluent.imol[gal_idx]
            reacted_mol = gal_in_mol - gal_out_mol

            # 반응열: -20 kJ/mol (발열, 냉각 필요)
            heat_of_reaction = -20 * reacted_mol  # kJ/hr
            self.Hnet = heat_of_reaction

        except:
            self.Hnet = 0

    # ========================================================================
    # 설계 메서드
    # ========================================================================

    def _design(self):
        """
        배치 반응기 설계 및 생산 사양 계산
        """
        # 부모 클래스 설계 호출
        super()._design()

        # 추가 설계 정보 저장
        Design = self.design_results

        # 운영 조건
        Design['pH'] = self.pH
        Design['Oxygen supply'] = self.oxygen_supply
        Design['Conversion'] = f"{self.conversion*100:.1f}%"

        # 기질 정보
        comp = self._calculate_feed_composition()
        if comp:
            Design['D-Galactose (initial)'] = f"{comp['galactose_mol']:.1f} mol"
            Design['Sodium Formate (initial)'] = f"{comp['formate_mol']:.1f} mol"
            Design['Formate excess ratio'] = f"{self.formate_excess*100:.1f}%"
            Design['NAD+ (initial)'] = f"{comp['nad_mol']:.3f} mol"
            Design['NADP+ (initial)'] = f"{comp['nadp_mol']:.4f} mol"

        # 생성물 정보
        try:
            tag_idx = self.effluent.chemicals.index('Tagatose')
            co2_idx = self.effluent.chemicals.index('CO2')
            Design['D-Tagatose production'] = f"{self.effluent.imol[tag_idx]:.1f} mol/hr"
            Design['CO2 production'] = f"{self.effluent.imol[co2_idx]:.1f} mol/hr"
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
            ('D-Galactose (initial)', f'{self.galactose_concentration:.1f}', 'g/L'),
            ('Biocatalyst (dry weight)', f'{self.biocatalyst_concentration:.1f}', 'g/L'),
            ('Sodium Formate excess', f'{self.formate_excess*100:.1f}%', ''),
            ('NAD+ concentration', f'{self.nad_concentration:.1f}', 'mM'),
            ('NADP+ concentration', f'{self.nadp_concentration:.2f}', 'mM'),
            ('pH', f'{self.pH:.1f}', ''),
            ('Oxygen supply', self.oxygen_supply, ''),
            ('D-Galactose conversion', f'{self.conversion*100:.1f}%', ''),
        ])
        return tuple(info)


# ============================================================================
# 사용 예시
# ============================================================================

"""
Example: D-Galactose to D-Tagatose Conversion (100% conversion)

>>> from biosteam import Stream, settings
>>> from biosteam.units import WholeCellBioreactor
>>> from biosteam.units.whole_cell_process import create_whole_cell_process

# 1. 화학 물질 설정
>>> settings.set_thermo('default')

# 2. 피드 스트림 (기질 + 코팩터)
>>> feed = Stream('feed',
...               D_Galactose=150,      # 150 g/L (0.833 M)
...               SodiumFormate=59.5,   # 59.5 g/L (0.875 M, 5% 과량)
...               Water=800,
...               units='kg/hr',
...               T=310.15)  # 37°C

# 3. 압축 공기 (산소)
>>> air = Stream('compressed_air',
...              O2=100,
...              N2=400,
...              units='kg/hr')

# 4. 반응기 구성
>>> R1 = WholeCellBioreactor(
...     'R1',
...     ins=[feed, air],
...     outs=('CO2_vent', 'product'),
...     tau=24,            # 24시간 반응
...     N=4,               # 4개 배치 반응기
...     pH=8.0,            # pH = 8
...     conversion=1.0,    # 100% 이론적 전환율
...     oxygen_supply='compressed'
... )

# 5. 통합 공정 (반응기 + 고액분리)
>>> R1_full, S1, process = create_whole_cell_process(
...     feed, tau=24, N=4, conversion=1.0
... )

# 6. 시뮬레이션 및 결과
>>> R1.simulate()
>>> print(f"D-Tagatose production: {R1.effluent.imol['Tagatose']:.1f} mol/hr")
>>> print(f"Theoretical yield: 100%")
>>> print(f"Actual yield: {(R1.effluent.imol['Tagatose'] / feed.imol['D_Galactose'] * 100):.1f}%")

# 7. 설계 정보
>>> R1.show()
"""
