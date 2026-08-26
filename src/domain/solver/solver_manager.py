SOLVER_ALGORITHM = "resplan"

def solve_mapf(
    mapf_instance, robustness_params, search_params, stop_event=None
):
    """Single entry point used by the GUI and both CLI runners to solve a MAPF instance.
    Dispatches on SOLVER_ALGORITHM so a new solving algorithm can be added or swapped in here
    without touching any call site."""
    if SOLVER_ALGORITHM == "resplan":
        from src.domain.solver.resplan_solver import resplan_mapf

        return resplan_mapf(
            mapf_instance, robustness_params, search_params, stop_event=stop_event
        )
    else:
        raise ValueError(f"Solving algorithm not recognized: {SOLVER_ALGORITHM}")
