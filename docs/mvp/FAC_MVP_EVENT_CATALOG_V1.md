# FAC MVP Event Catalog V1

## 1. 通用 Event Envelope
```text
event_id
event_type
version
object_ref
source_system
occurred_at
actor_id
correlation_id
causation_id
trace_id
payload_version
payload
evidence_refs
idempotency_key
```

## 2. 核心事件

### EV-01 OrderFinanceCalculationRequested
Publisher：User/System/FAC Scheduler  
Consumer：FAC-OFA  
Idempotency：order_id + input_revision_set + rule_set_version。

### EV-02 MaterialPriceMissing
Publisher：FAC-OFA  
Consumer：EDP/FAC Exception/CFO Agent/EBMS Exception  
结果：CALCULATION_INCOMPLETE。

### EV-03 FXRateMissing
Publisher：FAC-OFA/AR  
Consumer：EDP/Finance Owner/EBMS Exception  
禁止 fallback rate=1。

### EV-04 PlanCostCalculated
Publisher：FAC-OFA  
Consumer：Margin Engine/EDP/CFO Agent。

### EV-05 EstimatedActualCostUpdated
Publisher：FAC Cost  
Consumer：Margin Engine/EDP。允许多次发生，每次新 version。

### EV-06 FinalActualCostVerified
Publisher：FAC Cost  
Consumer：Margin Engine/EDP/EBMS。

### EV-07 MarginCalculated
Publisher：FAC Margin  
Consumer：EDP/CFO Agent/Risk/EBMS  
Idempotency：order_id + margin_type + calculation_id + rule_version。

### EV-08 MarginBelowThreshold
Publisher：FAC Margin  
Consumer：CFO Agent/Finance Owner/EBMS Exception。

### EV-09 ReceivableCreated
Publisher：FAC AR  
Consumer：EDP/AR Agent。

### EV-10 ReceivableDue
Publisher：FAC AR Scheduler  
Consumer：AR Agent。

### EV-11 ReceivableOverdue
Publisher：FAC AR  
Consumer：AR Agent/CFO Agent/EBMS Exception。

### EV-12 ARRiskRaised
Publisher：FAC AR Risk  
Consumer：AR Agent/CFO Agent/M01 DecisionCase capability。

### EV-13 CollectionDecisionCaseRequested
Publisher：AR Agent A1  
Consumer：M01/DEH。

### EV-14 CollectionActionCreated
Publisher：M01  
Consumer：FAC AR/POMS/EDP。

### EV-15 PaymentReceived
Publisher：EDP  
Consumer：FAC AR。

### EV-16 BankMatchProposed
Publisher：FAC Skill  
Consumer：Finance Owner。

### EV-17 BankMatchConfirmed
Publisher：Finance Owner  
Consumer：FAC AR。必须 Audit。

### EV-18 CollectionResultSubmitted
Publisher：Action Owner/System  
Consumer：Finance Verifier。

### EV-19 CollectionResultVerified
Publisher：Verifier  
Consumer：EDP/EBMS/CFO Agent。

### EV-20 RecalculationRequired
Publisher：FAC/EDP  
Trigger：BOM、Price、FX、Labor、Revenue、Cost 等关键变更。  
Consumer：FAC Calculation Orchestrator。

### EV-21 ResultSuperseded
Publisher：FAC  
Consumer：EDP/EBMS。旧 Result 仍可查询。

## 3. Retry 与 Replay

读型消费者可自动 retry。

财经写入型消费者必须满足：
```text
idempotent
auditable
no duplicate Result
```

EDP Event Replay 时 FAC 必须保证不产生重复 Revenue、AR、Result、Collection。

## 4. G2 Event Gate

必须测试 Schema、Required fields、Idempotency、Replay、correlation、causation、permission、evidence_refs。
