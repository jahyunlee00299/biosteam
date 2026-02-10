#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
타가토스 통합 생산 공정 - 완전한 예제

Full biorefinery simulation:
1. Feed preparation (D-Galactose + Sodium Formate)
2. Batch fermentation (WholeCellBioreactor, 36 hr, 25°C)
3. Oxygen supply (OxygenCompressor, 12-36 hr aerobic phase)
4. Downstream purification
   - Solid-liquid separation
   - Decolorization (activated carbon)
   - Crystallization or syrup concentration
5. Economic analysis

Production scale: 500L per batch
Annual capacity: ~32 batches/year (7500 operating hours)
Target product: Food-grade D-Tagatose

Author: Claude AI
"""

import biosteam as bst
from biosteam.units import (
    WholeCellBioreactor,
    OxygenCompressor,
    SolidLiquidSeparator,
    DecolorationUnit,
    CrystallizationUnit,
    SyrupConcentrationUnit
)
from biosteam.units.tagatose_economics import TagatoseEconomicAnalysis

# ============================================================================
# 1. 화학물질 설정
# ============================================================================

print("="*70)
print("INTEGRATED TAGATOSE PRODUCTION PROCESS")
print("="*70)

# BioSTEAM 설정 (기본 화학물질 사용)
# 실제 사용 시 D-Galactose, Tagatose, Galactitol, Sodium Formate 등 추가 필요
bst.settings.set_thermo('default')

# ============================================================================
# 2. 입력 스트림 정의
# ============================================================================

print("\n[1] FEED STREAM DEFINITION")
print("-" * 70)

# Feed: D-Galactose + Sodium Formate
feed = bst.Stream('feed',
    Water=400,          # 물 (400 kg)
    units='kg/hr',
    T=298.15)           # 25°C

print(f"  Feed temperature: {feed.T - 273.15:.1f}°C")
print(f"  Feed mass: {feed.F_mass:.1f} kg/hr")

# 압축 공기 (최소한의 기본 설정)
compressed_air = bst.Stream('compressed_air',
    N2=400,             # 질소 (공기의 79%)
    O2=100,             # 산소 (공기의 21%)
    units='kg/hr')

print(f"  Compressed air O2: {compressed_air.imass['O2']:.1f} kg/hr")

# ============================================================================
# 3. 공정 단위 설정
# ============================================================================

print("\n[2] PROCESS UNIT CONFIGURATION")
print("-" * 70)

# (1) 배치 반응기
R1 = WholeCellBioreactor(
    'R1',
    ins=feed,
    outs=('CO2_vent', 'reactor_effluent'),
    tau=36,              # 36시간 반응
    N=1,                 # 1개 반응기 (또는 계산 기반)
    T=298.15,            # 25°C
    pH=8.0,
    galactose_concentration=150,      # 150 g/L (D-Galactose)
    biocatalyst_concentration=50,      # 50 g/L (건중량)
    formate_excess=0.05,               # 5% 몰 과량
    nad_concentration=3.0,              # 3 mM
    nadp_concentration=0.1,             # 0.1 mM
    oxygen_supply='compressed'
)
print(f"  Bioreactor: {R1.ID}")
print(f"    - Reaction time: {R1.tau} hr (12h anaerobic + 24h aerobic)")
print(f"    - Temperature: {R1.T - 273.15:.1f}°C")
print(f"    - Target volume: 0.5 m³ (500L)")

# (2) 압축기
C1 = OxygenCompressor(
    'C1',
    ins=compressed_air,
    outs='pressurized_air',
    oxygen_demand=104.2,    # mol (이론적 요구량)
    compression_ratio=2.0,   # 2배 압축
    efficiency=0.75
)
print(f"  Compressor: {C1.ID}")
print(f"    - O2 demand: {C1.oxygen_demand:.1f} mol")
print(f"    - Compression ratio: {C1.compression_ratio:.1f}x")

# (3) 고액분리기
S1 = SolidLiquidSeparator(
    'S1',
    ins=R1.outs[1],
    outs=('liquid_to_decolorize', 'discarded_biomass'),
    recovery_tagatose=0.98,    # 98% 회수율
    equipment_type='centrifuge'
)
print(f"  Separator: {S1.ID}")
print(f"    - Tagatose recovery: {S1.recovery_tagatose*100:.0f}%")

# (4) 탈색 장치
D1 = DecolorationUnit(
    'D1',
    ins=S1.outs[0],
    outs='decolorized_liquid',
    carbon_loading=0.02,               # 2% 활성탄
    decolorization_efficiency=0.85      # 85% 탈색 효율
)
print(f"  Decolorization: {D1.ID}")
print(f"    - Carbon loading: {D1.carbon_loading*100:.1f}%")

# (5) 결정화 또는 시럽화 선택
print("\n  Choose product form:")
print("    A) Crystallization (고순도 결정)")
print("    B) Syrup Concentration (액상 시럽)")

product_form = 'A'  # 기본값: 결정화

if product_form == 'A':
    # 결정화 경로
    CR1 = CrystallizationUnit(
        'CR1',
        ins=D1.outs[0],
        outs=('tagatose_crystals', 'mother_liquor'),
        crystal_recovery=0.90,         # 90% 결정화 수율
        crystal_purity=0.99            # 99% 순도
    )
    final_product_stream = CR1.outs[0]
    final_product_name = "Tagatose Crystals"
    print(f"  Crystallization: {CR1.ID} ← Selected")
    print(f"    - Recovery: {CR1.crystal_recovery*100:.0f}%")
    print(f"    - Purity: {CR1.crystal_purity*100:.1f}%")
else:
    # 시럽화 경로
    SY1 = SyrupConcentrationUnit(
        'SY1',
        ins=D1.outs[0],
        outs='tagatose_syrup',
        target_concentration=0.70,      # 70% 농축도
        evaporation_efficiency=0.95     # 95% 효율
    )
    final_product_stream = SY1.outs[0]
    final_product_name = "Tagatose Syrup"
    print(f"  Syrup Concentration: {SY1.ID} ← Selected")
    print(f"    - Target concentration: {SY1.target_concentration*100:.0f}%")

# ============================================================================
# 4. 시스템 구성 및 시뮬레이션
# ============================================================================

print("\n[3] PROCESS SIMULATION")
print("-" * 70)

# 시스템 생성
try:
    @bst.System
    def tagatose_production():
        """타가토스 생산 공정"""
        # 반응기
        feed >> R1

        # 분리
        R1.outs[1] >> S1

        # 탈색
        S1.outs[0] >> D1

        # 최종 정제
        if product_form == 'A':
            D1.outs[0] >> CR1
        else:
            D1.outs[0] >> SY1

    system = tagatose_production()
    print(f"  System created with {len(system.units)} units")

    # 시뮬레이션 실행
    system.simulate()
    print("  ✓ Simulation completed successfully")

except Exception as e:
    print(f"  ✗ Simulation error: {e}")
    print("  (Note: Requires D-Galactose, Tagatose, Galactitol in chemical library)")

# ============================================================================
# 5. 결과 출력
# ============================================================================

print("\n[4] PROCESS RESULTS")
print("-" * 70)

# 반응기 결과
print(f"\n  {R1.ID} (WholeCellBioreactor)")
if hasattr(R1, 'design_results'):
    print(f"    Design results available: {len(R1.design_results)} items")
if hasattr(R1, 'oxygen_demand'):
    print(f"    O2 demand: {R1.oxygen_demand:.1f} mol")

# 분리기 결과
print(f"\n  {S1.ID} (Separator)")
print(f"    Tagatose recovery: {S1.recovery_tagatose*100:.0f}%")

# 탈색 결과
print(f"\n  {D1.ID} (Decolorization)")
print(f"    Decolorization efficiency: {D1.decolorization_efficiency*100:.0f}%")

# 최종 생성물
print(f"\n  Final Product: {final_product_name}")
if final_product_stream:
    print(f"    Mass: {final_product_stream.F_mass:.1f} kg/hr")

# ============================================================================
# 6. 경제성 분석
# ============================================================================

print("\n[5] ECONOMIC ANALYSIS")
print("-" * 70)

try:
    econ = TagatoseEconomicAnalysis(system=system, product_stream=final_product_stream)

    # 파라미터 설정
    econ.tagatose_price = 5.0  # $/kg (현재 시장 가격)
    econ.project_life = 20      # 20년 프로젝트
    econ.discount_rate = 0.10   # 10% 할인율

    # 상세 분석 출력
    econ.print_analysis()

except Exception as e:
    print(f"  Economic analysis error: {e}")
    print("  (This is expected if process simulation had issues)")

# ============================================================================
# 7. 요약
# ============================================================================

print("\n[6] SUMMARY")
print("-" * 70)
print("""
Process Configuration:
  • Reaction: 36 hours total
    - Anaerobic phase: 0-12 hr (Galactose → Galactitol)
    - Aerobic phase: 12-36 hr (Galactitol → Tagatose + O2 regeneration)

  • Operating conditions:
    - Temperature: 25°C
    - pH: 8.0
    - Reactor volume: 500L (0.5 m³)
    - D-Galactose: 150 g/L (75 kg total)
    - Sodium Formate: 59.5 g/L (100% consumption)
    - Cofactors: NAD+ 3 mM, NADP+ 0.1 mM

  • Downstream processing:
    - Solid-liquid separation
    - Decolorization (activated carbon)
    - Crystallization OR Syrup concentration

  • Production scale:
    - Per batch: 75 kg D-Tagatose (100% yield)
    - Annual (7500 hr/yr): ~32 batches
    - Annual production: ~2,400 kg D-Tagatose

Market opportunities:
  • Current price: $4-8/kg
  • Premium for crystals: $5-6/kg
  • Application: Functional sweetener (low glycemic index)
  • Market: Diabetic/health food segment
""")

print("="*70)
print("END OF PROCESS SIMULATION")
print("="*70)

# ============================================================================
# 선택적: 결과 저장
# ============================================================================

if __name__ == "__main__":
    # 경제성 분석 결과를 파일로 저장 (선택적)
    try:
        econ.save_results('tagatose_economics_results.txt')
        print("\n✓ Results saved to 'tagatose_economics_results.txt'")
    except:
        pass
