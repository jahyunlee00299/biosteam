# BioSTEAM Unit 구현 요구사항 (한글)

## 개요

BioSTEAM을 이용한 D-Tagatose 생산 공정의 완전한 단위 공정(Unit) 구현 및 경제성 분석 통합.

**현재 상태**: Unit 구조 정의 완료, Thermo 설정 미완료
**목표**: Route A/B 시스템 완전 구현 및 시뮬레이션 실행

---

## 1. 열역학 설정 (필수)

### 1.1 맞춤형 Thermo 데이터베이스 생성

**파일**: `biosteam/thermo/tagatose_thermo.py`

```python
import thermosteam as tmo

# D-Tagatose 공정에 필요한 모든 화학물질 정의
chemicals = [
    # 물과 용매
    'Water',

    # 당류 및 생성물
    'D-Glucose',      # 180.16 g/mol
    'D-Galactose',    # 180.16 g/mol
    'D-Tagatose',     # 180.16 g/mol (갈락토스와 분자량 같음)
    'Glucose',        # D-Glucose의 별칭

    # 공정 화학물질
    'H2SO4',          # 황산 (가수분해용)
    'NaOH',           # 수산화나트륨 (중화용)
    'Na2SO4',         # 황산나트륨 (중화 생성물)

    # 부산물 및 불순물
    'LevulinicAcid',  # C5H8O3, 116.12 g/mol (가수분해 부산물)
    'FormicAcid',     # CH2O2, 46.03 g/mol (가수분해 부산물)
    'HCl',            # 염산 (미량)
    'NaCl',           # 염화나트륨 (미량)

    # 생촉매 및 코팩터
    'E.coli',         # 전세포 (건조 세포 중량)
    'NADplus',        # NAD+ 코팩터 (니코틴아미드)
    'NADPplus',       # NADP+ 코팩터

    # 기타 물질
    'SodiumFormate',  # CHO2Na, 68.01 g/mol (전자공여체)
    'ActivatedCarbon', # 활성탄 (탈색용)
]

# Thermo 객체 생성
def get_tagatose_thermo():
    """D-Tagatose 생산용 열역학 객체 반환"""
    thermo = tmo.Thermo(chemicals, cache=True)
    return thermo

# 내보내기
tagatose_thermo = get_tagatose_thermo()
tmo.settings.set_thermo(tagatose_thermo)
```

### 1.2 필요한 화학물질 특성

각 화학물질에 필요한 정보:
- **분자량** (g/mol)
- **밀도** (kg/m³)
- **비열용량** (J/kg·K)
- **생성 엔탈피** (J/mol)
- **물에서의 용해도**

**데이터 출처**:
- NIST Chemistry WebBook
- PubChem
- ChemSpider
- Aspen Plus 성질 패키지

**간단한 접근** (이 구현용):
- 수용성 당류는 물의 성질 사용
- 밀도: 1000-1100 kg/m³ (일정)
- 비열: 4.18 kJ/kg·K (물처럼)

---

## 2. 스트림 정의 (필수)

### 2.1 Route A 입력 스트림

```python
import thermosteam as tmo
from biosteam import Stream

# 1. 정제 D-Galactose 원료
feed_galactose = Stream(
    'D-Galactose_feed',
    D_Galactose=110.0,  # kg/hr (110 g/L × 1000 L)
    price=2.0,          # $/kg
    units='kg/hr',
)

# 2. E. coli 세포
feed_cells = Stream(
    'E.coli_cells',
    E_coli=20.0,        # kg/hr DCW
    price=50.0,         # $/kg
)

# 3. Sodium Formate (전자공여체)
feed_formate = Stream(
    'SodiumFormate',
    SodiumFormate=44.0, # kg/hr
    price=0.25,         # $/kg
)

# 4. 코팩터 (선택적)
feed_cofactors = Stream(
    'Cofactors',
    NADplus=1.0,        # mol/hr (1 mM × 1000 L)
    NADPplus=0.1,       # mol/hr (0.1 mM × 1000 L)
    price=0.0,          # 경제 모델에서 처리
)
```

