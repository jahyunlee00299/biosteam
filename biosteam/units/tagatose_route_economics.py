# -*- coding: utf-8 -*-
"""
D-Tagatose Production - Route-Specific Economic Analysis

라우트별 경제성 분석:
- Route A: 정제 D-Galactose 구매 (Step 3-7만, Step 2.5 없음)
- Route B: 홍조류 원물 통합 (Step 1-7, Step 2.5 음이온 수지 포함)

Author: Claude AI
Date: 2026-02-12
"""

from biosteam.units.tagatose_economics import TagatoseEconomicAnalysis

__all__ = ('RouteAEconomics', 'RouteBEconomics')


class RouteAEconomics(TagatoseEconomicAnalysis):
    """
    Route A: 정제 D-Galactose 구매 (기본 시나리오)

    Process: Step 3-7 (바이오촉매 + 정제/건조)
    - 입력: 정제 D-Galactose ($2.00/kg)
    - 특징: 고순도, 염분 미량, 즉시 반응 가능
    - Step 6: 양이온 교환기만 필요

    Expected Results:
    - Annual Production: 34,375 kg/year
    - OPEX: ~$493,912/year
    - Breakeven: $30.69/kg (OPEX only)
    """

    def __init__(self):
        """Route A 초기화"""
        super().__init__()

        # Route A 파라미터 (기본 설정 유지)
        self.route_name = "Route A: Purified D-Galactose"
        self.glucose_cost = 2.0    # $/kg (정제 D-Galactose)
        self.include_step_25 = False  # Step 2.5 없음

    def calculate_opex_annual(self):
        """
        Route A OPEX 계산

        기본 시나리오이므로 부모 클래스 그대로 사용
        - 원료: D-Galactose, Sodium Formate, E. coli, 코팩터
        - 다운스트림: 탈염 (양이온만), 건조
        """
        return super().calculate_opex_annual()

    def get_production_summary(self):
        """Route A 생산 요약"""
        batches_per_year = self.production_hours_per_year / 30  # 30h batch
        annual_tagatose = 110.0 * batches_per_year  # 110 kg/batch

        return {
            'route': self.route_name,
            'annual_production_kg': annual_tagatose,
            'batches_per_year': batches_per_year,
            'kg_per_batch': 110.0,
            'feed_source': 'Purified D-Galactose ($2.00/kg)',
            'process_steps': 'Step 3-7 (biocatalysis + purification + drying)',
            'desalting_type': 'Cation exchanger only',
            'step_25_included': False,
        }


