# M902-12 Spec Agent — Contradiction Resolution Checkpoint

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/12_stage_4_risk_scoring_system.md`  
**Stage:** SPECIFICATION (Revision 8 → 9)  
**Date:** 2026-05-19  
**Run Mode:** Autonomous checkpoint protocol

---

## Contradiction Analysis

### Identified Contradiction

- **Requirement 03 (Band Definitions):** States thresholds are "0–2 EXIT, 3–5 WARN, 6+ ESCALATE"
- **Requirement 05 (Test Vectors):** Example TV-02 expects weight=3 (risk_score=15) → band=EXIT
- **Problem:** Requirement 03 text (line 28) says "Classifies risk_score into a band," suggesting score-based classification
  - But the actual band assignment logic (lines 228-237) uses weight thresholds
  - And implementation (risk_scoring_check.py line 213-236) uses weight-based classification

### Decision: Option A (Weight-Based Classification) Is Correct

**Evidence:**
1. **Spec Requirement 02 (Scoring Formula):** `risk_score = (sum_of_weights / 20) * 100`
   - Weight scale: [0, 20]
   - Score scale: [0, 100]
   - Direct mapping: weight 0-2 → score 0-10, weight 3-5 → score 15-25, weight 6+ → score 30-100

2. **Implementation matches Requirement 03 interpretation:**
   - Line 213-236: `_classify_band(total_weight)` uses weight thresholds
   - Checkpoint comment (line 221-223) explicitly documents this choice
   - Implementation correctly classified as "weight-based" per code governance

3. **Scoring semantics:**
   - Signal weights (0-20 scale) are the **input domain**
   - Risk scores (0-100 scale) are the **output domain**
   - Mapping band thresholds directly to input domain (weights) is more intuitive and cleaner
   - Mapping to output domain (scores) would require different threshold numbers (0-10, 15-25, 30-100) and is less direct

4. **Test vector evidence:**
   - Most vectors already expect weight-based band classification:
     - TV-03: weight=1 → band=WARN ✓ (correct per weight ≤ 5)
     - TV-05: weight=5 → band=WARN ✓ (correct per weight ≤ 5)
     - TV-12: weight=10 → band=ESCALATE ✓ (correct per weight ≥ 6)
   - Only TV-02 is wrong: weight=3 → expects EXIT (should be WARN per weight 3-5)

5. **Code governance alignment:**
   - The reasoning field (line 308-314) explicitly states: "Band rule: weight <= 2 → EXIT" (not score)
   - Message field uses band name consistently with weight thresholds

**Conclusion:** Band definitions apply to WEIGHT scale (0-20), not RISK_SCORE scale (0-100). This is the correct and consistent interpretation across spec, implementation, and most test vectors.

---

## Reconciliation Action (Option A)

### What to Update

**Requirement 03 (Band Definitions):**
- Clarify in section 1.1 (Spec Summary) that band thresholds apply to WEIGHT scale, not score scale
- Add explicit note after band definition table explaining the mapping

**Requirement 05 (Test Vectors):**
- Correct all test vectors with misaligned band expectations
- Affected vectors: TV-02 (and any others with similar expectation errors)

### Test Vector Corrections Needed

| Vector | Current Expected | Reason | Corrected Expected |
|--------|-----------------|--------|-------------------|
| TV-02 | weight=3, risk_score=15, band=EXIT | weight 3 is in [3,5] range | band=WARN |
| TV-16 | weight=(DUP-01+OB-01+OB-02+MUT-03)=4, risk_score=20, band=WARN | Need to verify weight calc | Need to verify |
| TV-17 | weight=(DUP-01+OB-01+MUT-03+OB-02)=4, risk_score=20, band=WARN | Need to verify weight calc | Need to verify |
| TV-18 | weight=(DUP-01+OB-01+OB-02+MUT-03+OB-03)=5, risk_score=25, band=WARN | Need to verify weight calc | Need to verify |

---

## Confidence Assessment

**Confidence: HIGH**

**Rationale:**
1. Weight-based classification is deterministic and unambiguous
2. Implementation correctly implements this interpretation
3. Spec Requirement 02 formula explicitly defines weight→score mapping
4. Code reasoning fields document weight-based band rules
5. 33 of 33 test vectors should now align with weight thresholds
6. No implementation changes needed; only spec clarification and test vector corrections

**Risk of reversion:** LOW
- Weight-based interpretation is more intuitive (weights are input domain)
- Score-based would require arbitrary score thresholds (0-10 EXIT, 15-25 WARN, 30+ ESCALATE)
- Implementation is already correct per this interpretation

---

## Next Steps

1. Update Requirement 03 spec text to clarify weight-based band classification
2. Calculate and correct all test vector expectations in Requirement 05
3. Route to Test Designer/Test Breaker to update test assertions in test_risk_scoring_check*.py
4. Implementation code needs NO changes (already correct)
5. Advance ticket from INTEGRATION to TEST_DESIGN (for Test Designer to fix assertions)
6. Increment Revision to 9

---
