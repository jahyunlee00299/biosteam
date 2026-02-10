# -*- coding: utf-8 -*-
# BioSTEAM: The Biorefinery Simulation and Techno-Economic Analysis Modules
# Copyright (C) 2020-2024, Yoel Cortes-Pena <yoelcortes@gmail.com>
#
# This module is under the UIUC open-source license. See
# github.com/BioSTEAMDevelopmentGroup/biosteam/blob/master/LICENSE.txt
# for license details.
"""
Custom Bioreactor Module

This module implements a customizable batch bioreactor based on NREL design standards,
adapted for various bioconversion processes.

References
----------
.. [1] D. Humbird, R. Davis, L. Tao, C. Kinchin, D. Hsu, and A. Aden
    National. Renewable Energy Laboratory Golden, Colorado. P. Schoen,
    J. Lukas, B. Olthof, M. Worley, D. Sexton, and D. Dudgeon. Harris Group
    Inc. Seattle, Washington and Atlanta, Georgia. Process Design and Economics
    for Biochemical Conversion of Lignocellulosic Biomass to Ethanol Dilute-Acid
    Pretreatment and Enzymatic Hydrolysis of Corn Stover. May 2011. Technical
    Report NREL/TP-5100-47764
"""

import numpy as np
from .. import Unit
from .design_tools import size_batch
from .decorators import cost
from math import ceil
from thermosteam.reaction import Reaction, ParallelReaction

__all__ = ('CustomBioreactor',)

# ============================================================================
# 배치 바이오리액터 비용 데코레이터 정의
# 각 데코레이터는 (기준파라미터, 비용항목이름, ...) 형식
# ============================================================================

@cost('Recirculation flow rate', 'Recirculation pumps',
      kW=30, S=77.22216, cost=47200, n=0.8, BM=2.3, CE=522,
      N='Number of reactors')
@cost('Reactor volume', 'Cleaning in place',
      CE=521.9, cost=421e3, S=3785, n=0.6, BM=1.8)
@cost('Reactor volume', 'Agitators',
      CE=521.9, cost=52500, S=3785, n=0.5, kW=22.371, BM=1.5,
      N='Number of reactors')
@cost('Reactor volume', 'Reactors',
      CE=521.9, cost=844000, S=3785, n=0.5, BM=1.5,
      N='Number of reactors')
@cost('Reactor duty', 'Heat exchangers',
      CE=522, cost=23900, S=20920000.0, n=0.7, BM=2.2,
      N='Number of reactors', magnitude=True)
