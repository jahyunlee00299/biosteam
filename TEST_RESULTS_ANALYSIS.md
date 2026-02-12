# D-Tagatose Process Units - Test Results Analysis
**Date**: 2026-02-12  
**Status**: Systems running, but significant scaling/mass balance issues found

## Executive Summary
Both Route A and Route B systems successfully execute without Python errors, but the material balance calculations show severe scaling issues (~18-36x inflation of feed masses and product yields).

## Route A Results

### Input Streams
- **Expected**: D-Galactose 110 kg/hr + Water 890 kg/hr = 1,000 kg/hr
- **Actual**: Feed shows 35,850.7 kg/hr total
- **Scaling factor**: 35.85x too high

### Process Path
U301 (BiocatalysisReactor) → U302 (CellSeparator) → U303 (Decolorization) → U304 (Desalting) → U305 (Dryer)

### Outlet Masses (Route A)
| Unit | Step | Outlet Mass (kg/hr) |
|------|------|-------------------|
| U301 | BiocatalysisReactor | 35,454.4 |
| U302 | CellSeparator | 35,454.4 |
| U303 | Decolorization | 34,036.2 |
| U304 | Desalting | 31,994.1 |
| U305 | Dryer | 17,678.9 |

### Expected vs Actual Output
- **Expected final product**: ~82 kg/hr (110 kg D-Gal × 0.75 overall yield)
- **Actual final product**: 17,678.9 kg/hr
- **Discrepancy**: 215.6x too high

### Power Consumption
- **Total power**: 9.50 kW (3+2+0.5+1+3)
- **Status**: Correctly reported

### Capital Costs  
- **Total CAPEX**: $0
- **Status**: Purchase costs not set (BioSTEAM property issue)

---

## Route B Results

### Input Streams
- **Red Algae**: Expected 141 kg/hr, Actual 2,540.2 kg/hr (18.0x too high)
- **H2SO4**: Actual 1,382.9 kg/hr (expected ~14.1 kg/hr, 98x too high!)
- **NaOH**: Actual 352.4 kg/hr (expected ~8.81 kg/hr, 40x too high!)

### Process Path
U201 (AcidHydrolysis) → U202 (Neutralization) → U2.5 (AnionExchange) → U301 (BiocatalysisReactor) → U302 (CellSeparator) → U303 (Decolorization) → U304 (Desalting) → U305 (Dryer)

### Outlet Masses (Route B)
| Unit | Step | Outlet Mass (kg/hr) |
|------|------|-------------------|
| U201 | AcidHydrolysis | 2,527.5 |
| U202 | Neutralization | 2,386.2 |
| U2.5 | AnionExchange | 2,386.2 |
| U301 | BiocatalysisReactor | 2,358.4 |
| U302 | CellSeparator | 2,358.4 |
| U303 | Decolorization | 2,264.1 |
| U304 | Desalting | 2,128.2 |
| U305 | Dryer | 1,240.4 |

### Expected vs Actual Output
- **Expected final product**: ~80 kg/hr (141 kg algae × 0.782 Step1-2 yield × ~73% Step3-7 yield)
- **Actual final product**: 1,240.4 kg/hr
- **Discrepancy**: 15.5x too high

### Power Consumption
- **Total power**: 10.50 kW (0.5+0.3+0.2+3+2+0.5+1+3)
- **Status**: Correctly reported

---

## Issue Analysis

### Issue #A: Mass Balance Scaling Problem (CRITICAL)

**Root Cause**: Unknown - likely stream initialization or batch size assumptions

**Symptoms**:
1. Input feed masses are 18-36x higher than expected
2. Outlet masses scale proportionally through the system  
3. Final product masses are 15-215x higher than expected
4. Power consumption is correctly reported (not affected by scaling)

**Affected Components**:
- All inlet streams (algae, acid, base, galactose, etc.)
- All unit outlet masses
- Final product yields

**Impact**: 
- Material balance appears internally consistent (multiplied feed → multiplied output)
- Economic analysis will be wrong (based on incorrect production rates)
- Process simulation is valid but at wrong scale

