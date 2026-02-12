# BioSTEAM Unit 구현 - 작업 이슈 및 사용자 입력 항목

구현 진행 중 **사용자가 직접 입력/수정해야 할 항목**들을 기록한 문서입니다.

---

## Issue #1: Thermo 데이터베이스 화학물질 분자량 확인

**상태**: 🔴 대기중
**담당**: 사용자 (입력 필요)
**파일**: `biosteam/thermo/tagatose_thermo.py`

### 문제
BioSTEAM Thermo 생성 시 각 화학물질의 정확한 분자량 필요

### 필요 정보 (사용자 입력)
```python
# 다음 화학물질의 분자량을 확인하고 입력해주세요:

chemicals = {
    'D-Galactose': ???,      # 현재: 180.16 (확인 필요)
    'D-Tagatose': ???,       # 현재: 180.16 (확인 필요)
    'LevulinicAcid': ???,    # 현재: 116.12 (확인 필요)
    'FormicAcid': ???,       # 현재: 46.03 (확인 필요)
    'SodiumFormate': ???,    # 현재: 68.01 (확인 필요)
    'ActivatedCarbon': ???,  # 구조 불정 (단순화 필요?)
    'E.coli': ???,           # 생물학적 물질 (특수 처리)
    'NADplus': ???,          # 현재: 미입력
    'NADPplus': ???,         # 현재: 미입력
}
```

### 체크리스트
- [ ] 분자량 확인 (NIST, PubChem 등)
- [ ] BioSTEAM 호환 가능 화학물질인지 확인
- [ ] 비표준 물질 (E.coli, ActivatedCarbon) 처리 방안 결정

### 예상 소요시간
- 15-30분

---

## Issue #2: Unit 기본값 (Hardcode) 확인 및 조정

**상태**: 🟡 진행중
**담당**: 사용자 + 개발자
**파일**: `biosteam/units/tagatose_process_units.py`

### 문제
각 Unit의 기본값들이 tagatose_economics.py와 일치하는지 확인

### 확인할 항목

#### BiocatalysisReactor (Step 3)
```python
✓ conversion = 0.98              # 전환율 (맞음)
✓ temperature = 37               # 온도 (맞음)
✓ volume = 1000                  # 배치 부피 (맞음)
✓ power = 3.0 kW                 # 전력 (확인 필요: 3 + 2 + 2 = 7 kW인가?)
? purchase_cost = 225000         # 자본비 (맞음)

필요 확인:
- [ ] 실제 전력 소비: agitation/aeration/cooling 합계 확인
- [ ] 배치 시간: 16h 혐기 + 8h 호기 = 24h? 아니면 다른가?
```

#### CellSeparator (Step 4)
```python
? removal_efficiency = 0.98      # 제거 효율 (확인 필요)
? purchase_cost = 25000          # 자본비 (확인 필요)
? power = 2.0 kW                 # 전력 (확인 필요)
```

#### Decolorization (Step 5)
```python
? recovery = 0.96                # 회수율 (확인 필요)
? purchase_cost = 20000          # 자본비 (확인 필요)
? power = 0.5 kW                 # 전력 (확인 필요)
```

#### Desalting (Step 6)
```python
? removal_efficiency = 0.94      # 제거 효율 (확인 필요)
? purchase_cost = 50000          # 자본비 (확인 필요)
? power = 1.0 kW                 # 전력 (확인 필요)
```

#### Dryer (Step 7)
```python
? recovery = 0.95                # 회수율 (확인 필요)
? moisture_content = 0.03        # 최종 수분 (확인 필요)
? purchase_cost = 80000          # 자본비 (확인 필요)
? power = 3.0 kW                 # 전력 (확인 필요)
```

### 체크리스트
- [ ] tagatose_economics.py와 값 비교
- [ ] 각 Unit별 파라미터 확인/수정
- [ ] 필요시 값 업데이트

### 예상 소요시간
- 30-60분

---

## Issue #3: Route A/B 스트림 입력값 확인

**상태**: 🟡 진행중
**담당**: 사용자 + 개발자
**파일**: `tagatose_route_a_system.py`, `tagatose_route_b_system.py`

### 문제
각 Route의 입력 스트림 값이 정확한지 확인

### Route A 입력값 확인
```python
# 현재 값:
feed_galactose = 110.0 kg/hr     # D-Galactose (맞음?)
feed_cells = 20.0 kg/hr           # E.coli DCW (맞음?)
feed_formate = 44.0 kg/hr         # Sodium Formate (맞음?)

필요 확인:
- [ ] D-Galactose: 110 kg/hr이 맞는가? (110 g/L × 1000L = 110 kg 기준)
- [ ] E.coli: 20 kg/hr가 맞는가? (20 g/L × 1000L = 20 kg 기준)
- [ ] Sodium Formate: 44 kg/hr이 맞는가? (화학양론 기준)
```

