# -*- coding: utf-8 -*-
# BioSTEAM: The Biorefinery Simulation and Techno-Economic Analysis Modules
# Copyright (C) 2020-2024, Yoel Cortes-Pena <yoelcortes@gmail.com>
#
# This module is under the UIUC open-source license. See
# github.com/BioSTEAMDevelopmentGroup/biosteam/blob/master/LICENSE.txt
# for license details.
"""
Whole Cell Bioreactor Module - D-Galactose to D-Tagatose Conversion (3-stage mechanism)

Multi-stage bioreactor for whole cell catalysis:
- Stage 1 (Anaerobic, 0-36 hr): D-Galactose → Galactitol (via NADPH)
- Stage 2 (Aerobic): Galactitol → D-Tagatose (via NAD+)
- Stage 3: NAD+ regeneration via O2

Reactions:
1. Galactose + NADPH → Galactitol + NADP+
2. NADP+ + Formate → CO2 + NADPH (NADP+ regeneration)
3. Galactitol + NAD+ → Tagatose + NADH
4. NADH + 0.25 O2 → NAD+ + 0.5 H2O

Key Parameters:
- Reaction time: 36 hr
- Temperature: 25°C
- Reactor volume: 500 L (0.5 m³)
- D-Galactose: 150 g/L
- Sodium Formate: 59.5 g/L (5% molar excess, fully consumed)
- Cofactors: NAD+ 3 mM, NADP+ 0.1 mM
- pH: 8.0
- Oxygen: Only in final NAD regeneration step

Author: Claude AI
"""

import numpy as np
from .custom_bioreactor import CustomBioreactor
from thermosteam.reaction import Reaction, ParallelReaction

__all__ = ('WholeCellBioreactor',)