### 2.2 Route B 입력 스트림

```python
# 1. 홍조류 바이오매스
feed_algae = Stream(
    'AlgaeBiomass',
    Algae=141.0,        # kg/hr (Step 1-2 수율 고려)
    price=0.75,         # $/kg
)

# 2. 황산 (가수분해용)
feed_acid = Stream(
    'H2SO4_hydrolysis',
    H2SO4=14.1,         # kg/hr
    price=0.05,         # $/kg
)

# 3. 수산화나트륨 (중화용)
feed_base = Stream(
    'NaOH_neutralization',
    NaOH=8.81,          # kg/hr
    price=0.50,         # $/kg
)

# 4-6. Route A와 동일 (세포, formate, 코팩터)
```

---

## 3. Unit 구현 상세 (필수)

### 3.1 BiocatalysisReactor (Step 3) - 우선순위 1

**구현해야 할 메서드**:

#### `_run()` - 물질 수지 계산
```python
def _run(self):
    """
    입출력 스트림 기반 물질 수지 계산

    핵심 방정식:
    D-Galactose → D-Tagatose (98% 전환)

    화학양론:
    - 1 mol D-Galactose → 1 mol D-Tagatose
    - 분자량 동일 (180.16 g/mol)
    - 질량 수지: 입력_갈락토스 × 0.98 = 출력_타가토스
    """

    feed = self.ins[0]  # D-Galactose 용액

    # 입력 질량 추출
    galactose_in = feed.imass['D-Galactose']  # kg/hr
    water_in = feed.imass['Water']

    # 생성물 계산
    tagatose_out = galactose_in * self.conversion  # 98%
    galactose_unreacted = galactose_in * (1 - self.conversion)  # 2%

    # 출력 스트림 설정
    product = self.outs[0]
    product.imass['D-Tagatose'] = tagatose_out
    product.imass['D-Galactose'] = galactose_unreacted
    product.imass['Water'] = water_in

    # 코팩터, 세포는 통과 (간단히)
    product.imass['E.coli'] = feed.imass.get('E.coli', 0)
```

#### `_design()` - 장비 크기 설계
```python
def _design(self):
    """
    생산 요구사항 기반 장비 크기 설계

    핵심 파라미터:
    - 부피: 1000 L (표준 배치)
    - 전력: 교반 (3 kW) + 통기 (2 kW) + 냉각 (2 kW)
    - 체류시간: 16시간 (혐기성) + 8시간 (호기성)
    - 온도: 37°C (유지)
    """

    # 배치 부피
    self.volume = 1000  # L

    # 전력 소비
    agitation_power = 3.0  # kW
    aeration_power = 2.0   # kW
    cooling_power = 2.0    # kW

    self.power_utility.consume(agitation_power + aeration_power + cooling_power)

    # 부피 기반 자본비 스케일링
    # 비용 상관식: C = base_cost × (V / V_ref)^0.6
    base_cost = 150000  # $ for 500L
    volume_ratio = self.volume / 500
    self.cost_scaled = base_cost * (volume_ratio ** 0.6)
```

#### `_cost()` - 자본비 및 운영비 추정
```python
def _cost(self):
    """
    장비 구매 비용 추정

    분류:
    - 1000L 반응기 용기: $150k
    - 교반/제어: $50k
    - 온도/pH 제어: $25k
    - 합계: $225k
    """

    self.purchase_cost = 225000  # $

    # 운영비는 tagatose_route_economics.py에서 처리
    # (E. coli, 코팩터, 유틸리티)
```

---

### 3.2 기타 Unit (우선순위 2-5)

#### CellSeparator (Step 4)
```python
필요한 계산:
- 세포 제거 효율: 98%
- 생성물 손실: ~2% (세포에 흡수, 잔류액)
- 전력: 원심분리 2 kW
- 장비 비용: $25k (원심분리기)

방정식:
  출력_질량 = 입력_질량 × 0.98
```