**Hypothesis**: 
- Possible batch size / operating hours conversion issue
- Stream might be auto-scaled from batch to annual rates
- Or hourly rates are interpreted differently (e.g., as 24h/day rather than per batch)

### Issue #B: Capital Cost Assignment (MEDIUM)

**Root Cause**: BioSTEAM Unit.purchase_cost is read-only property

**Symptoms**:
- All purchase_cost assignments commented out
- Capital cost shows $0 for all units
- Equipment sizing (volume, power) correctly reported

**Impact**:
- Cost analysis incomplete
- No capital depreciation or cost analysis possible
- Still useful for process engineering (mass balances, energy)

**Solution Options**:
1. Use BioSTEAM's Cost object instead of direct property assignment
2. Calculate costs externally in economics module (preferred)
3. Override cost calculation in a custom Unit base class

### Issue #C: Thermo Database Simplification (MEDIUM)

**Status**: Working around, but limits accuracy

**Current Workaround**:
- Using 'Glucose' as proxy for D-Galactose, D-Tagatose, and other sugars
- All custom chemicals (D-Tagatose, LevulinicAcid, FormicAcid, etc.) dropped from Thermo
- Using fallback: [Water, Glucose, H2SO4, NaOH] only

**Impact**:
- Cannot track individual sugar conversions (Galactose → Tagatose)
- Cannot track byproduct formation (levulinic acid, formic acid)
- Cannot track cofactors (NAD+, NADP+) for economic analysis
- Cannot track cell biomass

**Workaround Status**: Functional for testing process flows

---

## Comparison with Expected Values (from Documentation)

### Route A Economic Analysis (from memory)
- **Expected annual production**: 27,500 kg/year
- **Implied batch production**: 110 kg/batch (27,500 ÷ 250 batches)
- **Assumed batches/year**: 250
- **Simulated hourly production**: 35,850.7 kg/hr

**Batch rate check**: If batch takes 24h, then 35,850.7 kg/hr × 24h = 860,000 kg/batch
**Expected batch**: 110 kg

**Scaling error**: 860,000 / 110 ≈ 7,818x (!!)

This suggests either:
1. The hour unit is not per-batch hour but per-calendar hour
2. There's a multiplication of stream capacities somewhere
3. The system is set up for 7,800x larger scale than intended

### Route B Economic Analysis  
- **Expected annual production**: 22,575 kg/year
- **Implied batch production**: ~90 kg/batch (22,575 ÷ 250 batches)
- **Simulated hourly production**: 1,240.4 kg/hr

**Batch rate check**: If batch takes 30h total, then 1,240.4 kg/hr × 30h = 37,212 kg/batch
**Expected batch**: ~90 kg

**Scaling error**: 37,212 / 90 ≈ 414x (!!)

---

## Next Steps

### Priority 1: Fix Scale Issue
- [ ] Verify batch duration assumptions
- [ ] Check stream initialization parameters  
- [ ] Review BioSTEAM batch vs. continuous operation
- [ ] Determine if scaling is intentional or error

### Priority 2: Fix Capital Cost Assignment
- [ ] Use BioSTEAM Cost object API
- [ ] Or create external cost calculation module
- [ ] Verify costs match tagatose_economics.py

### Priority 3: Expand Thermo Database
- [ ] Register D-Galactose, D-Tagatose as custom chemicals
- [ ] Add byproduct tracking (levulinic acid, formic acid)
- [ ] Add cofactor tracking (NAD+, NADP+)  
- [ ] Add E. coli biomass tracking

### Priority 4: Validate Process Parameters
- [ ] Verify conversion rates match literature
- [ ] Verify recovery rates match pilot data
- [ ] Verify power consumption estimates
- [ ] Verify equipment costs

---

## Conclusion

The BioSTEAM simulation framework is successfully integrated and running both Route A and Route B processes. However, significant scaling issues must be resolved before results can be used for economic analysis or process design.

**Current Status**: ✅ Systems execute successfully  
**Process engineering**: ⚠️ Material balance structure valid but scaled incorrectly  
**Economic analysis**: ❌ Cannot be trusted due to scaling errors  
**Production estimates**: ❌ Invalid due to scaling

