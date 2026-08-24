"""
Headless CLI runner for ResplanMAPF v2 ("optimized" branch, no corridor
reasoning) -- no GUI/tkinter event loop required.

This is run_cli.py's v3 counterpart, adapted to v2's actual constructors:
  - build_graph(grid, num_agents) instead of build_graph(grid, k=k, m=m, h=h)
    (v2's area detection is keyed off raw agent count, not k/m/h -- and is
    unused by the solver either way, so this only affects a vestigial
    attribute, never solving behavior)
  - SearchParams takes 6 positional args here (no failure_history slot)

Everything else -- solve_mapf_with_profiling, solve_mapf_with_granular_profiling,
build_solutions_csv, the timeout-watcher pattern, the single/pkl/config CLI
modes -- is unchanged from run_cli.py, so results.csv rows from this script
and from run_cli.py use the identical schema and can be concatenated directly
for v2-vs-v3 comparison.

Usage: identical to run_cli.py (see that file's docstring for full examples),
e.g.:
    python -m src.run_cli_v2 config --file batch.json --set-name v2_sweep
"""
import argparse
import json
import os
import pickle
import threading
import time
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from src.domain.MAPFInstance import MAPFInstance, RobustnessParams, SearchParams
from src.domain.solver.Solution import Solution
from src.utils.map_handler import load_map, build_graph
from src.utils.plan_io import save_full_solution_pickle
from src.utils.profiling import solve_mapf_with_profiling, solve_mapf_with_granular_profiling
from src.utils.sperimental_analysis import build_solutions_csv

DEFAULT_TIME_LIMIT = 1200
FAILURE_TYPE_CHOICES = ["topw", "tops", "individual", "high-level"]


def _parse_coords(spec):
    """Parse "1,2;3,4" into [(1, 2), (3, 4)]."""
    return [tuple(int(v) for v in pair.split(",")) for pair in spec.split(";")]


def run_one_instance(map_name, starts, goals, k, m, h, failure_types,
                      time_limit=DEFAULT_TIME_LIMIT, granular=False,
                      instance_label="cli_solve", instance_idx=0):
    """Run a single ResplanMAPF (v2) solve headlessly. Returns (solution, stat, timed_out)."""
    print(f"\n*** [{instance_label} #{instance_idx}] Starting solve at {datetime.now()}")
    print(f"    map={map_name} agents={len(starts)} k={k} m={m} h={h} failures={failure_types}")

    grid = load_map(map_name)
    mapf_instance = MAPFInstance(build_graph(grid, len(starts)), starts, goals)
    robustness_params = RobustnessParams(k, m, h, failure_types)
    search_params = SearchParams(
        tuple(frozenset() for _ in starts),
        [0] * len(starts),
        set(), set(), dict(), dict(),
    )

    stop_event = threading.Event()
    start_time = time.perf_counter()

    def _timeout_watcher():
        if not stop_event.wait(timeout=time_limit):
            print(f"[{instance_label} #{instance_idx}] Timeout watcher: time limit reached, aborting.")
            stop_event.set()

    watcher = threading.Thread(target=_timeout_watcher, daemon=True)
    watcher.start()

    sol, stat = None, {}
    try:
        if granular:
            sol, profiling_data = solve_mapf_with_granular_profiling(
                mapf_instance, robustness_params, search_params, verbose=False, stop_event=stop_event,
            )
            elapsed = time.perf_counter() - start_time
            stat = profiling_data.get("granular_stats", {}) if profiling_data else {}
            stat["_counters"] = profiling_data.get("_counters", {}) if profiling_data else {}
        else:
            sol, profiling_data = solve_mapf_with_profiling(
                mapf_instance, robustness_params, search_params, stop_event=stop_event,
            )
            elapsed = time.perf_counter() - start_time
            stat = profiling_data if profiling_data else {}
        stat["elapsed_time"] = elapsed

        timed_out = stop_event.is_set()
        if timed_out:
            print(f"[{instance_label} #{instance_idx}] Timeout reached after {elapsed:.2f}s")
        elif sol and sol.tau_states:
            print(f"[{instance_label} #{instance_idx}] Solved in {elapsed:.2f}s")
            save_full_solution_pickle(
                sol, mapf_instance, robustness_params, map_name,
                filename=f"{instance_label}_inst{instance_idx}",
            )
        else:
            print(f"[{instance_label} #{instance_idx}] No solution found in {elapsed:.2f}s")
    finally:
        stop_event.set()

    if sol is None:
        sol = Solution(None, set(), set(), dict(), dict())

    return sol, stat, timed_out