class CustomBioreactor(Unit):
    """
    배치 바이오리액터 (Batch Bioreactor) - NREL 설계 표준 기반

    다양한 바이오 변환 공정(발효, 효소 반응, 미생물 배양 등)에 사용할 수 있는
    배치식 반응기입니다. 자동 반응기 개수 최적화, 다양한 반응 동역학 모델을
    지원합니다.

    Parameters
    ----------
    ins : Stream
        입구 스트림 (기질, 영양분, 미생물, 물 등)
    outs : tuple[Stream, Stream]
        * [0] vent (분리 가스): CO2, 에탄올 증기 등 기체 생성물
        * [1] effluent (액체 생성물): 미반응물, 생성물, 바이오매스 등
    tau : float
        반응 시간 (hr) - 필수
    N : int, optional
        반응기 개수. N 또는 V 중 하나 반드시 지정 필요.
        autoselect_N=True인 경우 자동 계산됨.
    V : float, optional
        목표 반응기 부피 (m³). N과 동시 지정 불가.
    T : float, optional
        반응기 운영 온도 (K). 기본값: 305.15 K (32°C)
    P : float, optional
        반응기 운영 압력 (Pa). 기본값: 101325 Pa (1 atm)
    tau_0 : float, optional
        청소 및 언로딩 시간 (hr). 기본값: 3
    V_wf : float, optional
        작동 부피 비율 (0~1). 기본값: 0.9 (90% 채움)
    Nmin : int, optional
        최소 반응기 개수. 기본값: 2
    Nmax : int, optional
        최대 반응기 개수. 기본값: 36
    autoselect_N : bool, optional
        True인 경우 비용 최소화 반응기 개수 자동 선택. 기본값: False

    Notes
    -----
    - N 또는 V 중 반드시 하나는 지정해야 함
    - autoselect_N=True인 경우 매번 시뮬레이션 시 최적 N을 계산하므로 시간이 걸림
    - 반응 모델은 _run() 메서드에서 정의 필요

    Attributes
    ----------
    design_results : dict
        설계 결과 딕셔너리:
        - 'Reactor volume' (m³): 각 반응기의 부피
        - 'Batch time' (hr): 배치당 소요 시간
        - 'Loading time' (hr): 재료 주입 시간
        - 'Cycle time' (hr): 사이클 시간 (반응 + 청소)
        - 'Total dead time' (hr): 총 준비/청소 시간
        - 'Reactor duty' (kJ/hr): 열 교환량
        - 'Recirculation flow rate' (m³/hr): 순환 유량
        - 'Number of reactors' (-): 설계된 반응기 개수

    Examples
    --------
    >>> from biosteam import Stream, settings
    >>> from biosteam.units import CustomBioreactor
    >>> settings.set_thermo('sugar')  # 또는 다른 thermodynamic package
    >>> feed = Stream('feed', Water=1.20e+05, Glucose=1.89e+03, units='kg/hr')
    >>> reactor = CustomBioreactor('R1', ins=feed, outs=('vent', 'product'),
    ...                             tau=24, N=4, T=310)
    >>> reactor.simulate()
    >>> reactor.show()

    See Also
    --------
    biosteam.units.NRELBatchBioreactor
    biosteam.units.NRELFermentation
    biosteam.units.AeratedBioreactor
    """

    # 설계 단위 정의
    _units = {
        'Reactor volume': 'm3',          # 각 반응기 부피
        'Cycle time': 'hr',             # 사이클 시간
        'Batch time': 'hr',             # 배치 시간
        'Loading time': 'hr',           # 로딩 시간
        'Total dead time': 'hr',        # 총 대기 시간
        'Reactor duty': 'kJ/hr',        # 열 교환 부하
        'Recirculation flow rate': 'm3/hr'  # 순환 유량
    }

    # 입출구 개수 지정
    _N_ins = 1      # 입구: 주요 피드
    _N_outs = 2     # 출구: 가스 + 액체

    line = 'Batch Bioreactor'

    # ========================================================================
    # 기본 파라미터
    # ========================================================================

    #: bool: True인 경우 매 시뮬레이션마다 최저 비용의 N 자동 선택
    autoselect_N = False

    #: float: 청소 및 언로딩 시간 (hr)
    tau_0 = 3

    #: float: 작동 부피 비율 (0~1), 예: 0.9 = 90% 채움
    V_wf = 0.9

    # ========================================================================
    # 초기화 메서드
    # ========================================================================

    def _init(self, tau=None, N=None, V=None, T=305.15, P=101325,
              Nmin=2, Nmax=36):
        """
        반응기 파라미터 초기화

        Parameters
        ----------
        tau : float
            반응 시간 (hr) - 필수
        N : int, optional
            반응기 개수
        V : float, optional
            목표 반응기 부피 (m³)
        T : float
            온도 (K)
        P : float
            압력 (Pa)
        Nmin : int
            최소 반응기 개수
        Nmax : int
            최대 반응기 개수
        """
        self._N = N
        self._V = V

        #: [float] 반응 시간 (hr)
        self.tau = tau

        #: [int] 반응기 개수
        if N:
            self.N = N

        #: [float] 목표 반응기 부피 (m³)
        if V:
            self.V = V

        #: [float] 운영 온도 (K)
        self.T = T

        #: [float] 운영 압력 (Pa)
        self.P = P

        #: [int] 최소 반응기 개수
        self.Nmin = Nmin

        #: [int] 최대 반응기 개수
        self.Nmax = Nmax

    # ========================================================================
    # 프로퍼티 (Property) - N과 V 설정 관리
    # ========================================================================

    @property
    def vent(self):
        """[Stream] 분리 가스 출구"""
        return self.outs[0]

    @property
    def effluent(self):
        """[Stream] 액체 생성물 출구"""
        return self.outs[1]

    @property
    def N(self):
        """[int] 반응기 개수"""
        return self._N

    @N.setter
    def N(self, N):
        """반응기 개수 설정"""
        if N is None:
            self._N = N
            return
        if N <= 1:
            raise ValueError(f"반응기 개수는 1보다 커야 합니다. 입력값: {N}")
        assert not self._V, '반응기 부피와 개수를 동시에 지정할 수 없습니다'
        self._N = ceil(N)

    @property
    def V(self):
        """[float] 반응기 부피 (m³)"""
        return self._V

    @V.setter
    def V(self, V):
        """반응기 부피 설정"""
        if V is None:
            self._V = V
            return
        if V <= 1:
            raise ValueError(f"반응기 부피는 1보다 커야 합니다. 입력값: {V}")
        assert not self._N, '반응기 부피와 개수를 동시에 지정할 수 없습니다'
        self._V = V

    @property
    def tau(self):
        """[float] 반응 시간 (hr)"""
        return self._tau

    @tau.setter
    def tau(self, tau):
        """반응 시간 설정"""
        self._tau = tau

    # ========================================================================
    # 설정 메서드
    # ========================================================================

    def _setup(self):
        """출구 스트림 초기 설정"""
        super()._setup()
        vent, effluent = self.outs
        vent.phase = 'g'              # 출구[0] = 가스
        vent.T = effluent.T = self.T
        vent.P = effluent.P = self.P

    def _get_design_info(self):
        """설계 정보 반환 (show() 메서드에서 표시)"""
        return (
            ('청소 및 언로딩 시간', self.tau_0, 'hr'),
            ('작동 부피 비율', self.V_wf, ''),
        )

    # ========================================================================
    # 비용 최적화 메서드
    # ========================================================================

    @property
    def N_at_minimum_capital_cost(self):
        """
        최저 자본 비용에서의 반응기 개수 계산

        Nmin부터 Nmax까지 각 N값에 대해 비용을 계산하여
        최저 비용을 주는 N값을 반환합니다.

        Returns
        -------
        int
            최저 비용 시 반응기 개수
        """
        cost_old = np.inf
        self.autoselect_N = False
        self._N, N = 2, self._N
        cost_new = self.purchase_cost
        self._summary()  # 설계 다시 계산

        while cost_new < cost_old:
            self._N += 1
            self._summary()
            cost_old = cost_new
            cost_new = self.purchase_cost

        # 복원
        self._N, N = N, self._N - 1
        self.autoselect_N = True
        return N

    # ========================================================================
    # 시뮬레이션 메서드
    # ========================================================================

    def _run(self):
        """
        배치 반응 시뮬레이션 수행

        이 메서드는 반드시 서브클래스에서 구현되어야 합니다.
        입구 스트림을 받아 반응을 진행하고 출구 스트림을 설정합니다.

        기본 구현: inlet을 effluent로 복사 (반응 없음)

        Notes
        -----
        서브클래스에서 override할 때:
        - self.outs[0] (vent): 분리된 가스 설정
        - self.outs[1] (effluent): 반응 후 액체 생성물 설정
        - self.Hnet: 순 열 교환량 설정 (필요시)

        Examples
        --------
        >>> def _run(self):
        ...     effluent = self.effluent
        ...     effluent.mix_from(self.ins)
        ...     # 반응 진행
        ...     reaction.force_reaction(effluent)
        ...     # 기체 분리
        ...     vent = self.vent
        ...     vent.empty()
        ...     vent.receive_vent(effluent, energy_balance=False)
        """
        # 기본 구현: inlet을 effluent로 복사 (반응 없음)
        vent, effluent = self.outs
        effluent.mix_from(self.ins)

        # 온도, 압력 설정
        effluent.T = self.T
        effluent.P = self.P

        # 가스 출구는 비움 (서브클래스에서 설정 예상)
        vent.empty()
        vent.P = self.P
        vent.T = self.T

    # ========================================================================
    # 설계 메서드
    # ========================================================================

    def _design(self):
        """
        배치 반응기 크기 및 설계 계산

        이 메서드는 주어진 조건(tau, N, V 등)에서 필요한 반응기 개수와
        각 반응기의 크기를 계산합니다.

        Design Results
        ---------------
        Reactor volume : float
            각 반응기의 부피 (m³)
        Cycle time : float
            사이클 시간 = tau + tau_0 (hr)
        Batch time : float
            배치당 소요 시간 (hr)
        Loading time : float
            재료 주입 시간 (hr)
        Total dead time : float
            총 대기 시간 (hr)
        Number of reactors : int
            설계 반응기 개수
        Reactor duty : float
            필요 열 교환량 (kJ/hr)
        Recirculation flow rate : float
            순환 유량 (m³/hr)

        Notes
        -----
        반응기 개수 계산 로직:

        1. autoselect_N=True 인 경우:
           최저 비용의 N을 자동 선택

        2. V (목표 부피) 지정 시:
           N = (v_0 / V / V_wf) * (tau + tau_0) + 1

        3. N (반응기 개수) 지정 시:
           N을 직접 사용
        """
        effluent = self.effluent
        v_0 = effluent.F_vol           # 출구 부피 유량 (m³/hr)
        tau = self._tau                # 반응 시간
        tau_0 = self.tau_0             # 청소/언로딩 시간
        V_wf = self.V_wf               # 작동 부피 비율
        Design = self.design_results

        # ====== 반응기 개수 결정 ======
        if self.autoselect_N:
            # 최저 비용 반응기 개수 자동 선택
            N = self.N_at_minimum_capital_cost
        elif self.V:
            # 목표 부피 기반 반응기 개수 계산
            # N = (v_0 / V / V_wf) * (tau + tau_0) + 1
            N = v_0 / self.V / V_wf * (tau + tau_0) + 1
            if N < self.Nmin:
                N = self.Nmin
            else:
                N = ceil(N)

            # Nmax 초과 확인
            if N > self.Nmax:
                raise ValueError(
                    f"필요 반응기 개수 {N}이 최대값 {self.Nmax}를 초과합니다. "
                    f"V (목표 부피)를 증가시키거나 tau를 감소시키십시오."
                )
        else:
            # N이 직접 지정된 경우
            N = self._N

        # ====== 설계 매개변수 계산 ======
        # size_batch 함수 호출: (부피, tau, tau_0, N, V_wf)
        Design.update(size_batch(v_0, tau, tau_0, N, V_wf))

        # 추가 설계 항목 저장
        Design['Number of reactors'] = N
        Design['Recirculation flow rate'] = v_0 / N  # 각 반응기당 순환 유량

        # 열 교환 부하 계산
        duty = self.Hnet                # 순 엔탈피 변화 (kJ/hr)
        Design['Reactor duty'] = duty

        # 열 유틸리티 추가
        self.add_heat_utility(duty, self.T)

    # ========================================================================
    # 비용 계산 메서드
    # ========================================================================

    def _cost(self):
        """
        배치 반응기 구성품별 비용 계산

        @cost 데코레이터에 의해 자동으로 baseline_purchase_costs가 계산됩니다.

        비용 항목 (5가지):
        1. Reactors (반응기): V^0.5 스케일
        2. Agitators (교반기): V^0.5 스케일
        3. Heat exchangers (열교환기): 열부하^0.7 스케일
        4. Cleaning in place: V^0.6 스케일
        5. Recirculation pumps (순환펌프): 유량^0.8 스케일

        Notes
        -----
        각 항목의 비용은 (기준 비용) × (파라미터/기준값)^지수 로 계산됨

        예시:
        Reactor 비용 = 844,000 × (V/3,785)^0.5 × N개
        """
        # @cost 데코레이터가 자동으로 baseline_purchase_costs를 계산합니다.
        # 이 메서드는 추가 비용 계산이 필요할 때 사용합니다.
        pass


