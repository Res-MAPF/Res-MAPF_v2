import os
import sys
import threading
import time
from tkinter import ttk as tctk
import customtkinter as ctk
from pathlib import Path

import tkinter.messagebox as messagebox
from tkinter import filedialog
import pickle

from src.domain.generation import TEST_INSTANCES_DIR
from src.utils.plan_io import (
    save_instance_to_file,
    load_instance_from_file,
    save_full_solution_pickle,
    load_full_solution_pickle,
)
from src.domain.MAPFInstance import MAPFInstance, RobustnessParams, SearchParams
from src.view.grid_visualizer import GridVisualizer
from src.utils.map_handler import load_map, build_graph
from src.utils.profiling import solve_mapf_with_profiling, solve_mapf_with_granular_profiling


TIME_LIMIT = 3600
SAVE_INSTANCE_INITIAL_DIR = str(Path("data/instances"))
LOAD_PLAN_INITIAL_DIR = str(Path("data/plans"))
DATA_DIR = str(Path("data"))
TITLE_SIMULATE = "MAPF Visualization"
SIZE_SIMULATE = "1300x700"
TITLE_RUN_TEST = "Starting Test"
SIZE_RUN_TEST = "400x500"

def configure_handlers(root, state, console_textbox):
    def update_agent_display():
        state.agent_listbox.delete(0, "end")
        for i, (start, goal) in enumerate(state.agent_list):
            state.agent_listbox.insert("end", f"Agent {i+1}: Start {start} -> Goal {goal}")

    def add_agent():
        coords = [e.get() for e in state.coord_entries]
        if all(val.isdigit() for val in coords):
            s = (int(coords[0]), int(coords[1]))
            g = (int(coords[2]), int(coords[3]))
            state.agent_list.append((s, g))
            update_agent_display()
            for e in state.coord_entries:
                e.delete(0, "end")
        else:
            messagebox.showerror("Error", "Coordinates must be integers.")

    def remove_agent():
        try:
            index = state.agent_listbox.curselection()[0]
            state.agent_list.pop(index)
            update_agent_display()
        except IndexError:
            messagebox.showerror("Error", "Select an agent to remove.")

    def handle_save_instance():
        if not state.map_var.get():
            messagebox.showerror("Error", "Select a map before saving.")
            return
        try:
            k = int(state.k_var.get())
            h = int(state.h_var.get())
            m = int(state.m_var.get())
        except ValueError:
            messagebox.showerror("Error", "k, h, and m must be integers.")
            return

        selected_failtypes = [ftype for ftype, var in state.fail_type_vars.items() if var.get()]
        try:
            starts = [s for s, _ in state.agent_list]
            goals = [g for _, g in state.agent_list]
            robustness_params = RobustnessParams(k, m, h, selected_failtypes)
            success = save_instance_to_file(
                state.map_var.get(), starts, goals, robustness_params, parent_window=root
            )
            if success:
                messagebox.showinfo("Success", "Instance saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_load_instance():
        path = filedialog.askopenfilename(initialdir=SAVE_INSTANCE_INITIAL_DIR, filetypes=[("JSON files", "*.json")])
        if path:
            grid, starts, goals, rp = load_instance_from_file(path)
            state.map_var.set(grid)
            state.agent_list.clear()
            for s, g in zip(starts, goals):
                state.agent_list.append((tuple(s), tuple(g)))
            update_agent_display()
            state.k_var.set(str(rp.k))
            state.h_var.set(str(rp.h))
            state.m_var.set(str(rp.m))
            for ftype in state.fail_type_vars:
                state.fail_type_vars[ftype].set(ftype in rp.selected_failure_types)

    def handle_simulate_plan():
        path = filedialog.askopenfilename(initialdir=LOAD_PLAN_INITIAL_DIR,filetypes=[("Pickle files", "*.pkl")])
        if path:
            solution, mapf_instance, robustness_params, grid_name = load_full_solution_pickle(path)
            if solution:
                grid = load_map(grid_name)
                vis_root = ctk.CTkToplevel()
                vis_root.title(TITLE_SIMULATE)
                vis_root.geometry(SIZE_SIMULATE)
                GridVisualizer(vis_root, grid, mapf_instance, robustness_params, solution)

    def handle_generate_instances():
        try:
            n = int(state.num_instances_var.get())
            a = int(state.num_agents_var.get())
            d = int(state.min_dist_var.get())
            name = state.name_set_var.get()
            mappa = state.map_gen_var.get()

            from src.domain.generation import generate_test_instances
            generate_test_instances(n, a, d, name, mappa)
            messagebox.showinfo("Success", f"{n} instances generated for map {mappa}.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_solve():
        if not state.map_var.get() or not state.agent_list:
            messagebox.showerror("Error", "Select a map and define at least one agent.")
            return
        
        def _solve_in_thread():
            try:
                from datetime import datetime
                print(f"\n*** Starting MAPF solve at {datetime.now()}")
                grid = load_map(state.map_var.get())
                starts = [s for s, _ in state.agent_list]
                goals = [g for _, g in state.agent_list]
                print(f"Starts: {starts}")
                print(f"Goals: {goals}")
                print(f"Number of agents: {len(starts)}")
                
                k = int(state.k_var.get())
                h = int(state.h_var.get())
                m = int(state.m_var.get())
                failtypes = [ftype for ftype, var in state.fail_type_vars.items() if var.get()]

                mapf_instance = MAPFInstance(build_graph(grid, len(starts)), starts, goals)
                initial_failed_actions = tuple(frozenset() for _ in starts)
                initial_failures = [0] * len(starts)
                r_up, r_down, predecessors, resilient_node_macroactions = set(), set(), dict(), dict()

                robustness_params = RobustnessParams(k, m, h, failtypes)
                sp = SearchParams(initial_failed_actions, initial_failures, r_up, r_down, predecessors, resilient_node_macroactions)
                
                # Timer setup - same as in handle_run_test
                import threading as _threading
                stop_event = _threading.Event()
                start_time = time.perf_counter()
                
                def _timeout_watcher():
                    if not stop_event.wait(timeout=TIME_LIMIT):
                        print(f"\nTimeout watcher: setting stop_event")
                        stop_event.set()
                
                watcher = _threading.Thread(target=_timeout_watcher, daemon=True)
                watcher.start()
                
                try:
                    solution, profiling_data = solve_mapf_with_profiling(mapf_instance, robustness_params, sp, stop_event=stop_event)
                    
                    elapsed_time = time.perf_counter() - start_time
                    
                    # Check if we were stopped by the timeout watcher
                    if stop_event.is_set():
                        timed_out = True
                        print(f"Warning: timeout reached after {elapsed_time:.2f}s")
                        #messagebox.showinfo("TIMEOUT", f"Timeout reached after {elapsed_time:.2f}s")
                        return

                    timed_out = False
                    if solution.tau_states:
                        print(f"*** Solve completed in {elapsed_time:.2f}s")
                        save_full_solution_pickle(solution, mapf_instance, robustness_params, state.map_var.get())
                        messagebox.showinfo("Success", f"{k}-resilient plan found successfully in {elapsed_time:.2f}s.")
                        vis_root = ctk.CTkToplevel()
                        vis_root.title(TITLE_SIMULATE)
                        vis_root.geometry(SIZE_SIMULATE)
                        GridVisualizer(vis_root, grid, mapf_instance, robustness_params, solution)
                    else:
                        print(f"*** No solution found in {elapsed_time:.2f}s")
                        messagebox.showinfo("No solution", "No resilient plan found.")
                    
                    # Record results to CSV
                    from src.utils.sperimental_analysis import build_solutions_csv
                    instances = [(state.map_var.get(), starts, goals)]
                    solutions = [solution]
                    stat = profiling_data if profiling_data else {}
                    stat["elapsed_time"] = elapsed_time
                    timing_stats = [stat]
                    timed_out_flags = [timed_out]
                    selected_set = "manual_solve"
                    build_solutions_csv(instances, robustness_params, solutions, selected_set, timing_stats, timed_out_flags)
                finally:
                    stop_event.set()
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error during planning: {e}")
        
        # Run solving in a separate thread to keep UI responsive
        thread = threading.Thread(target=_solve_in_thread, daemon=True)
        thread.start()

    def copy_console():
        content = console_textbox.get("0.0", "end-1c")
        root.clipboard_clear()
        root.clipboard_append(content)

    def clear_console():
        console_textbox.delete("1.0", "end")

    # Assign buttons
    state.add_button.configure(command=add_agent)
    state.remove_button.configure(command=remove_agent)
    state.save_instance_btn.configure(command=handle_save_instance)
    state.load_instance_btn.configure(command=handle_load_instance)
    state.simulate_plan_btn.configure(command=handle_simulate_plan)
    state.generate_instances_btn.configure(command=handle_generate_instances)
    state.solve_button.configure(command=handle_solve)
    state.copy_button.configure(command=copy_console)
    state.clear_button.configure(command=clear_console)


def handle_run_test(root, state):
    test_win = ctk.CTkToplevel(root)
    test_win.title(TITLE_RUN_TEST)
    test_win.geometry(SIZE_RUN_TEST)
    test_win.configure(bg="#f0f0f0")
    test_win.attributes('-topmost', True)

    main_test_frame = ctk.CTkFrame(test_win)
    main_test_frame.pack(fill="both", expand=True, padx=15, pady=15)

    ctk.CTkLabel(main_test_frame, text="Instance set:").grid(row=0, column=0, sticky="w", pady=5)
    test_sets = sorted(os.listdir(TEST_INSTANCES_DIR)) if os.path.exists(TEST_INSTANCES_DIR) else []
    test_set_combo = tctk.Combobox(main_test_frame, values=test_sets, width=25)
    test_set_combo.grid(row=0, column=1, pady=5, padx=(10, 0))

    ctk.CTkLabel(main_test_frame, text="k:").grid(row=1, column=0, sticky="w", pady=5)
    k_entry = tctk.Entry(main_test_frame, width=10)
    k_entry.grid(row=1, column=1, pady=5, padx=(10, 0), sticky="w")

    ctk.CTkLabel(main_test_frame, text="m:").grid(row=2, column=0, sticky="w", pady=5)
    m_entry = tctk.Entry(main_test_frame, width=10)
    m_entry.grid(row=2, column=1, pady=5, padx=(10, 0), sticky="w")

    ctk.CTkLabel(main_test_frame, text="h:").grid(row=3, column=0, sticky="w", pady=5)
    h_entry = tctk.Entry(main_test_frame, width=10)
    h_entry.grid(row=3, column=1, pady=5, padx=(10, 0), sticky="w")



    ctk.CTkLabel(main_test_frame, text="Failure types:").grid(row=4, column=0, columnspan=2, sticky="w", pady=(15, 5))
    failure_type_rows = len(state.fail_type_vars)
    for i, (ftype, var) in enumerate(state.fail_type_vars.items()):
        ctk.CTkCheckBox(main_test_frame, text=ftype, variable=var).grid(row=5 + i, column=0, columnspan=2, sticky="w", pady=2)

    ctk.CTkLabel(main_test_frame, text="Profiling:").grid(row=5 + failure_type_rows, column=0, columnspan=2, sticky="w", pady=(15, 5))
    profiling_combo = tctk.Combobox(main_test_frame, values=["No", "Granular Profiling"], width=25, state="readonly")
    profiling_combo.set("No")
    profiling_combo.grid(row=6 + failure_type_rows, column=0, columnspan=2, pady=5, padx=(10, 0))

    def _run_test_in_thread(selected_set, robustness_params, instances, selected_failtypes, enable_profiling):
        import time
        from datetime import datetime
        from src.utils.map_handler import build_graph
        from src.domain.solver.Solution import Solution
        from src.utils.profiling import generate_profiling_markdown, save_profiling_report

        successes, timeouts = 0, 0
        solutions, timing_stats, timed_out_flags = [], [], []

        for idx, instance in enumerate(instances):
            start_time = time.perf_counter()
            sol, stat, timed_out = None, {}, False
            profiling_data_complete = {}
            try:
                print(f"\n*** Processing instance {idx+1}/{len(instances)}...")
                map_name, starts, goals = instance
                grid = load_map(map_name)
                mapf_instance = MAPFInstance(build_graph(grid, len(starts)), starts, goals)
                init_failures = [0] * len(starts)
                init_failed_actions = tuple(frozenset() for _ in starts)
                r_up, r_down, pred, res_macro = set(), set(), dict(), dict()
                search_params = SearchParams(init_failed_actions, init_failures, r_up, r_down, pred, res_macro)

                import threading as _threading

                stop_event = _threading.Event()

                # Timer thread that sets stop_event after TIME_LIMIT seconds
                def _timeout_watcher():
                    if not stop_event.wait(timeout=TIME_LIMIT):
                        # wait() returned False → timeout expired, solver still running
                        print(f"\nTimeout watcher: setting stop_event for instance {idx}")
                        stop_event.set()

                watcher = _threading.Thread(target=_timeout_watcher, daemon=True)
                watcher.start()
                try:
                    if enable_profiling == "Granular Profiling":
                        print("!!! START TIME:", datetime.now() ,f" instance: {idx}]")
                        sol, profiling_data_complete = solve_mapf_with_granular_profiling(
                            mapf_instance,
                            robustness_params,
                            search_params,
                            False,  # verbose=False
                            stop_event=stop_event,
                        )
                        elapsed_time = time.perf_counter() - start_time
                        stat = profiling_data_complete.get('granular_stats', {})
                        stat["elapsed_time"] = elapsed_time
                        print(f"!!! INSTANCE {idx} ELAPSED TIME]", elapsed_time)

                        try:
                            markdown_report = generate_profiling_markdown(
                                granular_stats=stat,
                                analysis=profiling_data_complete.get('analysis', {}),
                                elapsed_time=elapsed_time,
                                instance_info={
                                    'test_set': selected_set.split(".")[0],
                                    'instance_idx': idx + 1,
                                    'map_name': map_name,
                                    'num_agents': len(starts),
                                    'k': robustness_params.k,
                                    'm': robustness_params.m,
                                    'h': robustness_params.h,
                                    'failure_types': robustness_params.selected_failure_types
                                }
                            )
                            report_path = save_profiling_report(
                                markdown_report,
                                test_set=selected_set.split(".")[0],
                                instance_idx=idx + 1,
                                map_name=map_name
                            )
                            print(f"Profiling report saved: {report_path}")
                        except Exception as e:
                            import traceback
                            print(f"Warning: failed to save profiling report for instance {idx}: {e}")
                            print(f"[DEBUG] Exception type: {type(e).__name__}")
                            print(f"[DEBUG] Traceback:\n{traceback.format_exc()}")
                    else:
                        # Use profiling to capture statistics even in non-granular mode
                        sol, profiling_data_complete = solve_mapf_with_profiling(
                            mapf_instance,
                            robustness_params,
                            search_params,
                            stop_event=stop_event,
                        )
                        
                        elapsed_time = time.perf_counter() - start_time
                        stat = profiling_data_complete if profiling_data_complete else {}
                        stat["elapsed_time"] = elapsed_time
                        print(f"*** Instance {idx} completed in {elapsed_time:.2f}s")

                    # Check if we were stopped by the timeout watcher
                    if stop_event.is_set():
                        elapsed_time = time.perf_counter() - start_time
                        stat["elapsed_time"] = elapsed_time
                        print(f"Warning: timeout reached for instance {idx}")
                        #messagebox.showinfo("TIMEOUT", f"!! Timeout reached for instance {idx}")
                        timeouts += 1
                        timed_out = True
                        sol = None

                finally:
                    # Always signal the watcher to stop (in case solver finished early)
                    stop_event.set()

                timed_out_flags.append(timed_out)
                
                if sol and sol.tau_states:
                    selected_set_name = selected_set.split(".")[0]
                    save_full_solution_pickle(sol, mapf_instance, robustness_params, map_name, filename=f"{selected_set_name}_inst{idx}")
                    successes += 1
                else:
                    sol = Solution(None, set(), set(), dict(), dict())

                solutions.append(sol)
                timing_stats.append(stat)

            except Exception as e:
                print(f"Error on instance {idx}: {e}")
                elapsed_time = time.perf_counter() - start_time
                stat["elapsed_time"] = elapsed_time
                solutions.append(Solution(None, set(), set(), dict(), dict()))
                timing_stats.append(stat)
                timed_out_flags.append(timed_out)

        #build_solutions_csv(instances, robustness_params, solutions, selected_set, timing_stats, timed_out_flags)
        print(f"\n !! Test completed: {selected_set} with:\n\tk={robustness_params.k}\n\tm={robustness_params.m}\n\t{robustness_params.h}\n\t{robustness_params.selected_failure_types}\n\n{successes}/{len(instances)} successful, {timeouts} timeouts.")
        if enable_profiling == "Granular Profiling":
            messagebox.showinfo("Test completed", f"{selected_set} with:\n\tk={robustness_params.k}\n\tm={robustness_params.m}\n\t{robustness_params.h}\n\t{robustness_params.selected_failure_types}\n\n{successes}/{len(instances)} successful, {timeouts} timeouts\n\nResults saved in profiling reports.")

    def _handle_start_test():
        selected_set = test_set_combo.get()
        if not selected_set:
            messagebox.showerror("Error", "Select an instance set.")
            return

        try:
            k = int(k_entry.get())
            h = int(h_entry.get())
            m = int(m_entry.get())
        except ValueError:
            messagebox.showerror("Error", "k, h, and m must be integers.")
            return

        selected_failtypes = [ftype for ftype, var in state.fail_type_vars.items() if var.get()]
        if not selected_failtypes:
            messagebox.showerror("Error", "Select at least one failure type.")
            return

        filepath = os.path.join(DATA_DIR, "test_instances", selected_set)
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"No such file: {filepath}")
            return

        with open(filepath, "rb") as f:
            instances = pickle.load(f)

        robustness_params = RobustnessParams(k, m, h, selected_failtypes)
        enable_profiling = profiling_combo.get()
        thread = threading.Thread(target=_run_test_in_thread, args=(selected_set, robustness_params, instances, selected_failtypes, enable_profiling), daemon=True)
        thread.start()
        test_win.destroy()

    ctk.CTkButton(main_test_frame, text="Start test", command=_handle_start_test).grid(row=7 + failure_type_rows, column=0, columnspan=2, pady=20)


def handle_kill_terminal(console_textbox=None):
    """Interrupt any running computation and restart the GUI from scratch."""
    if console_textbox is not None:
        try:
            console_textbox.insert("end", "\n[Kill Terminal] Restarting GUI...\n")
            console_textbox.see("end")
        except Exception:
            pass

    # Schedule the restart after a short delay so the UI has time to flush
    try:
        # Find the root window from the textbox widget
        root = console_textbox.winfo_toplevel() if console_textbox is not None else None
    except Exception:
        root = None

    def _do_restart():
        import subprocess
        import os as _os
        # Restore original stdout/stderr before restarting
        try:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        except Exception:
            pass
        # Destroy the current GUI window
        try:
            if root is not None:
                root.destroy()
        except Exception:
            pass
        # Relaunch preserving cwd and PYTHONPATH so 'src' is resolvable
        cwd = _os.getcwd()
        env = _os.environ.copy()
        subprocess.Popen([sys.executable, "-m", "src.main"], cwd=cwd, env=env)
        _os._exit(0)

    if root is not None:
        root.after(200, _do_restart)
    else:
        _do_restart()