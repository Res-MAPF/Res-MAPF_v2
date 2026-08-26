# src/

This is the root Python package of Res-MAPF v2. It contains everything needed to run the resilient MAPF solver, both through the graphical interface and headlessly from the command line for batch experiments. The three modules directly inside `src/` are entry points; the actual problem model, solving algorithm, GUI, and supporting utilities live in the subpackages below.

## Files

| Module | Description |
|--------|-------------|
| `main.py` | GUI entry point (`python -m src.main`) |
| `run_cli_v2.py` | Headless CLI runner for single/batch solves, no GUI required |
| `run_parallel.py` | Multiprocessing driver that fans a batch config out across CPU workers |

### `main.py`
Launches the graphical application. It sets `customtkinter`'s appearance mode to light and points it at `themes/midnight.json`, then constructs and runs `MainGUIController` (see [view/](view/README.md)). It also monkey-patches `tkinter`'s callback exception handling (both `sys.excepthook` and `Tk.report_callback_exception`) to silently swallow one specific, harmless `AttributeError` ("'str' object has no attribute 'master'") that CustomTkinter's scrollable-frame mouse-wheel handler can raise — every other exception still propagates normally. This is the file to run (`python -m src.main`) to use the app interactively.

### `run_cli_v2.py`
Headless counterpart to the GUI's "Solve" and "Run Test" actions, for scripted/batch use without a Tk event loop. It is v2's fork of the `run_cli.py` pattern (per its own docstring): it calls `build_graph(grid, num_agents)` and builds `SearchParams` with 6 positional args (no failure-history slot), matching v2's actual constructors, while keeping the same `results.csv` schema as other versions' CLI runners so rows can be concatenated across versions. `run_one_instance()` is the core routine — it loads a map, builds a `MAPFInstance`/`RobustnessParams`/`SearchParams`, runs the solver under a timeout watcher thread, and saves a full-solution pickle on success; it's also imported directly by `run_parallel.py`. `main()` exposes three subcommands: `single` (one instance from CLI flags), `pkl` (every instance in a `data/test_instances/*.pkl` file, same k/m/h/failure types for all), and `config` (a JSON list where each entry carries its own parameters). `run_batch()` drives the `pkl`/`config` modes with a `tqdm` progress bar and writes one `results.csv` row per instance as it finishes.

### `run_parallel.py`
Parallel batch driver for a `run_cli`-style JSON config. It fans instances out across a `multiprocessing.Pool` using `Pool.imap_unordered` (a dynamic work queue, chosen because per-instance runtime is too skewed for a static split to load-balance well). Each worker process gets its own `RESULTS_CSV_PATH` (`results_worker_<pid>.csv` under `--out-dir`) since `build_solutions_csv` has no file locking for concurrent writers; a separate merge step (not present in this v2 checkout) is expected to concatenate them afterward. `_run_one()` imports `run_one_instance` from `src.run_cli`, falling back to this package's own `run_cli_v2.run_one_instance` when `run_cli.py` doesn't exist (as in this v2 tree) — so the fallback import is what actually makes this script work here. Invoke with `python -m src.run_parallel --file <config.json> --set-name <name> --out-dir <dir> [--workers N]`.

## Subfolders

| Package | Description |
|---------|-------------|
| `domain/` | The MAPF problem model (instance/robustness/search parameter classes) and random instance generation — see [domain/README.md](domain/README.md) |
| `utils/` | Map loading, plan/instance persistence, profiling infrastructure, and experiment CSV output — see [utils/README.md](utils/README.md) |
| `view/` | The customtkinter GUI: layout, event handlers, state, and the plan/failure-simulation visualizer — see [view/README.md](view/README.md) |
