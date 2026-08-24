# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 4
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Time**: 440.1962s (actual wall-clock execution time)
- **Time from Analysis**: 1738.1465s (sum of all profiled sections)

*Note: These times may differ due to profiling overhead and untracked code sections.*

## Component Breakdown

| Component | Time (s) | Calls | Avg Time (ms) | % of Total |
|-----------|----------|-------|---------------|------------|
| ResPlaN | 585.8472 | 232227 | 2.52 | 33.7% |
| CBS | 568.6795 | 200572 | 2.84 | 32.7% |
| SIPPS | 583.5991 | 6031796 | 0.10 | 33.6% |

## Top 5 Time-Consuming Functions

| Function | Calls | Total Time (s) | Avg Time (ms) |
|----------|-------|----------------|---------------|
| resplan_iteration | 74950 | 436.7780 | 5.83 |
| compute_plan_cbs | 28653 | 284.4647 | 9.93 |
| root_compute_low_level_solution | 28653 | 280.6889 | 9.80 |
| low_level_search_cbs | 85959 | 279.3802 | 3.25 |
| SIPPS_loop | 85959 | 244.1719 | 2.84 |

## Detailed Granular Statistics

<pre style="overflow-x: auto; white-space: pre;">
ResPlaN | Component: ResPlaN | Total: 440.1962s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 74950 | Total: 436.7780s | Avg: 5.83ms | % of Parent: 99.2%
    └─ compute_plan_cbs | Component: CBS | Calls: 28653 | Total: 284.4647s | Avg: 9.93ms | % of Parent: 65.1%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0154s | Avg: 15.40ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 28653 | Total: 280.6889s | Avg: 9.80ms | % of Parent: 98.7%
        └─ low_level_search_cbs | Component: CBS | Calls: 85959 | Total: 279.3802s | Avg: 3.25ms | % of Parent: 99.5%
          └─ populate_hard_constraints | Component: SIPPS | Calls: 85959 | Total: 0.1883s | Avg: 0.00ms | % of Parent: 0.1%
          └─ populate_soft_constraints | Component: SIPPS | Calls: 85959 | Total: 1.2646s | Avg: 0.01ms | % of Parent: 0.5%
          └─ area_capacity_soft_constraints | Component: SIPPS | Calls: 85959 | Total: 0.3222s | Avg: 0.00ms | % of Parent: 0.1%
          └─ graph_modification | Component: SIPPS | Calls: 85959 | Total: 0.8994s | Avg: 0.01ms | % of Parent: 0.3%
          └─ build_safe_interval_table | Component: SIPPS | Calls: 85959 | Total: 21.7225s | Avg: 0.25ms | % of Parent: 7.8%
          └─ compute_goal_times | Component: SIPPS | Calls: 85959 | Total: 2.4043s | Avg: 0.03ms | % of Parent: 0.9%
          └─ create_root_sipps_node | Component: SIPPS | Total: 0.0000s | % of Parent: 0.0%
          └─ sipps_loop | Component: SIPPS | Calls: 85959 | Total: 244.1719s | Avg: 2.84ms | % of Parent: 87.4%
            └─ SIPPS_node_expansion | Component: SIPPS | Calls: 324758 | Total: 1.4567s | Avg: 0.00ms | % of Parent: 0.6%
            └─ hard_constraint_check | Component: SIPPS | Calls: 1692224 | Total: 4.6938s | Avg: 0.00ms | % of Parent: 1.9%
            └─ soft_constraint_check | Component: SIPPS | Calls: 1692224 | Total: 3.3585s | Avg: 0.00ms | % of Parent: 1.4%
            └─ sipps_node_creation | Component: SIPPS | Calls: 1692224 | Total: 22.4280s | Avg: 0.01ms | % of Parent: 9.2%
      └─ cbs_iteration | Component: CBS | Calls: 28653 | Total: 2.8094s | Avg: 0.10ms | % of Parent: 1.0%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 28653 | Total: 1.1691s | Avg: 0.04ms | % of Parent: 41.6%
        └─ detect_conflict | Component: CBS | Calls: 28653 | Total: 0.8407s | Avg: 0.03ms | % of Parent: 29.9%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 74950 | Total: 0.2683s | Avg: 0.00ms | % of Parent: 0.1%
    └─ macroaction_loop | Component: ResPlaN | Calls: 8597 | Total: 1.6711s | Avg: 0.19ms | % of Parent: 0.4%
    └─ rcheck | Component: ResPlaN | Calls: 73729 | Total: 147.0374s | Avg: 1.99ms | % of Parent: 33.7%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.0924s | Avg: 92.40ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-04-28 10:50:52*