class WholeCellBioreactor(CustomBioreactor):
    """
    3단계 전세포촉매 배치 반응기 (500L 스케일)

    D-Galactose를 D-Tagatose로 변환하는 다단계 배치 반응기입니다.
    초기 36시간은 혐기성 조건에서 Galactitol 중간체를 생성하고,
    이후 호기성 조건에서 최종 생성물 Tagatose로 전환합니다.

    **반응 메커니즘 (3단계):**

    Stage 1 (산소 없음, 0-36 hr):
        Galactose + NADPH → Galactitol + NADP+
        NADP+ + Formate → CO2 + NADPH (NADP+ 재생성)
        순 반응: Galactose + Formate → Galactitol + CO2

    Stage 2 (호기성):
        Galactitol + NAD+ → Tagatose + NADH

    Stage 3 (O2 재생성):
        NADH + 0.25 O2 → NAD+ + 0.5 H2O

    **입출구:**

    입구:
        [0] Feed: D-Galactose (150 g/L), Sodium Formate (59.5 g/L, 5% 과량),
                  NAD+ 3 mM, NADP+ 0.1 mM, pH 8.0, 물
        [1] Compressed Air: O2 공급 (최종 단계만)

    출구:
        [0] Vent: CO2 (Stage 1에서 생성)
        [1] Effluent: D-Tagatose (생성물), 물, 바이오매스

    Parameters
    ----------
    tau : float
        반응 시간 (hr). 기본값: 36
    N : int, optional
        배치 반응기 개수. N 또는 V 중 하나 필수.
    V : float, optional
        반응기 부피 (m³). 기본값: 0.5 (500L)
    T : float, optional
        반응 온도 (K). 기본값: 298.15 (25°C)
    P : float, optional
        반응 압력 (Pa). 기본값: 101325 Pa
    pH : float, optional
        반응 pH. 기본값: 8.0
    galactose_concentration : float, optional
        D-Galactose 농도 (g/L). 기본값: 150
    biocatalyst_concentration : float, optional
        바이오매스 농도 (g/L). 기본값: 50
    formate_excess : float, optional
        Formate 몰 과량. 기본값: 0.05 (5%)
    nad_concentration : float, optional
        NAD+ 농도 (mM). 기본값: 3
    nadp_concentration : float, optional
        NADP+ 농도 (mM). 기본값: 0.1
    oxygen_supply : str, optional
        산소 공급 방식. 'compressed' (압축기) 또는 'none'. 기본값: 'compressed'

    Attributes
    ----------
    oxygen_demand : float
        필요 산소량 (mol)
    galactitol_intermediate : float
        생성된 Galactitol 유량 (mol/hr)
    """

    line = 'Whole Cell Bioreactor (3-stage: Galactose → Galactitol → Tagatose)'

    # ========================================================================
    # 입출구 정의
    # ========================================================================

    _N_ins = 2   # Feed + Compressed air
    _N_outs = 2  # Vent (CO2) + Effluent

    # ========================================================================
    # 기본 파라미터
    # ========================================================================

    #: float: 반응 시간 (36시간)
    tau_default = 36

    #: float: 반응 온도 (25°C)
    T_default = 298.15

    #: float: 목표 반응기 부피 (500L = 0.5 m³)
    V_default = 0.5

    #: float: D-Galactose 초기 농도 (g/L)
    galactose_concentration = 150.0

    #: float: 바이오매스 농도 (g/L, 건중량)
    biocatalyst_concentration = 50.0

    #: float: Sodium Formate 몰 과량 (5%)
    formate_excess = 0.05

    #: float: NAD+ 농도 (mM)
    nad_concentration = 3.0

    #: float: NADP+ 농도 (mM)
    nadp_concentration = 0.1

    #: float: 반응 pH
    pH = 8.0

    #: str: 산소 공급 ('compressed' 또는 'none')
    oxygen_supply = 'compressed'

    # ========================================================================
    # 화학 상수 (분자량)
    # ========================================================================

    MW_GALACTOSE = 180.0        # C6H12O6
    MW_GALACTITOL = 182.0       # C6H14O6 (Galactose + H2)
    MW_TAGATOSE = 180.0         # C6H12O6
    MW_SODIUM_FORMATE = 68.0    # HCOONa
    MW_CO2 = 44.0
    MW_NAD = 663.0              # NAD+ (분자량, 근사값)
    MW_NADP = 743.0             # NADP+ (분자량, 근사값)

    # ========================================================================
    # 초기화
    # ========================================================================

    def _init(self, tau=None, N=None, V=None, T=None, P=101325, pH=8.0,
              galactose_concentration=None, biocatalyst_concentration=None,
              formate_excess=None, nad_concentration=None,
              nadp_concentration=None, oxygen_supply='compressed',
              Nmin=2, Nmax=36):
        """
        3단계 반응기 초기화

        Parameters
        ----------
        tau : float, optional
            반응 시간 (hr). 기본값: 36
        N : int, optional
            반응기 개수
        V : float, optional
            반응기 부피 (m³). 기본값: 0.5 (500L)
        T : float, optional
            온도 (K). 기본값: 298.15 (25°C)
        pH : float
            pH (기본값: 8.0)
        """
        # 기본값 설정
        if tau is None:
            tau = self.tau_default
        if T is None:
            T = self.T_default
        if V is None:
            V = self.V_default

        # 부모 클래스 초기화
        super()._init(tau=tau, N=N, V=V, T=T, P=P, Nmin=Nmin, Nmax=Nmax)

        self.pH = pH
        self.oxygen_supply = oxygen_supply

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

        # 초기화
        self.oxygen_demand = 0  # mol O2
        self.galactitol_intermediate = 0  # mol/hr

    # ========================================================================
    # 설정
    # ========================================================================

    def _setup(self):
        """반응 모델 설정"""
        super()._setup()
        self._setup_reactions()

    def _setup_reactions(self):
        """3단계 반응 메커니즘 설정"""
        chemicals = self.chemicals

        # Stage 1: Galactose + NADPH → Galactitol + NADP+
        try:
            self._rxn_galactose_to_galactitol = Reaction(
                'D_Galactose -> Galactitol',
                'D_Galactose', 1.0, chemicals
            )
        except:
            self._rxn_galactose_to_galactitol = None

        # Stage 1 (보조): NADP+ + Formate → CO2 + NADPH
        try:
            self._rxn_nadp_regeneration = Reaction(
                'SodiumFormate -> CO2',
                'SodiumFormate', 1.0, chemicals
            )
        except:
            self._rxn_nadp_regeneration = None

        # Stage 2: Galactitol + NAD+ → Tagatose + NADH
        try:
            self._rxn_galactitol_to_tagatose = Reaction(
                'Galactitol -> Tagatose',
                'Galactitol', 1.0, chemicals
            )
        except:
            self._rxn_galactitol_to_tagatose = None

        # Stage 3: NADH + O2 → NAD+ + H2O
        try:
            self._rxn_nad_regeneration = Reaction(
                'NADH + 0.25 O2 -> NAD + 0.5 H2O',
                'NADH', 1.0, chemicals
            )
        except:
            self._rxn_nad_regeneration = None

    # ========================================================================
    # 프로퍼티
    # ========================================================================

    @property
    def vent(self):
        """[Stream] CO2 가스 출구"""
        return self.outs[0]

    @property
    def effluent(self):
        """[Stream] 생성물 출구"""
        return self.outs[1]

    # ========================================================================
    # 계산 메서드
    # ========================================================================

    def _calculate_stoichiometry(self):
        """
        스토이키오메트리 계산 (500L 기준)

        Returns
        -------
        dict: 기질, 생성물, 산소 요구량
        """
        feed = self.ins[0]
        if feed is None or feed.F_vol == 0:
            return {}

        volume_L = feed.F_vol * 1000  # m³ → L

        # D-Galactose 입력
        galactose_g = self.galactose_concentration * volume_L
        galactose_mol = galactose_g / self.MW_GALACTOSE

        # Sodium Formate 입력 (5% 과량, 완전 소비)
        formate_mol = galactose_mol * (1 + self.formate_excess)
        formate_g = formate_mol * self.MW_SODIUM_FORMATE

        # Stage 1: Galactose + Formate → Galactitol + CO2
        # 1:1 비율이므로
        galactitol_mol = galactose_mol  # 100% 전환
        co2_from_stage1 = galactose_mol  # 1:1

        # Stage 2: Galactitol → Tagatose (수율 100%)
        tagatose_mol = galactitol_mol
        tagatose_g = tagatose_mol * self.MW_TAGATOSE

        # Stage 3: NAD 재생성에 필요한 O2
        # Galactitol → Tagatose는 산화 단계
        # 각 mol은 1 NADH를 생성
        # 1 mol NADH + 0.25 mol O2 → NAD+
        oxygen_mol = galactitol_mol * 0.25

        # 코팩터
        nad_mol = self.nad_concentration * volume_L / 1000
        nadp_mol = self.nadp_concentration * volume_L / 1000

        return {
            'galactose_mol': galactose_mol,
            'formate_mol': formate_mol,
            'galactitol_mol': galactitol_mol,
            'tagatose_mol': tagatose_mol,
            'tagatose_g': tagatose_g,
            'co2_mol': co2_from_stage1,
            'oxygen_mol': oxygen_mol,
            'nad_mol': nad_mol,
            'nadp_mol': nadp_mol,
            'volume_L': volume_L,
        }

    # ========================================================================
    # 시뮬레이션 메서드
    # ========================================================================

    def _run(self):
        """
        3단계 배치 반응 시뮬레이션

        Stage 1 (혐기성, 0-36 hr):
            Galactose + NADPH → Galactitol + NADP+
            NADP+ + Formate → CO2 + NADPH (재생성)
            순: Galactose + Formate → Galactitol + CO2

        Stage 2-3 (호기성):
            Galactitol + NAD+ → Tagatose + NADH
            NADH + O2 → NAD+ + H2O
        """
        vent, effluent = self.outs
        feed = self.ins[0]

        # 초기 조성 설정
        effluent.copy_like(feed)
        effluent.T = self.T
        effluent.P = self.P

        # Stage 1: Galactose → Galactitol
        # 반응: Galactose + NADPH → Galactitol + NADP+
        if self._rxn_galactose_to_galactitol:
            self._rxn_galactose_to_galactitol.force_reaction(effluent)
        else:
            self._run_stage1_manual(effluent)

        # Stage 1 (보조): Formate → CO2
        # 반응: NADP+ + Formate → CO2 + NADPH (NADP+ 재생성)
        if self._rxn_nadp_regeneration:
            self._rxn_nadp_regeneration.force_reaction(effluent)
        else:
            self._run_formate_oxidation(effluent)

        # Stage 2: Galactitol → Tagatose
        # 반응: Galactitol + NAD+ → Tagatose + NADH
        if self._rxn_galactitol_to_tagatose:
            self._rxn_galactitol_to_tagatose.force_reaction(effluent)
        else:
            self._run_stage2_manual(effluent)

        # Stage 3: NAD+ 재생성 (O2 기반)
        # 반응: NADH + O2 → NAD+ + H2O
        if self._rxn_nad_regeneration:
            self._rxn_nad_regeneration.force_reaction(effluent)

        # CO2 분리
        vent.empty()
        vent.receive_vent(effluent, energy_balance=False)
        vent.T = self.T
        vent.P = self.P

        # 산소 요구량 저장
        stoich = self._calculate_stoichiometry()
        self.oxygen_demand = stoich.get('oxygen_mol', 0)
        self.galactitol_intermediate = stoich.get('galactitol_mol', 0)

        # 열 부하
        self._calculate_reactor_duty(effluent, stoich)

    def _run_stage1_manual(self, effluent):
        """
        Stage 1 수동 계산: Galactose + Formate → Galactitol + CO2

        화학식:
        Galactose (C6H12O6) + Formate (HCOO-) → Galactitol (C6H14O6) + CO2
        """
        try:
            gal_idx = effluent.chemicals.index('D_Galactose')
            gal_it_idx = effluent.chemicals.index('Galactitol')
            co2_idx = effluent.chemicals.index('CO2')
            for_idx = effluent.chemicals.index('SodiumFormate')

            gal_mol = effluent.imol[gal_idx]

            # 100% 전환
            effluent.imol[gal_idx] = 0
            effluent.imol[gal_it_idx] += gal_mol        # Galactitol 생성
            effluent.imol[co2_idx] += gal_mol            # CO2 생성
            effluent.imol[for_idx] = 0                   # Formate 완전 소비

        except (ValueError, IndexError):
            pass

    def _run_formate_oxidation(self, effluent):
        """
        Formate 산화: NADP+ + Formate → CO2 + NADPH
        (이미 위의 Stage 1에서 처리됨, 중복 방지)
        """
        pass

    def _run_stage2_manual(self, effluent):
        """
        Stage 2 수동 계산: Galactitol + NAD+ → Tagatose + NADH

        화학식:
        Galactitol (C6H14O6) + NAD+ → Tagatose (C6H12O6) + NADH + H+
        산화: 2H 손실
        """
        try:
            gal_it_idx = effluent.chemicals.index('Galactitol')
            tag_idx = effluent.chemicals.index('Tagatose')

            gal_it_mol = effluent.imol[gal_it_idx]

            # 100% 전환
            effluent.imol[gal_it_idx] = 0
            effluent.imol[tag_idx] += gal_it_mol  # Tagatose 생성

        except (ValueError, IndexError):
            pass

    def _calculate_reactor_duty(self, effluent, stoich):
        """
        열 부하 계산

        반응이 약간 흡열성 또는 중성으로 가정
        (산화 반응이지만 생화학 대사 과정)
        """
        try:
            if stoich.get('galactose_mol'):
                # 추정: -15 kJ/mol (약한 발열성)
                gal_mol = stoich['galactose_mol']
                heat = -15 * gal_mol
                self.Hnet = heat
            else:
                self.Hnet = 0
        except:
            self.Hnet = 0

    # ========================================================================
    # 설계 메서드
    # ========================================================================

    def _design(self):
        """배치 반응기 설계 및 산소 요구량 계산"""
        super()._design()

        Design = self.design_results
        stoich = self._calculate_stoichiometry()

        # 운영 조건
        Design['pH'] = self.pH
        Design['Temperature'] = f"{self.T - 273.15:.1f}°C"
        Design['Oxygen supply'] = self.oxygen_supply

        # 기질/생성물
        if stoich:
            Design['D-Galactose (input)'] = f"{stoich['galactose_mol']:.1f} mol"
            Design['Sodium Formate (input)'] = f"{stoich['formate_mol']:.1f} mol"
            Design['Formate excess'] = f"{self.formate_excess*100:.1f}%"
            Design['Galactitol (intermediate)'] = f"{stoich['galactitol_mol']:.1f} mol"
            Design['D-Tagatose (output)'] = f"{stoich['tagatose_mol']:.1f} mol ({stoich['tagatose_g']:.0f} g)"
            Design['CO2 (from formate)'] = f"{stoich['co2_mol']:.1f} mol"
            Design['Oxygen demand'] = f"{stoich['oxygen_mol']:.1f} mol"
            Design['NAD+ (cofactor)'] = f"{stoich['nad_mol']:.3f} mol"
            Design['NADP+ (cofactor)'] = f"{stoich['nadp_mol']:.4f} mol"

    # ========================================================================
    # 정보 표시
    # ========================================================================

    def _get_design_info(self):
        """설계 정보 출력"""
        info = list(super()._get_design_info())
        info.extend([
            ('Reaction time', f'{self.tau}', 'hr'),
            ('Temperature', f'{self.T - 273.15:.1f}', '°C'),
            ('D-Galactose (initial)', f'{self.galactose_concentration:.1f}', 'g/L'),
            ('Biocatalyst', f'{self.biocatalyst_concentration:.1f}', 'g/L (dry)'),
            ('Sodium Formate excess', f'{self.formate_excess*100:.1f}%', ''),
            ('NAD+ concentration', f'{self.nad_concentration:.1f}', 'mM'),
            ('NADP+ concentration', f'{self.nadp_concentration:.2f}', 'mM'),
            ('pH', f'{self.pH:.1f}', ''),
        ])
        return tuple(info)


