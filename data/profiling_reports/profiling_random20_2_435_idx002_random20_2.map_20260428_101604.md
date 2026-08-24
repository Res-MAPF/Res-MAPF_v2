# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 2
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Time**: 346.4211s (actual wall-clock execution time)
- **Time from Analysis**: 1449.5689s (sum of all profiled sections)

*Note: These times may differ due to profiling overhead and untracked code sections.*

## Component Breakdown

| Component | Time (s) | Calls | Avg Time (ms) | % of Total |
|-----------|----------|-------|---------------|------------|
| ResPlaN | 434.0155 | 163757 | 2.65 | 29.9% |
| CBS | 501.1248 | 151908 | 3.30 | 34.6% |
| SIPPS | 514.4281 | 4573812 | 0.11 | 35.5% |

## Top 5 Time-Consuming Functions

| Function | Calls | Total Time (s) | Avg Time (ms) |
|----------|-------|----------------|---------------|
| resplan_iteration | 53034 | 343.6825 | 6.48 |
| compute_plan_cbs | 21701 | 250.6700 | 11.55 |
| root_compute_low_level_solution | 21701 | 247.2653 | 11.39 |
| low_level_search_cbs | 65103 | 246.0844 | 3.78 |
| SIPPS_loop | 65103 | 214.6656 | 3.30 |

## Detailed Granular Statistics

<pre style="overflow-x: auto; white-space: pre;">
ResPlaN | Component: ResPlaN | Total: 346.4211s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 53034 | Total: 343.6825s | Avg: 6.48ms | % of Parent: 99.2%
    └─ compute_plan_cbs | Component: CBS | Calls: 21701 | Total: 250.6700s | Avg: 11.55ms | % of Parent: 72.9%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0130s | Avg: 13.00ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 21701 | Total: 247.2653s | Avg: 11.39ms | % of Parent: 98.6%
        └─ low_level_search_cbs | Component: CBS | Calls: 65103 | Total: 246.0844s | Avg: 3.78ms | % of Parent: 99.5%
          └─ populate_hard_constraints | Component: SIPPS | Calls: 65103 | Total: 0.1634s | Avg: 0.00ms | % of Parent: 0.1%
          └─ populate_soft_constraints | Component: SIPPS | Calls: 65103 | Total: 1.1553s | Avg: 0.02ms | % of Parent: 0.5%
          └─ area_capacity_soft_constraints | Component: SIPPS | Calls: 65103 | Total: 0.2841s | Avg: 0.00ms | % of Parent: 0.1%
          └─ graph_modification | Component: SIPPS | Calls: 65103 | Total: 0.8001s | Avg: 0.01ms | % of Parent: 0.3%
          └─ build_safe_interval_table | Component: SIPPS | Calls: 65103 | Total: 19.2835s | Avg: 0.30ms | % of Parent: 7.8%
          └─ compute_goal_times | Component: SIPPS | Calls: 65103 | Total: 2.0891s | Avg: 0.03ms | % of Parent: 0.8%
          └─ create_root_sipps_node | Component: SIPPS | Total: 0.0000s | % of Parent: 0.0%
          └─ sipps_loop | Component: SIPPS | Calls: 65103 | Total: 214.6656s | Avg: 3.30ms | % of Parent: 87.2%
            └─ SIPPS_node_expansion | Component: SIPPS | Calls: 250897 | Total: 1.3342s | Avg: 0.01ms | % of Parent: 0.6%
            └─ hard_constraint_check | Component: SIPPS | Calls: 1281831 | Total: 4.1946s | Avg: 0.00ms | % of Parent: 2.0%
            └─ soft_constraint_check | Component: SIPPS | Calls: 1281831 | Total: 2.9806s | Avg: 0.00ms | % of Parent: 1.4%
            └─ sipps_node_creation | Component: SIPPS | Calls: 1281831 | Total: 20.2123s | Avg: 0.02ms | % of Parent: 9.4%
      └─ cbs_iteration | Component: CBS | Calls: 21701 | Total: 2.5355s | Avg: 0.12ms | % of Parent: 1.0%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 21701 | Total: 1.0637s | Avg: 0.05ms | % of Parent: 42.0%
        └─ detect_conflict | Component: CBS | Calls: 21701 | Total: 0.7582s | Avg: 0.03ms | % of Parent: 29.9%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 53034 | Total: 0.2179s | Avg: 0.00ms | % of Parent: 0.1%
    └─ macroaction_loop | Component: ResPlaN | Calls: 5789 | Total: 1.3538s | Avg: 0.23ms | % of Parent: 0.4%
    └─ rcheck | Component: ResPlaN | Calls: 51899 | Total: 88.6581s | Avg: 1.71ms | % of Parent: 25.8%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.1032s | Avg: 103.20ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-04-28 10:16:04*