### Route B 입력값 확인
```python
# 현재 값:
feed_algae = 141.0 kg/hr          # 홍조류 바이오매스
feed_acid = 14.1 kg/hr            # H2SO4
feed_base = 8.81 kg/hr            # NaOH

필요 확인:
- [ ] 홍조류: 141 kg/hr가 맞는가? (110 kg D-Gal ÷ 0.782 yield = 141 kg 기준)
- [ ] H2SO4: 14.1 kg/hr가 맞는가? (141 kg × 0.1 = 14.1 kg 기준)
- [ ] NaOH: 8.81 kg/hr가 맞는가? (141 kg × 0.0625 = 8.8 kg 기준)
```

### 체크리스트
- [ ] Route A 입력값 확인/수정
- [ ] Route B 입력값 확인/수정
- [ ] 화학양론 재확인 필요시 수정

### 예상 소요시간
- 20-30분

---

## Issue #4: Unit 물질 수지 검증 (실제 테스트 후)

**상태**: 🔴 CRITICAL - 심각한 스케일링 문제 발견!
**담당**: 개발자 + 사용자
**파일**: `tagatose_route_a_system.py`, `tagatose_route_b_system.py`

### 테스트 결과 (2026-02-12)
✅ 시스템 성공적으로 실행됨
❌ 물질 수지 스케일링 오류 발견 (18-36배 과다)
⚠️ 자본비 할당 실패 (BioSTEAM 속성 이슈)

### 발견된 문제들

#### Problem #4A: 심각한 스케일링 오류 (CRITICAL)

**Route A 테스트 결과**:
- 예상 입력: 110 kg D-Galactose + 890 kg Water = 1,000 kg/hr
- 실제 입력: 35,850.7 kg/hr (**35.85배 과다**)
- 예상 생성물: ~82 kg/hr (110×0.75 수율)
- 실제 생성물: 17,678.9 kg/hr (**215배 과다**)

**Route B 테스트 결과**:
- 예상 입력: 141 kg 홍조류
- 실제 입력: 2,540.2 kg/hr (**18배 과다**)
- 예상 생성물: ~80 kg/hr
- 실제 생성물: 1,240.4 kg/hr (**15.5배 과다**)

**근본 원인 (가설)**:
1. 배치 크기 / 시간 단위 변환 오류
2. BioSTEAM 자동 스케일링 (배치 → 연간)
3. 시간 단위 해석 차이 (시간당 vs 배치)

**영향도**:
- ❌ 경제성 분석 신뢰 불가
- ❌ 생산량 추정 무효
- ⚠️ 공정 흐름도는 유효하나 스케일 잘못됨
- ✅ 전력 소비 정확함

**해결 방법**:
- [ ] 배치 시간 파라미터 재검토
- [ ] Stream 초기화 파라미터 확인
- [ ] BioSTEAM 배치 vs 연속 운영 문서 검토
- [ ] 스케일 1:1 조정 또는 원인 파악

#### Problem #4B: 자본비 할당 실패 (MEDIUM)

**증상**:
- BioSTEAM Unit.purchase_cost는 읽기 전용 속성
- 모든 자본비 할당 제거됨 → CAPEX = $0 보고됨
- 장비 사이징(부피, 전력)은 정확함

**해결 방법**:
- [ ] BioSTEAM Cost object API 사용
- [ ] 또는 외부 경제 모듈에서 비용 계산
- [ ] tagatose_route_economics.py와 동기화

#### Problem #4C: Thermo 데이터베이스 제한 (MEDIUM)

**현재 상태**:
- 'Glucose'를 D-Galactose/D-Tagatose 대체물로 사용
- 사용자 화학물질 모두 제거됨
- Fallback: [Water, Glucose, H2SO4, NaOH] 만 사용

**미추적 항목**:
- 설탕 개별 전환 (D-Galactose → D-Tagatose)
- 부산물 생성 (levulinic acid, formic acid)
- 보조인자 (NAD+, NADP+)
- 세포 바이오매스

**해결 방법**:
- [ ] 사용자 화학물질 등록 (D-Galactose, D-Tagatose)
- [ ] 부산물 추적 활성화
- [ ] 보조인자 추적 추가

### 체크리스트
- [ ] Route A 시스템 시뮬레이션 실행
- [ ] 최종 생성물 검증 (27,500 kg/year 예상)
- [ ] Route B 시스템 시뮬레이션 실행
- [ ] 최종 생성물 검증 (22,575 kg/year 예상)
- [ ] 결과가 경제 모델과 일치 (±5%)

### 예상 소요시간
- 1-2시간 (시뮬레이션 + 디버깅)

---

## Issue #5: 경제성 모델과 Unit 비용 통합

**상태**: 🟠 보류중 (Unit 구현 후)
**담당**: 개발자 + 사용자 (검증)
**파일**: `tagatose_route_economics.py` (참고용)

### 문제
Unit의 CAPEX가 RouteAEconomics의 값과 일치하는지 확인

