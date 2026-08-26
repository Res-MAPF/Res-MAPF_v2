# src/utils

Support modules used across the project: turning a `.map` file into the navigation graph the solver runs on, persisting instances/plans to disk, timing and reporting on solver performance, and writing per-instance results to a CSV for offline experiment analysis. Nothing in this folder implements MAPF solving itself — see [domain/solver/](../domain/solver/README.md) for that.

## Files

| Module | Description |
|--------|-------------|
| `map_handler.py` | Loads a `.map` file and builds the NetworkX navigation graph |
| `plan_io.py` | Save/load MAPF instances and solved plans (pickle/JSON) |
| `granular_profiler.py` | Low-level section timer/call-counter used to instrument the solver |
| `profiling.py` | Wraps `solve_mapf` with profiling and renders markdown reports |
| `bottleneck_analyzer.py` | Buckets profiler output into ResPlaN/CBS/SIPPS and suggests optimization targets |
| `sperimental_analysis.py` | Writes one `results.csv` row per solved instance for offline analysis |

### `map_handler.py`
`load_map(file_path)` reads a map file from `maps/` (the `MAPS_DIR` constant), skipping its header up to the `map` marker line, into a 2D list of characters. `build_graph(grid, num_agents=None)` turns that grid into a `networkx.DiGraph` connecting every walkable (`.`) cell to its 8-connected walkable neighbors, with edge weight 1 for cardinal moves and `1.414` (√2) for diagonals, and disallowing diagonal "corner cutting" through a wall. Note: the `num_agents` parameter (and the "area info" language in its docstring) is vestigial in this v2 version — it's accepted for signature compatibility with other call sites (`build_graph(grid, len(starts))` is called throughout the GUI and both CLI runners) but is not used to compute any per-node area attribute or otherwise affect graph construction or solving here.

### `plan_io.py`
Persistence for both MAPF instances and full solved plans. `save_full_solution_pickle()` / `load_full_solution_pickle()` serialize a `Solution` together with its `MAPFInstance`, `RobustnessParams`, and map name to `data/plans/*.pkl`; `create_solution_name()` builds the filename, encoding the label, map, k/m/h, failure types, agent count, and a timestamp. `save_instance_to_file()` / `load_instance_from_file()` do the analogous save/load for just the instance definition (map, starts, goals, robustness params) as JSON under `data/instances/`, driven by `tkinter.filedialog` save/open dialogs — so this module is GUI-coupled even though the `*_pickle` functions (used by both CLI runners as well as the GUI) don't touch Tk at all.

### `granular_profiler.py`
The actual timing primitive everything else in this folder builds on. `GranularProfiler` tracks, per named section, call count, inclusive time, and (via a call stack) time attributable to nested child sections, plus arbitrary named integer counters (`increment_counter`, used e.g. for CBS conflict counts). It's exposed as a process-wide singleton through `get_profiler()` and the `profile_section(name)` context manager, which is used throughout `computeplan.py` and `resplan_solver.py` to mark the sections that get measured. `get_report_dict()` aggregates entries whose name carries an `_agent_N` suffix (e.g. per-agent SIPPS calls) into one combined stat per base name. Change this file if the way time/calls are measured needs to change; change `profiling.py`/`bottleneck_analyzer.py` for how that data gets reported.

### `profiling.py`
Wraps `solve_mapf()` (from `solver_manager`) with the granular profiler. `solve_mapf_with_profiling()` resets and enables the profiler, runs the solve, and returns `(solution, stats_dict)` with a flattened per-section stats dict plus `elapsed_time` — this is what both CLI runners and the GUI's normal "Solve" button use. `solve_mapf_with_granular_profiling()` does the same but additionally runs `BottleneckAnalyzer` and returns `{'granular_stats', 'analysis', 'elapsed_time'}` — used when the "Granular Profiling" option is selected in the GUI's Run Test dialog or the CLI's `--granular` flag. `generate_profiling_markdown()` renders a full markdown report from that data (execution summary with wall-clock vs. profiled-time accounting, a ResPlaN/CBS/SIPPS component breakdown table, top-10 time-consuming functions, a SIPPS-loop operation breakdown, and a hierarchical call-tree rendering), and `save_profiling_report()` writes it to `data/profiling_reports/`.

### `bottleneck_analyzer.py`
`BottleneckAnalyzer.analyze()` post-processes the granular profiler's stats (via `get_profiler()`), bucketing every measured section into one of three components — `ResPlaN`, `CBS`, `SIPPS` — by matching on the section name, then computes each component's share of total time and a handful of heuristic recommendations (e.g. flagging a component that's over 50% of total time, or "CBS is Nx more expensive than SIPPS, check conflict counts"). `print_analysis()` renders this as a formatted text report. Used by `profiling.solve_mapf_with_granular_profiling()`.

### `sperimental_analysis.py`
(Filename as spelled in the repository.) `build_solutions_csv(instances, robustness_params, solutions, selected_set, timing_stats, timed_out_flags)` is the main experiment-output writer — it appends one row per solved instance to a results CSV (path defaults to `results.csv`, overridable via the `RESULTS_CSV_PATH` environment variable, which is how `run_parallel.py` gets each worker process to write its own file). Each row records success/timeout status, `R_up`/`R_down` set sizes, `k`/`m`/`h`, the resilient plan's cost vs. the 0-resilient CBS baseline cost and the delta % between them, per-failure-type info, and a per-component (ResPlaN/CBS/SIPPS) timing breakdown. `aggregate_granular_stats()` buckets the granular profiler's raw per-section stats into `resplan_mapf` / `compute_plan_cbs` / `low_level_search_cbs` / `build_safe_interval_table` totals for those CSV columns. `compute_map_info()` reports a map's total cell count and the percentage that are walkable. This is the file to change to add, remove, or recompute a `results.csv` column.