class RouteBEconomics(TagatoseEconomicAnalysis):
    """
    Route B: 홍조류 원물 통합 (시나리오 1)

    Process: Step 1-7 (가수분해 → 중화 → 음이온수지 → 반응 → 정제 → 건조)
    - 입력: 홍조류 건조 바이오매스 ($0.75/kg)
    - 특징: 원료 비용 낮음, 정제 공정 추가
    - Step 2.5: 음이온 수지 교환 필수 (SO₄²⁻, 레불린산, 포름산 제거)
    - Step 6: 양이온 교환기만 (Step 2.5에서 이미 음이온 제거됨)

    Expected Results:
    - Annual Production: 28,219 kg/year (-17.9% vs Route A)
    - OPEX: ~$1,012,837/year
    - Breakeven: $35.88/kg (OPEX only)
    """

    def __init__(self):
        """Route B 초기화"""
        super().__init__()

        # Route B 파라미터
        self.route_name = "Route B: Red Algae Biomass + Step 2.5"

        # Step 1-2: 가수분해 & 중화
        self.algae_cost = 0.75          # $/kg (홍조류 건조 바이오매스)
        self.acid_hydrolysis_cost_per_kg_algae = 0.40  # H₂SO₄, 에너지
        self.neutralization_cost_per_kg_algae = 0.25   # NaOH, 여과재
        self.step_12_yield = 0.782      # 85% × 92% (가수분해 × 중화)

        # Step 2.5: 음이온 수지 교환
        self.anion_resin_cost_per_batch = 370.0  # $/배치 (음이온 수지)

        # Step 3-7는 기본과 동일하지만, D-Galactose 투입량 조정
        self.glucose_cost = 0.0  # Step 1-2에서 계산되므로 별도 비용 없음
        self.include_step_25 = True  # Step 2.5 포함

    def calculate_opex_annual(self):
        """
        Route B OPEX 계산

        기본 OPEX + Step 1-2 + Step 2.5
        """
        opex = super().calculate_opex_annual()

        # Step 1-2 비용 계산
        batches_per_year = self.production_hours_per_year / 30

        # 110 kg D-Galactose 도출에 필요한 홍조류 양
        # 110 kg ÷ 0.782 = 141 kg 홍조류 필요 (Step 1-2 수율 고려)
        algae_per_batch = 141.0  # kg

        # Step 1: 황산 가수분해
        hydrolysis_cost = (algae_per_batch * self.acid_hydrolysis_cost_per_kg_algae) * batches_per_year
        opex['Step 1: Acid Hydrolysis (H2SO4)'] = hydrolysis_cost

        # Step 2: 중화 & 여과
        neutralization_cost = (algae_per_batch * self.neutralization_cost_per_kg_algae) * batches_per_year
        opex['Step 2: Neutralization (NaOH)'] = neutralization_cost

        # Step 2.5: 음이온 수지 교환 (필수)
        anion_exchange_cost = self.anion_resin_cost_per_batch * batches_per_year
        opex['Step 2.5: Anion Exchange (SO4, levulinic, formic)'] = anion_exchange_cost

        # D-Galactose 비용 추가 (기존 코드는 $2.00/kg으로 계산했는데, Route B는 0으로 설정했으므로 보정)
        # 실제로는 Step 1-2에서 홍조류로부터 추출되므로, 여기서는 추가 구매 비용 없음
        # 기존 D-Galactose 비용 제거
        if 'D-Galactose' in opex:
            opex.pop('D-Galactose')

        # 홍조류 원료 비용 추가 (대체)
        algae_total_cost = algae_per_batch * self.algae_cost * batches_per_year
        opex['Raw Material: Algae Biomass'] = algae_total_cost

        # 총 OPEX 재계산
        opex['Total Annual OPEX'] = sum(
            v for k, v in opex.items() if k != 'Total Annual OPEX'
        )

        return opex

    def calculate_revenue_annual(self, product_concentration=None):
        """
        Route B 수익 계산

        Route B는 Step 1-2 수율 손실로 최종 산출량이 적음
        """
        if product_concentration is None:
            # Route B: Step 1-2 수율 고려
            # 110 kg D-Galactose 입력 (Step 3 기준)
            # 후처리 수율: 98% × 96% × 94% × 95% = 83.8% (vs 기본 ~75%)
            # 최종: 110 × 0.838 = 92.2 kg 타가토스/배치
            # 하지만 보수적으로 90.3 kg/batch 사용 (문서 기준)
            product_concentration = 90.3  # kg/배치

        batches_per_year = self.production_hours_per_year / 30
        annual_tagatose_kg = product_concentration * batches_per_year

        dry_powder_price = self.tagatose_price
        total_revenue = annual_tagatose_kg * dry_powder_price

        return {
            'Annual Tagatose (kg)': annual_tagatose_kg,
            'Dry Powder Yield (kg)': annual_tagatose_kg,
            'Dry Powder Price ($/kg)': dry_powder_price,
            'Dry Powder Revenue ($)': total_revenue,
            'Total Annual Revenue ($)': total_revenue,
        }

    def get_production_summary(self):
        """Route B 생산 요약"""
        batches_per_year = self.production_hours_per_year / 30
        annual_tagatose = 90.3 * batches_per_year  # 90.3 kg/batch (Step 1-2 수율 감안)

        return {
            'route': self.route_name,
            'annual_production_kg': annual_tagatose,
            'batches_per_year': batches_per_year,
            'kg_per_batch': 90.3,
            'feed_source': 'Red Algae Biomass ($0.75/kg)',
            'process_steps': 'Step 1-7 (hydrolysis + neutralization + anion exchange + biocatalysis + purification + drying)',
            'step_25_included': True,
            'step_25_purpose': 'Remove SO4²⁻, levulinic acid (13%), formic acid (5%)',
            'desalting_type': 'Cation exchanger only (anion removed in Step 2.5)',
            'step_12_yield': self.step_12_yield,
            'algae_per_batch_kg': 141.0,
        }
