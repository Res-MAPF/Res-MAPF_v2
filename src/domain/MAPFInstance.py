class MAPFInstance:
    """The problem to solve: a navigation graph plus each agent's start and goal cell."""
    def __init__(self, graph, starts, goals):
        self.graph = graph
        self.starts = starts
        self.goals = goals

class RobustnessParams:
    """The resilience budget a plan must be solved under.

    k: total number of failures the plan must tolerate.
    m: max number of distinct agents any tolerated failure combination may affect.
    h: max number of failures a single agent may individually suffer.
    selected_failure_types: subset of failure semantics to consider
        ("topw", "tops", "individual", "high-level" - see resplan_solver.compute_affected_actions).
    """
    def __init__(self, k, m, h, selected_failure_types):
        self.k = k
        self.m = m
        self.h = h
        self.selected_failure_types = selected_failure_types

class SearchParams:
    """Search state carried into a solve, allowing it to resume instead of restarting from scratch.

    A fresh solve starts these empty/zeroed. The GUI's interactive failure-simulation flow instead
    passes in a previous solution's r_up/r_down/predecessors here to resume the search from there.
    """
    def __init__(self, initial_failed_actions, initial_failures, r_up, r_down, predecessors, resilient_node_macroactions):
        self.initial_failed_actions = initial_failed_actions
        self.initial_failures = initial_failures
        self.r_up = r_up
        self.r_down = r_down
        self.predecessors = predecessors
        self.resilient_node_macroactions = resilient_node_macroactions