#### Decolorization (Step 5)
```python
필요한 계산:
- 활성탄 흡착용량: ~10 g/L
- 회수율: 96% (4% 손실)
- 전력: 0.5 kW (혼합)
- 장비 비용: $20k

방정식:
  출력_질량 = 입력_질량 × 0.96
```

#### Desalting (Step 6)
```python
필요한 계산:
- 이온 제거: 94% (Na+, SO4²⁻)
- 생성물 회수: 94%
- 수지 재생 비용: 경제 모델에서 처리
- 전력: 1 kW (수지를 통한 펌핑)
- 장비 비용: $50k

방정식:
  출력_타가토스 = 입력_타가토스 × 0.94
  출력_염분 = 입력_염분 × 0.05  (95% 제거)
```

#### Dryer (Step 7)
```python
필요한 계산:
- 최종 수분 함량: 3% (습식 기준)
- 회수율: 95% (드라이어에서 5% 손실)
- 건조 시간: 20시간, 65°C
- 전력: 3 kW 가열
- 장비 비용: $80k

에너지 수지:
  필요_열 = 제거_수량 × 잠열_증발
  = (입력_질량 × 수분_비율) × 2256 kJ/kg

방정식:
  출력_분말 = 입력_액체 × 회수율 × (1 / (1 - 수분_최종))
```

---

## 4. 시스템 통합 (필수)

### 4.1 Route A 시스템

**파일**: `tagatose_route_a_system.py` (업데이트 필요)

```python
# 필요한 컴포넌트:
1. Thermo 설정 (tagatose_thermo.py에서 import)
2. 스트림 정의 (Route A 입력)
3. Unit 인스턴스화 (U301-U305, 5개 Unit)
4. 시스템 생성
5. 시뮬레이션 실행
6. 결과 보고

# 핵심 통합 지점:
- U301.outs[0] → U302.ins[0]  (스트림 연결)
- 모든 Unit이 동일 thermo 객체 공유
- 각 Unit은 출력 T, P, 조성 업데이트
```

### 4.2 Route B 시스템

**파일**: `tagatose_route_b_system.py` (업데이트 필요)

```python
# 추가 컴포넌트:
1. Step 1: AcidHydrolysis (U201)
2. Step 2: Neutralization (U202)
3. Step 2.5: AnionExchange (U2_5)
4. Mixer: D-Galactose + 세포 + formate 혼합 (U301 전)

# 스트림 연결:
피드_홍조류 → U201 → U202 → U2_5 → Mixer → U301 → ... → U305
```

---

## 5. 검증 및 테스트 (필수)

### 5.1 Unit 테스트

```python
# 파일: tests/test_tagatose_units.py

def test_biocatalysis_reactor():
    """BiocatalysisReactor 물질 수지 테스트"""

    # 입력 스트림 생성
    feed = Stream('feed', D_Galactose=100, Water=900)

    # Unit 생성
    reactor = BiocatalysisReactor(
        ID='test_reactor',
        ins=feed,
        outs='product',
        conversion=0.98
    )

    # 시뮬레이션
    reactor._run()

    # 검증
    assert reactor.outs[0].imass['D-Tagatose'] == 98  # kg/hr
    assert reactor.outs[0].imass['D-Galactose'] == 2   # kg/hr
    assert abs(reactor.outs[0].F_mass - 902) < 0.1    # 질량 보존
```

### 5.2 시스템 테스트

```python
def test_route_a_system():
    """Route A 시스템 완전 테스트"""

    # 생성 및 시뮬레이션
    sys = create_route_a_system()
    sys.simulate()

    # 결과 확인
    product = sys.streams['D-Tagatose_powder']

    # 검증
    assert product.F_mass > 0  # 생성물 있음
    assert product.imass['D-Tagatose'] / product.F_mass > 0.95  # >95% 순도

    # 에너지 수지 확인
    total_power = sum(u.power_utility.power for u in sys.units)
    assert total_power < 15  # <15 kW 총 전력

    # 비용 확인
    total_capex = sum(u.purchase_cost for u in sys.units)
    assert total_capex > 500000  # >$500k
```

### 5.3 경제성 검증

