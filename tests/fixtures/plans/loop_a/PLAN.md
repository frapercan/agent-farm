# loop_a Plan (fixture)

## F1 first phase

### A.1 first slice in loop a

```yaml
id: A.1
phase: F1
loop: loop_a
status: done
deps: []
acceptance: |-
  done already
priority: P0
tags: [fixture]
```

History note.

### A.2 pickable slice in loop a P2

```yaml
id: A.2
phase: F1
loop: loop_a
status: pending
deps: [A.1]
acceptance: |-
  pick me once A.1 is done
priority: P2
tags: [fixture]
```

## F2 second phase

### A.3 blocked on missing dep

```yaml
id: A.3
phase: F2
loop: loop_a
status: pending
deps: [A.1, MISSING.1]
acceptance: |-
  cannot pick because MISSING.1 does not exist
priority: P1
tags: [fixture]
```

### A.4 needs human

```yaml
id: A.4
phase: F2
loop: loop_a
status: pending
deps: []
acceptance: |-
  requires_human true keeps the picker away
priority: P0
tags: [fixture]
requires_human: true
```
