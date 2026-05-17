# loop_x Plan (fixture, contains a duplicate slice id on purpose)

### X.1 first

```yaml
id: X.1
phase: F1
loop: loop_x
status: pending
deps: []
acceptance: |-
  first
priority: P2
```

### X.1 duplicate id (parser must reject)

```yaml
id: X.1
phase: F1
loop: loop_x
status: pending
deps: []
acceptance: |-
  duplicate
priority: P2
```
