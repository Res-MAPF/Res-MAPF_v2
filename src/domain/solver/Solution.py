class Solution:
    """Return-value container for solve_mapf(). tau_states is the resilient macro-action plan
    (None if none was found); resilient_cost and cbs_cost hold the resilient plan's cost and the
    unconstrained ("0-resilient") CBS baseline cost, used to compute the resilience overhead."""
    def __init__(
        self,
        tau_states,
        R_up,
        R_down,
        predecessors,
        resilient_node_macroactions,
        cost=None,
        cbs_cost=None,
    ):
        self.tau_states = tau_states
        self.R_up = R_up
        self.R_down = R_down
        self.predecessors = predecessors
        self.resilient_node_macroactions = resilient_node_macroactions
        self.resilient_cost = cost
        self.cbs_cost = cbs_cost
