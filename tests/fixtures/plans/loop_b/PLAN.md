# loop_b Plan (fixture)

## G phase one

### B.1 pickable P1 in loop b

```yaml
id: B.1
phase: G
loop: loop_b
status: pending
deps: []
acceptance: |-
  highest priority pickable slice across the two fixture loops
priority: P1
tags: [fixture]
```

### B.2 in_progress slice

```yaml
id: B.2
phase: G
loop: loop_b
status: in_progress
deps: []
acceptance: |-
  in_progress is not pickable
priority: P0
tags: [fixture]
```