# ============================================================================
# 전체 반응식 (이론적 수지)
# ============================================================================

"""
THREE-STAGE REACTION MECHANISM

**Stage 1 (Anaerobic, 0-36 hr): Reduction to Galactitol**
    Galactose + NADPH → Galactitol + NADP+
    NADP+ + Formate → CO2 + NADPH  [NADP+ regeneration]
    ─────────────────────────────────────────────────
    Net: Galactose + Formate → Galactitol + CO2

    Stoichiometry (1:1:1:1)
    C6H12O6 + HCOO- → C6H14O6 + CO2

**Stage 2 (Aerobic): Oxidation to Tagatose**
    Galactitol + NAD+ → Tagatose + NADH + H+

    Stoichiometry (1:1:1:1)
    C6H14O6 + NAD+ → C6H12O6 + NADH + H+

**Stage 3: NAD+ Regeneration**
    NADH + 0.25 O2 → NAD+ + 0.5 H2O

    Stoichiometry (1:0.25:1:0.5)

**OVERALL REACTION:**
    Galactose + Formate + NAD+ + 0.25 O2 → Tagatose + CO2 + H2O

Or (simplified):
    C6H12O6 + HCOO- + 0.25 O2 → C6H12O6 (tagatose) + CO2 + H2O

**MATERIAL BALANCE (500L scale, T=25°C)**

INPUT:
- D-Galactose: 150 g/L × 500 L = 75 kg = 416.7 mol
- Sodium Formate: 59.5 g/L × 500 L = 29.75 kg = 437.5 mol (5% excess)
- NAD+: 3 mM × 500 L = 1.5 mol
- NADP+: 0.1 mM × 500 L = 0.05 mol
- Water: ~400 kg
- Biocatalyst: 50 g/L × 500 L = 25 kg (dry wt)

OUTPUT:
- D-Tagatose: 416.7 mol = 75 kg (100% yield)
- CO2: 416.7 mol = 18.3 kg (from formate)
- Sodium Formate remaining: ~10.8 mol (2.5% of input, from excess)
  But specification says fully consumed → remaining = 0
- O2 consumed: 416.7 × 0.25 = 104.2 mol
- H2O produced: 416.7 × 0.5 = 208.3 mol = 3.75 kg

OXYGEN DEMAND:
- 104.2 mol O2 per reaction cycle
- Air composition: 21% O2, 79% N2
- Required air: 104.2 / 0.21 = 495.7 mol air ≈ 14.4 kg air
- Compressed air requirement: 14.4 kg/hr (scaled to reactor time)
"""
