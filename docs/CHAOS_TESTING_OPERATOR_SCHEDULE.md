# P-OS Chaos Testing Operator Rotation Schedule

**Purpose:** Define operator rotation for 4-week chaos testing program  
**Status:** ACTIVE — Locked Calendar  
**Created:** 2026-05-07  
**Duration:** 4 weeks (May 13 - June 9, 2026)  
**Classification:** SOVEREIGN GRADE — OPERATIONAL PROTOCOL

---

## META

**Schedule Version:** 1.0  
**Approved By:** Budowniczy P-OS + Nadzorca  
**Next Review:** 2026-06-09 (post-chaos retrospective)  

---

## PURPOSE

Ensure **fresh cognitive load per operator** during chaos testing to prevent fatigue-induced errors and maximize learning diversity.

**Objectives:**
1. Distribute chaos testing workload across 4 operators
2. Prevent single-operator burnout during intensive failure injection
3. Capture diverse perspectives on system resilience
4. Build organizational knowledge (not individual expertise)
5. Validate procedures work for different operator skill levels

---

## OPERATOR ROSTER

| Operator | Role | Experience Level | Contact | Availability |
|----------|------|-----------------|---------|-------------|
| **Operator SS** | Primary (Week 1) | Senior (3+ years P-OS) | ss@milejczyce.gov.pl | Mon-Fri 08:00-17:00 UTC |
| **Operator TK** | Secondary (Week 2) | Mid-level (1-2 years) | tk@milejczyce.gov.pl | Mon-Fri 09:00-18:00 UTC |
| **Operator LM** | Tertiary (Week 3) | Junior (<1 year) | lm@milejczyce.gov.pl | Mon-Fri 08:30-17:30 UTC |
| **Operator PA** | Quaternary (Week 4) | Senior (3+ years) | pa@milejczyce.gov.pl | Mon-Fri 07:00-16:00 UTC |

### Backup Operators (On-Call)
- **Backup 1:** ops-backup1@milejczyce.gov.pl (covers SS/TK absences)
- **Backup 2:** ops-backup2@milejczyce.gov.pl (covers LM/PA absences)

---

## WEEKLY ASSIGNMENTS

### Week 1: Infrastructure Chaos (May 13-19, 2026)
**Primary Operator:** Operator SS  
**Tests:** Test 1 (Deployment Failure), Test 5 (Race Condition), Test 6 (Integrity Violation)  
**Focus:** System-level failures, automated recovery mechanisms  

**Daily Schedule:**
- 09:00-09:15: Daily standup (previous day review)
- 09:15-12:00: Execute assigned test(s)
- 12:00-13:00: Lunch break
- 13:00-15:00: Document observations, capture metrics
- 15:00-16:00: Update procedures if gaps found
- 16:00-17:00: Prep for next day's test

**Support Team:**
- Budowniczy: Available for architectural questions
- Nadzorca: Observes for governance compliance
- Engineering Agent: On-call for technical troubleshooting

---

### Week 2: Operational Chaos (May 20-26, 2026)
**Primary Operator:** Operator TK  
**Tests:** Test 2 (Webhook Silence), Test 3 (Operator Absent), Test 8 (Exhausted Operator)  
**Focus:** Human-centric failures, alert routing, manual recovery  

**Daily Schedule:** Same as Week 1

**Special Considerations:**
- Operator TK is mid-level → Extra supervision from Budowniczy
- Test 8 requires simulating fatigue → Ethical guidelines apply (no actual sleep deprivation)
- Focus on procedure clarity for less experienced operators

---

### Week 3: Security Chaos (May 27 - June 2, 2026)
**Primary Operator:** Operator LM  
**Tests:** Test 4 (BREAK_GLASS Abuse), Penetration Test, Social Engineering Test  
**Focus:** Authorization bypasses, security gate effectiveness  

**Daily Schedule:** Same as Week 1

