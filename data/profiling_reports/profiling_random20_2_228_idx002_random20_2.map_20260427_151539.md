# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_228
- **Instance Index**: 2
- **Map**: random20_2.map
- **Agents**: 2
- **Parameters**: k=2, m=1, h=1
- **Failure Types**: tops

## Execution Summary

- **Total Time**: 0.4688s (actual wall-clock execution time)
- **Time from Analysis**: 1.4200s (sum of all profiled sections)

*Note: These times may differ due to profiling overhead and untracked code sections.*

## Component Breakdown

| Component | Time (s) | Calls | Avg Time (ms) | % of Total |
|-----------|----------|-------|---------------|------------|
| ResPlaN | 0.4207 | 1468 | 0.29 | 29.7% |
| CBS | 0.4742 | 259 | 1.83 | 33.5% |
| SIPPS | 0.5222 | 31310 | 0.02 | 36.8% |

## Top 5 Time-Consuming Functions

| Function | Calls | Total Time (s) | Avg Time (ms) |
|----------|-------|----------------|---------------|
| resplan_iteration | 482 | 0.3290 | 0.68 |
| compute_plan_cbs | 43 | 0.2352 | 5.47 |
| root_compute_low_level_solution | 43 | 0.2324 | 5.40 |
| low_level_search_cbs | 86 | 0.2317 | 2.69 |
| SIPPS_loop | 86 | 0.1817 | 2.11 |

## Detailed Granular Statistics

<pre style="overflow-x: auto; white-space: pre;">
ResPlaN | Component: ResPlaN | Total: 0.4688s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 482 | Total: 0.3290s | Avg: 0.68ms | % of Parent: 70.2%
    └─ compute_plan_cbs | Component: CBS | Calls: 43 | Total: 0.2352s | Avg: 5.47ms | % of Parent: 71.5%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0034s | Avg: 3.40ms | % of Parent: 1.4%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 43 | Total: 0.2324s | Avg: 5.40ms | % of Parent: 98.8%
        └─ low_level_search_cbs | Component: CBS | Calls: 86 | Total: 0.2317s | Avg: 2.69ms | % of Parent: 99.7%
          └─ populate_hard_constraints | Component: SIPPS | Calls: 86 | Total: 0.0001s | Avg: 0.00ms | % of Parent: 0.0%
          └─ populate_soft_constraints | Component: SIPPS | Calls: 86 | Total: 0.0002s | Avg: 0.00ms | % of Parent: 0.1%
          └─ area_capacity_soft_constraints | Component: SIPPS | Calls: 86 | Total: 0.0001s | Avg: 0.00ms | % of Parent: 0.0%
          └─ graph_modification | Component: SIPPS | Calls: 86 | Total: 0.0006s | Avg: 0.01ms | % of Parent: 0.3%
          └─ build_safe_interval_table | Component: SIPPS | Calls: 86 | Total: 0.0443s | Avg: 0.52ms | % of Parent: 19.1%
          └─ compute_goal_times | Component: SIPPS | Calls: 86 | Total: 0.0008s | Avg: 0.01ms | % of Parent: 0.3%
          └─ create_root_sipps_node | Component: SIPPS | Total: 0.0000s | % of Parent: 0.0%
          └─ sipps_loop | Component: SIPPS | Calls: 86 | Total: 0.1817s | Avg: 2.11ms | % of Parent: 78.4%
            └─ SIPPS_node_expansion | Component: SIPPS | Calls: 1709 | Total: 0.0033s | Avg: 0.00ms | % of Parent: 1.8%
            └─ hard_constraint_check | Component: SIPPS | Calls: 9652 | Total: 0.0114s | Avg: 0.00ms | % of Parent: 6.3%
            └─ soft_constraint_check | Component: SIPPS | Calls: 9652 | Total: 0.0083s | Avg: 0.00ms | % of Parent: 4.6%
            └─ sipps_node_creation | Component: SIPPS | Calls: 9652 | Total: 0.0390s | Avg: 0.00ms | % of Parent: 21.5%
      └─ cbs_iteration | Component: CBS | Calls: 43 | Total: 0.0022s | Avg: 0.05ms | % of Parent: 0.9%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 43 | Total: 0.0010s | Avg: 0.02ms | % of Parent: 45.5%
        └─ detect_conflict | Component: CBS | Calls: 43 | Total: 0.0007s | Avg: 0.02ms | % of Parent: 31.8%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 482 | Total: 0.0006s | Avg: 0.00ms | % of Parent: 0.2%
    └─ macroaction_loop | Component: ResPlaN | Calls: 43 | Total: 0.0512s | Avg: 1.19ms | % of Parent: 15.6%
    └─ rcheck | Component: ResPlaN | Calls: 460 | Total: 0.0397s | Avg: 0.09ms | % of Parent: 12.1%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.0002s | Avg: 0.20ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-04-27 15:15:39*