```python
def test_economics_integration():
    """Unit 비용이 RouteAEconomics와 일치 확인"""

    # 시스템 실행
    sys = create_route_a_system()
    sys.simulate()
    system_capex = sum(u.purchase_cost for u in sys.units)

    # 경제 모델 실행
    route_a = RouteAEconomics()
    model_capex = route_a.calculate_capex()['Equipment Cost']

    # 5% 이내 일치
    assert abs(system_capex - model_capex) / model_capex < 0.05
```

---

## 6. 필요 문서 (필수)

### 6.1 코드 문서

- 모든 Unit 클래스 docstring (파라미터, 방정식, 가정)
- 공정 흐름도 (docstring의 ASCII art)
- 물질 수지 예시
- 문헌 참고문헌

### 6.2 사용자 가이드

- Route A/B 시스템 생성 방법
- 파라미터 수정 방법 (전환율, 온도 등)
- 결과 해석 방법
- 다른 시나리오 확장 방법 (스케일업, Route C 등)

---

## 7. 타임라인 및 노력 추정

| 작업 | 노력 | 소요일 |
|------|------|--------|
| 7.1 Thermo 설정 및 화학물질 | 2시간 | 0.25일 |
| 7.2 스트림 정의 | 1시간 | 0.1일 |
| 7.3 Unit 구현 (5개 Unit) | 8시간 | 1일 |
| 7.4 시스템 통합 (A + B) | 4시간 | 0.5일 |
| 7.5 테스트 및 검증 | 4시간 | 0.5일 |
| 7.6 문서작성 | 3시간 | 0.4일 |
| **합계** | **22시간** | **~3일** |

---

## 8. 위험 및 완화

| 위험 | 심각도 | 완화 방법 |
|------|--------|---------|
| Thermo DB 미완료 | 높음 | 단순화된 성질 사용 (물처럼) |
| Unit 전력 계산 부정확 | 중간 | 문헌값 사용 + 검증 테스트 |
| 스트림 연결 실패 | 중간 | 단일 Unit에서 시작, 순차 추가 |
| BioSTEAM API 변경 | 낮음 | 버전 고정 |
| 경제 모델 불일치 | 중간 | Unit 테스트로 비용 비교 |

---

## 9. 성공 기준

✅ **필수 요구사항**:
1. 8개 Unit 모두 구현 및 테스트
2. Route A 시스템 오류 없이 시뮬레이션
3. Route B 시스템 오류 없이 시뮬레이션
4. 질량 수지 보존 (입력 = 출력 ±1%)
5. 생산량이 경제 모델과 일치 (±5%)
6. 자본비가 경제 모델과 일치 (±10%)

✅ **권장 사항**:
7. 전력 소비가 현실적 (<15 kW)
8. 에너지 수지 검증
9. 완전한 문서작성
10. 예시 출력 및 사용 사례

✅ **추가 기능** (선택):
11. BioSTEAM 내 민감도 분석
12. 생산 최대화 최적화
13. biosteam.evaluation 통합

---

## 10. 다음 단계

1. **`biosteam/thermo/tagatose_thermo.py` 생성**
   - 화학물질 리스트 정의
   - 간단한 스트림으로 테스트
   - 분자량 검증

2. **BiocatalysisReactor 상세 구현**
   - 세 메서드 모두 코드화 (_run, _design, _cost)
   - Unit 테스트
   - 방정식 문서화

3. **나머지 4개 Unit 구현**
   - CellSeparator, Decolorization, Desalting, Dryer
   - 순차 테스트

4. **Route A/B 시스템 생성**
   - Unit 연결
   - 시뮬레이션
   - 경제 모델과 비교

5. **완전한 문서작성 및 배포**

---

## 참고자료

- **BioSTEAM 문서**: https://biosteam.readthedocs.io/
- **Thermosteam**: https://github.com/yoelcortes/thermosteam
- **D-Tagatose 공정**: D_TAGATOSE_PROCESS_OVERVIEW.md
- **경제 모델**: tagatose_route_economics.py

---

**작성자**: Claude AI
**작성일**: 2026-02-12
**상태**: 요구사항 문서 (한글)