**Special Considerations:**
- Operator LM is junior → Closest supervision required
- Security tests require DPO presence (remote observation)
- All penetration attempts logged for audit trail
- Social engineering test requires informed consent from target operator

---

### Week 4: Recovery Chaos (June 3-9, 2026)
**Primary Operator:** Operator PA  
**Tests:** Test 7 (Rollback Correctness), Full DR Drill, Backup Restoration Test  
**Focus:** System restoration, data integrity verification  

**Daily Schedule:** Same as Week 1

**Special Considerations:**
- Full DR drill requires all 4 operators present (simulation of team response)
- Backup restoration test may take 4-6 hours (schedule accordingly)
- Final week → Comprehensive retrospective preparation

---

## DAILY STANDUP PROTOCOL

**Time:** 09:00-09:15 UTC (15 minutes, strict timebox)  
**Attendees:** Current week operator + Budowniczy + Nadzorca + ops contact  
**Format:** Video call (Teams/Zoom) with screen sharing  

### Agenda (Strict 15-Minute Timebox)

1. **Previous Day Results (5 min)**
   - What test was executed?
   - Did it pass/fail?
   - MTTR measured?
   - Any unexpected behavior?

2. **Today's Test Preview (5 min)**
   - Which test will be executed?
   - Prerequisites verified?
   - Expected outcome?
   - Known risks?

3. **Blockers & Support Needs (5 min)**
   - Any tools missing?
   - Any clarifications needed?
   - Escalations required?

### Standup Rules
- ✅ **Start on time** — 09:00 sharp, no waiting
- ✅ **Camera on** — Visual engagement required
- ✅ **Screen share** — Show logs/metrics from previous day
- ❌ **No problem-solving** — If issue needs >2 min discussion, schedule separate call
- ❌ **No blame** — Focus on system behavior, not operator performance

---

## WEEKLY RETROSPECTIVE PROTOCOL

**Time:** Friday 14:00-15:00 UTC (60 minutes)  
**Attendees:** All 4 operators + Engineering Agent + DPO (remote) + Budowniczy + Nadzorca  
**Format:** Video call with collaborative whiteboard (Miro/Mural)  

### Agenda (60 Minutes)

1. **Week Review (20 min)**
   - Tests executed this week
   - MTTR trends (improving/degrading?)
   - SPOFs identified
   - False positive/negative rates

2. **Procedure Updates (15 min)**
   - Which checklists need revision?
   - Which error messages were unclear?
   - Which steps caused confusion?

3. **Operator Feedback (15 min)**
   - Stress levels (before/after each test)
   - Confidence ratings (1-10 scale)
   - Suggestions for improvement

4. **Next Week Prep (10 min)**
   - Assignments confirmed
   - Tools validated
   - Risks identified

### Retrospective Outputs
- Updated chaos testing procedures (if changes needed)
- Operator feedback summary (anonymous if requested)
- Action items for following week
- MTTR trend chart (visual)

---

## ESCALATION MATRIX

### Level 1: Operator Self-Resolution (0-15 min)
**Trigger:** Minor confusion, unclear instruction  
**Action:** Operator consults runbook, tries alternative approach  
**Escalate If:** No progress after 15 minutes

### Level 2: Engineering Agent Support (15-60 min)
**Trigger:** Technical issue, tool malfunction, unexpected behavior  
**Action:** Contact ops@milejczyce.gov.pl with correlation ID  
**Response Time:** <30 minutes  
**Escalate If:** Issue unresolved after 60 minutes

### Level 3: Budowniczy Intervention (1-4 hours)
**Trigger:** Architectural ambiguity, constitutional interpretation needed  
**Action:** Email budowniczy@milejczyce.gov.pl with detailed context  
**Response Time:** <2 hours  
**Escalate If:** Critical vulnerability discovered

### Level 4: Nadzorca Emergency Override (Immediate)
**Trigger:** Security breach, data loss risk, system compromise  
**Action:** Call security@milejczyce.gov.pl (phone, not email)  
**Response Time:** Immediate (<15 minutes)  
**Action:** Halt all chaos testing, initiate incident response