### 비용 항목 확인
```python
# Route A 예상 CAPEX ($682,000):
BiocatalysisReactor:   $225,000   (실제값: ?)
CellSeparator:         $ 25,000   (실제값: ?)
Decolorization:        $ 20,000   (실제값: ?)
Desalting:             $ 50,000   (실제값: ?)
Dryer:                 $ 80,000   (실제값: ?)
--- 소계:               $400,000
간접비 (40%):          $160,000
운영자본 (15%):        $ 60,000
--- 합계:               $620,000

필요 확인:
- [ ] 각 Unit의 purchase_cost 값 확인
- [ ] 간접비/운영자본 계산 일치 확인
- [ ] 최종 CAPEX ±10% 이내?
```

### 체크리스트
- [ ] Unit별 CAPEX 검증
- [ ] 경제 모델과의 일치도 확인 (±10%)
- [ ] 불일치시 원인 파악 및 수정

### 예상 소요시간
- 30-60분

---

## Issue #6: BioSTEAM 호환성 문제 처리

**상태**: 🔴 대기중 (구현 중 발생시)
**담당**: 사용자 + 개발자
**파일**: 다양 (발생시마다)

### 예상 문제 및 해결책

#### 문제 1: Thermo 데이터베이스 화학물질 미등록
```
Error: UndefinedChemicalAlias: 'D_Galactose'

해결책:
1. BioSTEAM 기본 화학물질 DB에서 이름 찾기
   예: 'Glucose' 대신 'D-Glucose' 사용
2. 또는 표준명 사용 (NIST 기준)
3. 또는 비표준 물질은 간단히 처리
```

#### 문제 2: Stream 생성 실패
```
Error: AttributeError: thermo 설정 없음

해결책:
1. 파일 상단에 thermo 설정 필수:
   from biosteam.thermo.tagatose_thermo import tagatose_thermo
   tmo.settings.set_thermo(tagatose_thermo)
```

#### 문제 3: Unit 연결 오류
```
Error: Unit inlet/outlet 불일치

해결책:
1. 스트림 개수 확인 (ins/outs 개수)
2. 스트림 순서 확인
3. 필요시 Mixer 추가
```

### 체크리스트
- [ ] 발생시마다 이슈로 기록
- [ ] 해결책 문서화
- [ ] 같은 문제 반복 방지

### 예상 소요시간
- 상황에 따라 다름 (30분-2시간)

---

## Issue #7: 문서작성 및 주석 추가

**상태**: 🟠 보류중 (구현 완료 후)
**담당**: 사용자 + 개발자
**파일**: 모든 Python 파일

### 필요 문서

#### 7.1 코드 주석
```python
# 각 Unit에 필요한 주석:
- [ ] 클래스 docstring (목적, 입/출력)
- [ ] 메서드별 docstring (_run, _design, _cost)
- [ ] 방정식 설명 (물질 수지 공식)
- [ ] 파라미터 의미 설명
```

#### 7.2 사용자 가이드
```markdown
- [ ] Route A/B 시스템 생성 튜토리얼
- [ ] 파라미터 수정 방법
- [ ] 결과 해석 방법
- [ ] 문제 해결 가이드
```

#### 7.3 API 문서
```markdown
- [ ] Unit 클래스별 문서
- [ ] 메서드 시그니처 설명
- [ ] 예시 코드
```

### 체크리스트
- [ ] 모든 Unit에 docstring 추가
- [ ] 사용자 가이드 작성
- [ ] README 업데이트

### 예상 소요시간
- 2-3시간

---

## 요약 테이블

| Issue | 상태 | 파일 | 진행상황 |
|-------|------|------|---------|
| #1 Thermo | 🟡 진행 | thermo | Fallback 구현 (부분) |
| #2 Units | ✅ 완료 | units | 8개 Unit 구현 완료 |
| #3 Systems | ✅ 완료 | systems | Route A/B 시스템 구현 |
| #4A 스케일링 | 🔴 CRITICAL | streams | 입력값 18-36배 과다 |
| #4B CAPEX | 🟡 진행 | units | purchase_cost 이슈 |
| #4C Thermo | 🟡 진행 | thermo | 사용자 화학물질 제한 |
| #5 경제 | 🟠 보류 | econ | 스케일 문제 후 진행 |
| #6 호환성 | ✅ 완료 | units | power_utility 수정 |
| #7 문서 | 🟠 보류 | docs | 구현 완료 후 진행 |

**전체 진행도**: 40% (기본 구현) / 0% (스케일 해결)

**긴급 이슈**: 스케일링 오류로 경제성 분석 불가능

---

## 진행 순서

```
1️⃣  Issue #1: Thermo DB 화학물질 확인 (사용자)
         ↓
2️⃣  Issue #2: Unit 기본값 확인 (혼합)
         ↓
3️⃣  Issue #3: 스트림 입력값 확인 (혼합)
         ↓
4️⃣  Thermo/Unit/System 구현 (개발자)
         ↓
5️⃣  Issue #4: Unit 물질 수지 검증 (혼합)
         ↓
6️⃣  Issue #5: 경제성 통합 검증 (혼합)
         ↓
7️⃣  Issue #6: BioSTEAM 호환성 문제 (필요시)
         ↓
8️⃣  Issue #7: 문서작성 (혼합)
         ↓
✅ 완료!
```

---

**작성일**: 2026-02-12
**상태**: 진행중
**최종 검토**: 필요시 업데이트
