# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_228
- **Instance Index**: 1
- **Map**: random20_2.map
- **Agents**: 2
- **Parameters**: k=2, m=1, h=1
- **Failure Types**: tops

## Execution Summary

- **Total Time**: 0.4383s (actual wall-clock execution time)
- **Time from Analysis**: 0.9895s (sum of all profiled sections)

*Note: These times may differ due to profiling overhead and untracked code sections.*

## Component Breakdown

| Component | Time (s) | Calls | Avg Time (ms) | % of Total |
|-----------|----------|-------|---------------|------------|
| ResPlaN | 0.3598 | 1480 | 0.24 | 36.3% |
| CBS | 0.3347 | 277 | 1.21 | 33.8% |
| SIPPS | 0.2959 | 18339 | 0.02 | 29.9% |

## Top 5 Time-Consuming Functions

| Function | Calls | Total Time (s) | Avg Time (ms) |
|----------|-------|----------------|---------------|
| resplan_iteration | 487 | 0.2556 | 0.52 |
| compute_plan_cbs | 45 | 0.1461 | 3.25 |
| low_level_search_cbs | 92 | 0.1421 | 1.54 |
| root_compute_low_level_solution | 45 | 0.1237 | 2.75 |
| SIPPS_loop | 92 | 0.1004 | 1.09 |

## Detailed Granular Statistics

<pre style="overflow-x: auto; white-space: pre;">
ResPlaN | Component: ResPlaN | Total: 0.4383s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 487 | Total: 0.2556s | Avg: 0.52ms | % of Parent: 58.3%
    └─ compute_plan_cbs | Component: CBS | Calls: 45 | Total: 0.1461s | Avg: 3.25ms | % of Parent: 57.2%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0032s | Avg: 3.20ms | % of Parent: 2.2%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 45 | Total: 0.1237s | Avg: 2.75ms | % of Parent: 84.7%
        └─ low_level_search_cbs | Component: CBS | Calls: 92 | Total: 0.1421s | Avg: 1.54ms | % of Parent: 114.9%
          └─ populate_hard_constraints | Component: SIPPS | Calls: 92 | Total: 0.0001s | Avg: 0.00ms | % of Parent: 0.1%
          └─ populate_soft_constraints | Component: SIPPS | Calls: 92 | Total: 0.0002s | Avg: 0.00ms | % of Parent: 0.1%
          └─ area_capacity_soft_constraints | Component: SIPPS | Calls: 92 | Total: 0.0012s | Avg: 0.01ms | % of Parent: 0.8%
          └─ graph_modification | Component: SIPPS | Calls: 92 | Total: 0.0007s | Avg: 0.01ms | % of Parent: 0.5%
          └─ build_safe_interval_table | Component: SIPPS | Calls: 92 | Total: 0.0351s | Avg: 0.38ms | % of Parent: 24.7%
          └─ compute_goal_times | Component: SIPPS | Calls: 92 | Total: 0.0007s | Avg: 0.01ms | % of Parent: 0.5%
          └─ create_root_sipps_node | Component: SIPPS | Total: 0.0000s | % of Parent: 0.0%
          └─ sipps_loop | Component: SIPPS | Calls: 92 | Total: 0.1004s | Avg: 1.09ms | % of Parent: 70.7%
            └─ SIPPS_node_expansion | Component: SIPPS | Calls: 943 | Total: 0.0018s | Avg: 0.00ms | % of Parent: 1.8%
            └─ hard_constraint_check | Component: SIPPS | Calls: 5569 | Total: 0.0059s | Avg: 0.00ms | % of Parent: 5.9%
            └─ soft_constraint_check | Component: SIPPS | Calls: 5569 | Total: 0.0046s | Avg: 0.00ms | % of Parent: 4.6%
            └─ sipps_node_creation | Component: SIPPS | Calls: 5569 | Total: 0.0215s | Avg: 0.00ms | % of Parent: 21.4%
      └─ cbs_iteration | Component: CBS | Calls: 46 | Total: 0.0218s | Avg: 0.47ms | % of Parent: 14.9%
        └─ cbs_vertex_conflict | Component: CBS | Calls: 1 | Total: 0.0198s | Avg: 19.80ms | % of Parent: 90.8%
        └─ build_solution | Component: CBS | Calls: 46 | Total: 0.0010s | Avg: 0.02ms | % of Parent: 4.6%
        └─ detect_conflict | Component: CBS | Calls: 46 | Total: 0.0007s | Avg: 0.02ms | % of Parent: 3.2%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 487 | Total: 0.0006s | Avg: 0.00ms | % of Parent: 0.2%
    └─ macroaction_loop | Component: ResPlaN | Calls: 45 | Total: 0.0547s | Avg: 1.22ms | % of Parent: 21.4%
    └─ rcheck | Component: ResPlaN | Calls: 460 | Total: 0.0487s | Avg: 0.11ms | % of Parent: 19.1%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.0002s | Avg: 0.20ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-04-27 15:15:38*