---

## ABSENCE COVERAGE PROTOCOL

### Planned Absence (>24 hours notice)
1. Operator notifies Budowniczy via email
2. Backup operator assigned from roster
3. Handover call scheduled (30 min)
4. Access credentials transferred securely
5. Documentation updated with new operator name

### Unplanned Absence (<24 hours notice)
1. Operator sends emergency notification (SMS/call)
2. Backup operator activated immediately
3. Budowniczy briefed within 1 hour
4. Previous day's logs reviewed by backup
5. Test schedule adjusted if needed

### Extended Absence (>3 days)
1. Week reassigned to different operator
2. Remaining tests rescheduled
3. Chaos testing timeline extended
4. Post-absence debrief conducted

---

## COGNITIVE LOAD MANAGEMENT

### Fatigue Prevention Rules
- ✅ **Max 2 chaos tests per day** — Prevents decision fatigue
- ✅ **Mandatory lunch break** — 60 minutes, no work discussions
- ✅ **No testing after 17:00 UTC** — Protects work-life balance
- ✅ **Weekly rest day** — Saturday/Sunday off, no exceptions
- ❌ **No consecutive high-stress tests** — Alternate easy/hard tests

### Stress Monitoring
- **Pre-test rating:** Operator rates stress level (1-10)
- **Post-test rating:** Operator rates stress level (1-10)
- **Threshold:** If post-test rating >8, next test delayed 24 hours
- **Trend analysis:** Weekly review of stress trends across operators

### Support Resources
- **Peer support:** Operators can pair-test if feeling uncertain
- **Technical mentor:** Engineering Agent available for guidance
- **Psychological safety:** No blame culture, mistakes are learning opportunities
- **Escalation path:** Operator can request test postponement without penalty

---

## SUCCESS METRICS FOR ROTATION

### Individual Operator Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Tests Completed | 100% assigned | Count completed / count assigned |
| MTTR Achievement | <5 min average | Timer from failure to recovery |
| Documentation Quality | ≥8/10 rating | Peer review of observation notes |
| Stress Management | ≤7/10 post-test | Self-reported stress rating |
| Learning Progression | Improvement week-over-week | Confidence rating trend |

### Team-Level Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Coverage | 4/4 operators participate | Attendance records |
| Knowledge Sharing | ≥3 procedure updates | Count of checklist revisions |
| Cross-Training | Each operator observes ≥1 other week's test | Observation logs |
| Retrospective Participation | 100% attendance | Meeting attendance records |

---

## COMMUNICATION CHANNELS

### Primary Channels
- **Daily Standup:** Teams video call (link sent calendar invite)
- **Weekly Retrospective:** Teams video call + Miro whiteboard
- **Async Updates:** Slack channel `#chaos-testing-week1` (rotate weekly)
- **Emergency:** Phone call to security@milejczyce.gov.pl

### Documentation Repositories
- **Test Logs:** `logs/chaos_tests/test_<number>_YYYY-MM-DD.log`
- **Screenshots:** `screenshots/chaos_tests/test_<number>/`
- **Metrics:** `metrics/chaos_tests/results.csv`
- **Feedback Forms:** `docs/chaos_tests/feedback_test_<number>.md`

---

## APPROVAL SIGNATURES

**Budowniczy P-OS:**  
Name: ________________________  
Signature: ________________________  
Date: ________________________  

**Nadzorca:**  
Name: ________________________  
Signature: ________________________  
Date: ________________________  

**Lead Operator (SS):**  
Name: ________________________  
Signature: ________________________  
Date: ________________________  

---

## VERSION HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-07 | p-os-engineering | Initial rotation schedule created |

---

**🛡️ OPERATOR ROTATION SCHEDULE LOCKED — READY FOR EXECUTION 🛡️**

**Remember:** Fresh minds catch more bugs. Rotate early, rotate often.
