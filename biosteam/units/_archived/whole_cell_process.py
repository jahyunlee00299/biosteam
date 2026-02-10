# -*- coding: utf-8 -*-
# BioSTEAM: The Biorefinery Simulation and Techno-Economic Analysis Modules
# Copyright (C) 2020-2024, Yoel Cortes-Pena <yoelcortes@gmail.com>
#
# This module is under the UIUC open-source license. See
# github.com/BioSTEAMDevelopmentGroup/biosteam/blob/master/LICENSE.txt
# for license details.
"""
Whole Cell Bioconversion Process Module

This module provides helper functions and example setups for integrating
WholeCellBioreactor with downstream separation processes.

Typical process flow:
    Feed → WholeCellBioreactor → [Vent: CO2]
                                 [Effluent] → Separator → [Liquid: Product]
                                                       → [Solid: Biocatalyst]

Author: Claude AI
"""

__all__ = ('create_whole_cell_process',)


def create_whole_cell_process(feed_stream, reactor_id='R1', separator_id='S1',
                              tau=24, N=4, kLa_option='medium',
                              conversion=0.85, split_dict=None):
    """
    전세포촉매 공정 생성 함수

    배치 반응기 + 고액분리 통합 프로세스를 만듭니다.

    Parameters
    ----------
    feed_stream : Stream
        입구 피드 스트림 (Galactose, Formate, Water 등 포함)
    reactor_id : str
        반응기 ID. 기본값: 'R1'
    separator_id : str
        분리기 ID. 기본값: 'S1'
    tau : float
        반응 시간 (hr). 기본값: 24
    N : int
        반응기 개수. 기본값: 4
    kLa_option : str
        산소 전달률 옵션: 'low', 'medium', 'high'. 기본값: 'medium'
    conversion : float
        갈락토스 전환율. 기본값: 0.85
    split_dict : dict, optional
        분리기 split 딕셔너리. None이면 자동 설정:
        - Tagatose, Galactose, Formate, Water → 액체
        - 고체 바이오매스 → 고체

    Returns
    -------
    reactor : WholeCellBioreactor
        반응기 유닛
    separator : Separator
        고액분리 유닛
    process : dict
        프로세스 딕셔너리: {'reactor': reactor, 'separator': separator}

    Examples
    --------
    >>> from biosteam import Stream, settings
    >>> from biosteam.units.whole_cell_process import create_whole_cell_process
    >>> settings.set_thermo('default')
    >>> feed = Stream('feed', Galactose=50, Formate=30, Water=1000,
    ...               units='kg/hr')
    >>> R1, S1, process = create_whole_cell_process(
    ...     feed, tau=24, N=4, kLa_option='medium'
    ... )
    >>> R1.simulate()
    >>> print(f"Product (Tagatose): {R1-S1.outs[0]}")
    """
    from biosteam.units import WholeCellBioreactor
    from biosteam.units.solids_separation import Separator

    # 1. 반응기 생성
    vent_id = f'{reactor_id}_vent'
    effluent_id = f'{reactor_id}_effluent'

    reactor = WholeCellBioreactor(
        reactor_id,
        ins=feed_stream,
        outs=(vent_id, effluent_id),
        tau=tau,
        N=N,
        kLa_option=kLa_option,
        conversion=conversion,
    )

    # 2. 고액분리기 설정
    if split_dict is None:
        # 기본 분리: 타가토스, 미반응 갈락토스, 포르메이트, 물은 액체로
        # 바이오매스는 고체로
        split_dict = {
            'Galactose': 1.0,   # 액체로 (미반응)
            'Tagatose': 1.0,    # 액체로 (생성물)
            'Formate': 1.0,     # 액체로 (미반응)
            'Water': 1.0,       # 액체로
            # 바이오매스는 지정하지 않으면 고체로 남음
        }

    liquid_id = f'{separator_id}_product'
    solid_id = f'{separator_id}_biocatalyst'

    separator = Separator(
        separator_id,
        ins=reactor.outs[1],  # 반응기 effluent 입력
        outs=(liquid_id, solid_id),
        split=split_dict
    )

    process = {
        'reactor': reactor,
        'separator': separator,
        'vent': reactor.outs[0],      # CO2 가스
        'product': separator.outs[0],  # 타가토스 포함 액체
        'biocatalyst': separator.outs[1],  # 회수 바이오매스
    }

    return reactor, separator, process


