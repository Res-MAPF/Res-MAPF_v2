# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 3
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Time**: 1641.0733s (actual wall-clock execution time)
- **Time from Analysis**: 7817.1842s (sum of all profiled sections)

*Note: These times may differ due to profiling overhead and untracked code sections.*

## Component Breakdown

| Component | Time (s) | Calls | Avg Time (ms) | % of Total |
|-----------|----------|-------|---------------|------------|
| ResPlaN | 1753.8773 | 175528 | 9.99 | 22.4% |
| CBS | 4255.1711 | 213873 | 19.90 | 54.4% |
| SIPPS | 1808.1045 | 6406244 | 0.28 | 23.1% |

## Top 5 Time-Consuming Functions

| Function | Calls | Total Time (s) | Avg Time (ms) |
|----------|-------|----------------|---------------|
| resplan_iteration | 56762 | 1638.5598 | 28.87 |
| compute_plan_cbs | 22155 | 1510.2394 | 68.17 |
| low_level_search_cbs | 82857 | 1501.7454 | 18.12 |
| CBS_iteration | 37523 | 1232.5417 | 32.85 |
| area_capacity_soft_constraints | 82857 | 931.4614 | 11.24 |

## Detailed Granular Statistics

<pre style="overflow-x: auto; white-space: pre;">
ResPlaN | Component: ResPlaN | Total: 1641.0733s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 56762 | Total: 1638.5598s | Avg: 28.87ms | % of Parent: 99.8%
    └─ compute_plan_cbs | Component: CBS | Calls: 22155 | Total: 1510.2394s | Avg: 68.17ms | % of Parent: 92.2%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0154s | Avg: 15.40ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 20700 | Total: 276.5465s | Avg: 13.36ms | % of Parent: 18.3%
        └─ low_level_search_cbs | Component: CBS | Calls: 82857 | Total: 1501.7454s | Avg: 18.12ms | % of Parent: 543.0%
          └─ populate_hard_constraints | Component: SIPPS | Calls: 82857 | Total: 0.2550s | Avg: 0.00ms | % of Parent: 0.0%
          └─ populate_soft_constraints | Component: SIPPS | Calls: 82857 | Total: 1.5445s | Avg: 0.02ms | % of Parent: 0.1%
          └─ area_capacity_soft_constraints | Component: SIPPS | Calls: 82857 | Total: 931.4614s | Avg: 11.24ms | % of Parent: 62.0%
          └─ graph_modification | Component: SIPPS | Calls: 82857 | Total: 1.0900s | Avg: 0.01ms | % of Parent: 0.1%
          └─ build_safe_interval_table | Component: SIPPS | Calls: 82857 | Total: 275.0570s | Avg: 3.32ms | % of Parent: 18.3%
          └─ compute_goal_times | Component: SIPPS | Calls: 82857 | Total: 2.9321s | Avg: 0.04ms | % of Parent: 0.2%
          └─ create_root_sipps_node | Component: SIPPS | Total: 0.0000s | % of Parent: 0.0%
          └─ sipps_loop | Component: SIPPS | Calls: 82857 | Total: 278.4485s | Avg: 3.36ms | % of Parent: 18.5%
            └─ SIPPS_node_expansion | Component: SIPPS | Calls: 355992 | Total: 1.8990s | Avg: 0.01ms | % of Parent: 0.7%
            └─ hard_constraint_check | Component: SIPPS | Calls: 1833136 | Total: 5.9038s | Avg: 0.00ms | % of Parent: 2.1%
            └─ soft_constraint_check | Component: SIPPS | Calls: 1808210 | Total: 4.1274s | Avg: 0.00ms | % of Parent: 1.5%
            └─ sipps_node_creation | Component: SIPPS | Calls: 1808207 | Total: 28.8393s | Avg: 0.02ms | % of Parent: 10.4%
      └─ cbs_iteration | Component: CBS | Calls: 37523 | Total: 1232.5417s | Avg: 32.85ms | % of Parent: 81.6%
        └─ cbs_vertex_conflict | Component: CBS | Calls: 58 | Total: 7.9307s | Avg: 136.74ms | % of Parent: 0.6%
        └─ build_solution | Component: CBS | Calls: 37523 | Total: 1.6504s | Avg: 0.04ms | % of Parent: 0.1%
        └─ detect_conflict | Component: CBS | Calls: 33756 | Total: 1.0481s | Avg: 0.03ms | % of Parent: 0.1%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 56762 | Total: 0.2396s | Avg: 0.00ms | % of Parent: 0.0%
    └─ macroaction_loop | Component: ResPlaN | Calls: 6979 | Total: 1.4915s | Avg: 0.21ms | % of Parent: 0.1%
    └─ rcheck | Component: ResPlaN | Calls: 55025 | Total: 113.5864s | Avg: 2.06ms | % of Parent: 6.9%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Total: 0.0000s | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-04-28 10:43:32*