def run_batch(instances, selected_set):
    """Run a list of (map, starts, goals, k, m, h, failure_types, time_limit, granular)
    tuples, writing one results.csv row per instance as soon as it finishes.

    Progress (solved/timeout/other out of total, elapsed, ETA) is shown as a
    tqdm bar, updated once per completed instance. Deliberately NOT routing
    run_one_instance's own print() calls through tqdm.write(): resplan_mapf
    is itself very verbose (prints every plan step, R_up/R_down sizes, etc.),
    and routing dozens of prints per instance through tqdm.write() forces a
    full bar clear-and-redraw on each one -- tried this, and on real instances
    it floods the log with near-duplicate bar lines instead of giving a clean
    progress readout. Updating the bar only once per instance (here) avoids
    that entirely; the solver's own messages just print normally around it.
    """
    successes, timeouts = 0, 0

    with tqdm(total=len(instances), desc=selected_set, unit="instance") as pbar:
        for idx, inst in enumerate(instances):
            map_name, starts, goals, k, m, h, failure_types, time_limit, granular = inst
            try:
                sol, stat, timed_out = run_one_instance(
                    map_name, starts, goals, k, m, h, failure_types,
                    time_limit=time_limit, granular=granular,
                    instance_label=selected_set, instance_idx=idx,
                )
            except Exception as e:
                print(f"[{selected_set} #{idx}] ERROR: {e}")
                sol, stat, timed_out = Solution(None, set(), set(), dict(), dict()), {}, False

            if timed_out:
                timeouts += 1
            elif sol.tau_states:
                successes += 1

            robustness_params = RobustnessParams(k, m, h, failure_types)
            build_solutions_csv(
                [(map_name, starts, goals)], robustness_params, [sol], selected_set, [stat], [timed_out]
            )

            other = (idx + 1) - successes - timeouts
            pbar.set_postfix(solved=successes, timeout=timeouts, other=other)
            pbar.update(1)

    print(f"\n*** Batch '{selected_set}' completed: {successes}/{len(instances)} solved, {timeouts} timeouts.")


def _load_pkl_instances(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def main():
    parser = argparse.ArgumentParser(description="Headless CLI runner for ResplanMAPF v2 (no GUI).")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_single = sub.add_parser("single", help="Run a single instance from CLI flags.")
    p_single.add_argument("--map", required=True, help="Map filename, e.g. random18.map")
    p_single.add_argument("--starts", required=True, help='Semicolon-separated coords, e.g. "1,2;3,4"')
    p_single.add_argument("--goals", required=True, help='Semicolon-separated coords, e.g. "5,6;7,8"')
    p_single.add_argument("--k", type=int, required=True)
    p_single.add_argument("--m", type=int, required=True)
    p_single.add_argument("--h", type=int, required=True)
    p_single.add_argument("--failtypes", nargs="+", required=True, choices=FAILURE_TYPE_CHOICES)
    p_single.add_argument("--time-limit", type=int, default=DEFAULT_TIME_LIMIT)
    p_single.add_argument("--granular", action="store_true", help="Enable granular profiling.")
    p_single.add_argument("--label", default="cli_solve", help="Name used in logs, solution filenames and the CSV test_case_name.")

    p_pkl = sub.add_parser("pkl", help="Run every instance in a data/test_instances pickle, same params for all.")
    p_pkl.add_argument("--file", required=True, help="Filename inside data/test_instances/")
    p_pkl.add_argument("--k", type=int, required=True)
    p_pkl.add_argument("--m", type=int, required=True)
    p_pkl.add_argument("--h", type=int, required=True)
    p_pkl.add_argument("--failtypes", nargs="+", required=True, choices=FAILURE_TYPE_CHOICES)
    p_pkl.add_argument("--time-limit", type=int, default=DEFAULT_TIME_LIMIT)
    p_pkl.add_argument("--granular", action="store_true", help="Enable granular profiling.")
    p_pkl.add_argument("--set-name", default=None, help="Defaults to the pickle filename without extension.")

    p_config = sub.add_parser("config", help="Run a JSON config listing one or more instances, each with its own parameters.")
    p_config.add_argument("--file", required=True, help="Path to the JSON config file.")
    p_config.add_argument("--set-name", default=None, help="Defaults to the JSON filename without extension.")

    args = parser.parse_args()

    if args.mode == "single":
        starts = _parse_coords(args.starts)
        goals = _parse_coords(args.goals)
        sol, stat, timed_out = run_one_instance(
            args.map, starts, goals, args.k, args.m, args.h, args.failtypes,
            time_limit=args.time_limit, granular=args.granular, instance_label=args.label,
        )
        robustness_params = RobustnessParams(args.k, args.m, args.h, args.failtypes)
        build_solutions_csv(
            [(args.map, starts, goals)], robustness_params, [sol], args.label, [stat], [timed_out]
        )

    elif args.mode == "pkl":
        filepath = os.path.join("data", "test_instances", args.file)
        raw_instances = _load_pkl_instances(filepath)
        set_name = args.set_name or Path(args.file).stem
        instances = [
            (map_name, starts, goals, args.k, args.m, args.h, args.failtypes, args.time_limit, args.granular)
            for (map_name, starts, goals) in raw_instances
        ]
        run_batch(instances, set_name)

    elif args.mode == "config":
        with open(args.file, encoding="utf-8") as f:
            config = json.load(f)
        set_name = args.set_name or Path(args.file).stem
        instances = [
            (
                entry["map"],
                [tuple(s) for s in entry["starts"]],
                [tuple(g) for g in entry["goals"]],
                entry["k"], entry["m"], entry["h"],
                entry["failure_types"],
                entry.get("time_limit", DEFAULT_TIME_LIMIT),
                entry.get("granular_profiling", False),
            )
            for entry in config
        ]
        run_batch(instances, set_name)


if __name__ == "__main__":
    main()