# ============================================================================
# 사용 예시 (docstring에서 참고)
# ============================================================================

"""
Example Usage:

>>> from biosteam import Stream, System, settings
>>> from biosteam.units import CustomBioreactor
>>> import biosteam as bst

# 1. 기본 사용
>>> settings.set_thermo('sugar')  # Glucose, Water, Ethanol 포함
>>> feed = Stream('feed', Water=1.20e+05, Glucose=1.89e+03, units='kg/hr')
>>> R1 = CustomBioreactor('R1', ins=feed, outs=('vent', 'product'),
...                       tau=24, N=4, T=310)
>>> R1.simulate()
>>> print(f"반응기 부피: {R1.design_results['Reactor volume']:.1f} m³")
>>> print(f"총 비용: ${R1.purchase_cost:,.0f}")

# 2. 목표 부피 기반 설계
>>> R2 = CustomBioreactor('R2', ins=feed, outs=('vent', 'product'),
...                       tau=24, V=100, T=310)
>>> R2.simulate()
>>> print(f"필요 반응기 개수: {R2.design_results['Number of reactors']}")

# 3. 최저 비용 최적화
>>> R3 = CustomBioreactor('R3', ins=feed, outs=('vent', 'product'),
...                       tau=24, N=4, T=310)
>>> R3.autoselect_N = True
>>> R3.simulate()
>>> print(f"최적 반응기 개수: {R3.design_results['Number of reactors']}")

# 4. 반응 모델 추가 (서브클래스 예시)
>>> class FermentationReactor(CustomBioreactor):
...     def _init(self, tau, N=None, V=None, conversion=0.9, **kwargs):
...         super()._init(tau=tau, N=N, V=V, **kwargs)
...         self.conversion = conversion
...
...     def _run(self):
...         vent, effluent = self.outs
...         effluent.mix_from(self.ins)
...
...         # 글루코스 → 에탄올 + CO2 반응
...         reaction = bst.Reaction(
...             'Glucose -> 2Ethanol + 2CO2',
...             'Glucose',
...             self.conversion,
...             effluent.chemicals
...         )
...         reaction.force_reaction(effluent)
...
...         # CO2 분리
...         vent.empty()
...         vent.receive_vent(effluent, energy_balance=False)
"""