def print_process_summary(reactor, separator):
    """
    공정 요약 정보 출력

    Parameters
    ----------
    reactor : WholeCellBioreactor
        반응기 유닛
    separator : Separator
        고액분리 유닛
    """
    print("\n" + "="*70)
    print("WHOLE CELL BIOCONVERSION PROCESS SUMMARY")
    print("="*70)

    print("\n[1] REACTOR CONDITIONS")
    print(f"  Reaction time: {reactor.tau} hr")
    print(f"  Number of reactors: {reactor.design_results.get('Number of reactors', 'N/A')}")
    print(f"  Temperature: {reactor.T - 273.15:.1f}°C")
    print(f"  kLa option: {reactor.kLa_option} (kLa = {reactor.kLa:.0f} 1/hr)")
    print(f"  Galactose conversion: {reactor.conversion*100:.1f}%")
    print(f"  NAD regeneration efficiency: {reactor.nad_regeneration_efficiency*100:.1f}%")

    print("\n[2] FEED STREAM")
    if reactor.ins:
        feed = reactor.ins[0]
        print(f"  Total flow: {feed.F_mass:.1f} kg/hr")
        try:
            gal_idx = feed.chemicals.index('Galactose')
            for_idx = feed.chemicals.index('Formate')
            print(f"  Galactose: {feed.imol[gal_idx]:.1f} mol/hr")
            print(f"  Formate: {feed.imol[for_idx]:.1f} mol/hr")
        except:
            print("  (Detailed composition not available)")

    print("\n[3] PRODUCT STREAM (from Reactor)")
    if reactor.outs:
        effluent = reactor.outs[1]
        print(f"  Total flow: {effluent.F_mass:.1f} kg/hr")
        try:
            tag_idx = effluent.chemicals.index('Tagatose')
            co2_idx = effluent.chemicals.index('CO2')
            print(f"  Tagatose: {effluent.imol[tag_idx]:.1f} mol/hr")
            print(f"  CO2 (in vent): {reactor.outs[0].imol[co2_idx]:.1f} mol/hr")
        except:
            print("  (Detailed composition not available)")

    print("\n[4] SEPARATION")
    print(f"  Separator: {separator.ID}")
    print(f"  Liquid product outlet: {separator.outs[0].ID}")
    print(f"  Solid biocatalyst outlet: {separator.outs[1].ID}")

    print("\n[5] DESIGN SPECIFICATIONS")
    Design = reactor.design_results
    if Design:
        print(f"  Reactor volume: {Design.get('Reactor volume', 'N/A'):.1f} m³")
        print(f"  Cycle time: {Design.get('Cycle time', 'N/A'):.1f} hr")
        print(f"  Heat duty: {Design.get('Reactor duty', 'N/A'):.0f} kJ/hr")

    print("\n" + "="*70 + "\n")


# ============================================================================
# 산소 전달률 비교 함수
# ============================================================================

def compare_kLa_options():
    """
    산소 전달률(kLa) 옵션 비교

    서로 다른 산소 전달률에서의 NAD 재생성 효율을 비교합니다.
    """
    print("\n" + "="*70)
    print("OXYGEN TRANSFER RATE (kLa) OPTIONS - SHAKING FLASK CONDITIONS")
    print("="*70 + "\n")

    kLa_options = {
        'low': {
            'kLa': 50,
            'description': '낮은 폭기 (저속 shaker)',
            'efficiency': 0.7,  # 70% NAD 재생성
            'remarks': '제한적 산소 조건, 부분적 NAD 재생성'
        },
        'medium': {
            'kLa': 75,
            'description': '중간 폭기 (표준 shaker)',
            'efficiency': 0.85,  # 85% NAD 재생성
            'remarks': '최적 균형, 대부분의 경우 권장'
        },
        'high': {
            'kLa': 100,
            'description': '높은 폭기 (고속 shaker)',
            'efficiency': 1.0,  # 100% NAD 재생성
            'remarks': '충분한 산소 공급, 최대 전환율'
        },
    }

    for option, details in kLa_options.items():
        print(f"[{option.upper()}] {details['description']}")
        print(f"  kLa value: {details['kLa']:.0f} 1/hr")
        print(f"  NAD regen. efficiency: {details['efficiency']*100:.0f}%")
        print(f"  Remarks: {details['remarks']}")
        print()

    print("="*70 + "\n")


# ============================================================================
# 반응 화학식 참조
# ============================================================================

"""
WHOLE CELL CATALYST REACTIONS

1. MAIN REACTION (메인 반응)
   Galactose + Formate → Tagatose + CO2

   Stoichiometry:
   C6H12O6 + HCOO- + NADH + H+ → C6H12O6 (tagatose) + CO2 + NAD+ + H2O

   Galactose (L-galactose) → D-tagatose (rare sugar)
   포르메이트: electron donor 역할

2. COFACTOR BALANCE (코팩터 균형)
   - NADH: 메인 반응에서 소비
   - NADP/NADPH: 보조 반응에서 사용
   - NAD+: 산소를 통해 재생성

3. NAD REGENERATION (NAD 재생성)
   NADH + 0.25 O2 → NAD+ + 0.5 H2O

   - 산소 의존 반응
   - 산소 전달률(kLa)에 따라 재생성 효율 변화
   - kLa가 낮으면 부분적 재생성, 반응 지연

4. INTERMEDIATE (중간체)
   - Galactitol: 반응 경로 상 중간체
   - 축적되지 않음 (조건 적절 시)

CONVERSION FACTORS

Galactose MW: 180 g/mol
Tagatose MW: 180 g/mol
Formate MW: 45 g/mol (as formate ion, 46 for formic acid)
CO2 MW: 44 g/mol

Ideal stoichiometry (1:1:1:1):
100 kg Galactose → 100 kg Tagatose (theoretical)
               → 24.4 kg CO2
               → 73 kg Formate consumed

With typical losses & side reactions:
- Actual conversion: 80-90%
- Tagatose yield: 70-80% (theoretical)
- CO2 yield: corresponding to main reaction
"""
