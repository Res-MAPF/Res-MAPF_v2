# src/domain

The domain layer models a resilient MAPF problem: the plain data structures that describe an instance, the robustness budget it must be solved under, and the mutable state carried through the search, plus the logic for generating random test instances. It does not contain any solving algorithm itself — that lives in [solver/](solver/README.md), which consumes the classes defined here.

## Files

| Module | Description |
|--------|-------------|
| `MAPFInstance.py` | `MAPFInstance`, `RobustnessParams`, `SearchParams` — the core value objects passed between the GUI/CLI and the solver |
| `generation.py` | Random test-instance generation, saved as pickles for later batch solving |

### `MAPFInstance.py`
Three small, otherwise-logic-free container classes shared by every entry point (GUI handlers, both CLI runners, the solver):

- `MAPFInstance(graph, starts, goals)` — the navigation graph (a NetworkX graph built by [`map_handler.build_graph`](../utils/README.md)) plus each agent's start and goal cell.
- `RobustnessParams(k, m, h, selected_failure_types)` — the resilience budget: `k` is the total number of failures the plan must tolerate, `m` the maximum number of distinct agents any combination of tolerated failures may affect, `h` the maximum number of failures a single agent may individually suffer, and `selected_failure_types` the subset of failure semantics to consider (`topw`, `tops`, `individual`, `high-level` — see [`resplan_solver.compute_affected_actions`](solver/README.md)).
- `SearchParams(initial_failed_actions, initial_failures, r_up, r_down, predecessors, resilient_node_macroactions)` — the solver's carried-over search state: which actions are already known-failed per agent, each agent's failure count so far, the accumulated resilient/non-resilient state sets (`r_up`/`r_down`), the predecessor map used to reconstruct a plan, and the cache of macro-actions already proven resilient at a node. A fresh solve starts these empty/zeroed; the GUI's interactive failure-simulation flow (in [`grid_visualizer.py`](../view/README.md)) instead re-solves by passing in the *previous* solution's `R_up`/`R_down`/`predecessors` here, so the search can resume rather than restart from scratch.

### `generation.py`
`generate_test_instances(n_instances, n_agents, min_dst, name, map_name)` builds `n_instances` random start/goal assignments for `n_agents` agents on `map_name`, each pair separated by a shortest-path distance in `[min_dst, min_dst + 5]`, and pickles the resulting `(map_name, starts, goals)` list to `data/test_instances/<name>.pkl`. `extract_start_goal_with_min_distance()` implements the sampling: it first tries up to 100 random start/goal draws checked against the distance window, then falls back to a single-source BFS/Dijkstra from a random start to find any goal at or beyond `min_dst` if random sampling doesn't hit the window. This is what backs the GUI's "Generate test instances" panel (via `handlers.handle_generate_instances`) and is also usable standalone to produce a batch fixture for the CLI runners' `pkl` mode.

## Subfolders

| Package | Description |
|---------|-------------|
| `solver/` | The ResPlaN resilient-planning algorithm (CBS/SIPPS nominal planner plus the resilience search built on top of it) — see [solver/README.md](solver/README.md) |
