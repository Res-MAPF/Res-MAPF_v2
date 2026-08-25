import heapq
from bisect import bisect_left
from collections import defaultdict

from copy import deepcopy

from math import sqrt

from src.utils.granular_profiler import profile_section, get_profiler

_profiler = get_profiler()


HIGH_LEVEL_MOVES = {
    (-1, 0): "up",
    (1, 0): "down",
    (0, -1): "left",
    (0, 1): "right",
    (-1, 1): "up_right",
    (-1, -1): "up_left",
    (1, 1): "down_right",
    (1, -1): "down_left",
    (0, 0): "wait",
}


def move_real_cost(from_pos, to_pos):
    """Real geometric cost of a single move: sqrt(2) for diagonal, 1 for
    cardinal, 0 for staying put.

    Every move costs exactly 1 timestep in SIPPS's own g/f accounting, so it
    cannot distinguish a path that wastes a diagonal detour from one that goes
    straight when both take the same number of timesteps. This is used only
    to break that kind of tie in favor of the geometrically shorter route.
    """
    if from_pos == to_pos:
        return 0
    dr = to_pos[0] - from_pos[0]
    dc = to_pos[1] - from_pos[1]
    return sqrt(2) if dr != 0 and dc != 0 else 1


def get_valid_successors(graph, node, removed_edges):
    """Get successors of a node, excluding edges in removed_edges set.
    
    Args:
        graph: NetworkX directed graph
        node: Current node
        removed_edges: Set of (from_node, to_node) tuples that are logically removed
        
    Returns:
        List of valid successor nodes
    """
    return [w for w in graph.successors(node) if (node, w) not in removed_edges]


class SafeIntervalCache:
    """Incremental cache for safe interval tables.
    
    Only recomputes T_table entries for vertices where constraints have changed.
    Stored on graph object to maintain state across agent searches.
    """
    def __init__(self):
        self.cached_T = {}  # vertex -> intervals
        self.cached_hard_by_vertex = {}  # vertex -> set of hard times
        self.cached_soft_by_vertex = {}  # vertex -> set of soft times
    
    def get_or_update_table(self, graph, Oh_vertex, Oh_target, Os_vertex, Os_target, max_time):
        """Get T_table, recomputing only vertices with changed constraints.

        Args:
            graph: NetworkX graph (original, unmodified - removed edges are tracked separately)
            Oh_vertex, Oh_target: Hard vertex constraints
            Os_vertex, Os_target: Soft vertex constraints
            max_time: Maximum timestep
            
        Returns:
            dict: Complete T_table {vertex -> [(start, end), ...]} for all nodes in graph
        """
        # Index new constraints by vertex
        new_hard_by_vertex = defaultdict(set)
        for v, t in Oh_vertex | Oh_target:
            new_hard_by_vertex[v].add(t)

        new_soft_by_vertex = defaultdict(set)
        for v, t in Os_vertex | Os_target:
            new_soft_by_vertex[v].add(t)

        # Identify vertices requiring recomputation
        changed_vertices = set()

        all_constraint_vertices = (
            self.cached_hard_by_vertex.keys()
            | self.cached_soft_by_vertex.keys()
            | new_hard_by_vertex.keys()
            | new_soft_by_vertex.keys()
        )
        
        # Check for constraint changes on existing cached vertices
        for v in all_constraint_vertices:
            old_hard = self.cached_hard_by_vertex.get(v, set())
            old_soft = self.cached_soft_by_vertex.get(v, set())
            new_hard = new_hard_by_vertex.get(v, set())
            new_soft = new_soft_by_vertex.get(v, set())

            # If constraints changed, mark vertex for recomputation
            if old_hard != new_hard or old_soft != new_soft:
                changed_vertices.add(v)

        # Also recompute any vertex that isn't cached yet, so the table stays
        # complete for every node in the graph (removed edges don't affect nodes)
        for v in graph.nodes:
            if v not in self.cached_T:
                changed_vertices.add(v)

        # Update cache with new constraint sets
        self.cached_hard_by_vertex = dict(new_hard_by_vertex)
        self.cached_soft_by_vertex = dict(new_soft_by_vertex)

        # Recompute only changed vertices
        for v in changed_vertices:
            hard_times = self.cached_hard_by_vertex.get(v, set())
            soft_times = self.cached_soft_by_vertex.get(v, set())
            self.cached_T[v] = self.compute_vertex_intervals(hard_times, soft_times, max_time)
        
        # Return the complete table: intervals for every vertex in graph.nodes
        result = {v: self.cached_T[v] for v in graph.nodes}
        return result
    
    def compute_vertex_intervals(self, hard_times, soft_times, max_time):
        """Compute safe intervals for a single vertex.
        
        Args:
            hard_times: Set of timesteps with hard constraints
            soft_times: Set of timesteps with soft constraints
            max_time: Maximum timestep
            
        Returns:
            list: [(start, end), ...] intervals where vertex is safe
        """
        intervals = []
        t = 0
        while t < max_time:
            if t in hard_times:
                t += 1
                continue
            
            soft_flag = t in soft_times
            start = t
            t += 1
            while t < max_time and t not in hard_times and (t in soft_times) == soft_flag:
                t += 1
            end = t
            intervals.append((start, end))
        
        return intervals

class CBSNode:
    def __init__(self, constraints=None, solution=None, cost=float("inf")):
        self.constraints = constraints if constraints is not None else set()
        self.solution = solution
        self.cost = cost

    def __lt__(self, other):
        return self.cost < other.cost

    def compute_low_level_solution(self, starts, goals, original_graph, failed_actions, h_maps,
                                    parent_solution=None, agent_to_compute=None,
                                    initial_paths=None, stop_event=None):
        """
        Compute low-level solutions for agents.

        Args:
            starts: List of start positions for all agents
            goals: List of goal positions for all agents
            original_graph: Original navigation graph
            failed_actions: Failed actions per agent
            h_maps: Heuristic maps for all agents
            parent_solution: Optional parent solution to reuse paths from (CBS optimization)
            agent_to_compute: If provided, only compute this single agent's path
            initial_paths: Optional list; None entries trigger replanning, existing
                entries are reused as-is and pre-seed the soft constraints
            stop_event: Optional threading event for early termination
        """
        # Determine which agents to compute and pre-populate soft-constraint paths
        if parent_solution is not None and agent_to_compute is not None:
            agents_to_compute = [agent_to_compute]
            paths = [parent_solution[j] for j in range(len(starts)) if j != agent_to_compute]
        elif initial_paths is not None:
            # Only replan agents with a None entry; others pre-seed soft constraints
            agents_to_compute = [i for i in range(len(starts)) if initial_paths[i] is None]
            paths = [p for p in initial_paths if p is not None]
        else:
            agents_to_compute = list(range(len(starts)))
            paths = []

        newly_computed = {}  # agent_idx -> path (used in initial_paths mode only)
        total_cost = 0

        for i in agents_to_compute:
            start = starts[i]
            goal = goals[i]
            try:
                with profile_section(f"low_level_search_cbs_agent_{i}"):
                    path, cost = low_level_search_cbs(
                        i,
                        start,
                        goal,
                        self.constraints,
                        original_graph,
                        failed_actions,
                        h_maps[i],
                        paths=paths,
                        goals=goals,
                        stop_event=stop_event,
                    )
            except Exception as exc:
                print(
                    f"Low-level search failed for agent {i} with start {start} and goal {goal}: {exc}"
                )
                return False

            if path is None:
                return False

            paths.append(path)
            total_cost += cost
            if initial_paths is not None:
                newly_computed[i] = path

        # Build final solution
        if parent_solution is not None and agent_to_compute is not None:
            # Merge: reuse parent paths + insert newly computed path
            self.solution = list(parent_solution)
            self.solution[agent_to_compute] = paths[-1]
            total_cost = sum(len(p) - 1 for p in self.solution)
        elif initial_paths is not None:
            # Merge: use initial_paths as base, fill in newly computed paths
            self.solution = list(initial_paths)
            for i, p in newly_computed.items():
                self.solution[i] = p
            total_cost = sum(len(p) - 1 for p in self.solution)
        else:
            # Standard case: all paths were computed
            self.solution = paths

        self.cost = total_cost
        return True

class SIPPSNode:
    def __init__(
            self,
            v,
            interval,
            interval_id,
            g,
            heuristic_map,
            Os_vertex,
            Os_edge,
            Os_target,
            T,
            Tprime,
            is_goal=False,
            parent=None,
            cfuture=0,
    ):
        self.v = v
        self.low, self.high = interval
        self.interval_id = interval_id
        # arrival time = low
        self.g = g

        self.real_cost = (
            parent.real_cost + move_real_cost(parent.v, v)
            if parent is not None
            else 0
        )
        self.c_conflicts = self.compute_c_value(
            parent, Os_vertex, Os_edge, Os_target, cfuture
        )

        if is_goal:
            self.h = 0
        else:
            d = heuristic_map[v]
            if self.c_conflicts == 0:
                # No soft collision
                self.h = max(d, Tprime - self.low)
            else:
                # At least one soft collision
                self.h = max(d, T - self.low)

        self.f = self.g + self.h
        self.is_goal = is_goal
        self.parent = parent

    def __lt__(self, other):
        # Lexicographic ordering: conflicts first, then f-value, then real
        # geometric distance so far (tie-break, see move_real_cost).
        return (self.c_conflicts, self.f, self.real_cost) < \
               (other.c_conflicts, other.f, other.real_cost)

    def is_identical(self, other):
        return (self.v, self.interval_id, self.is_goal) == (
            other.v,
            other.interval_id,
            other.is_goal,
        )

    def dominates_weakly(self, other):
        if self.is_identical(other):
            if (
                self.low <= other.low
                and self.high >= other.high
                and self.c_conflicts <= other.c_conflicts
                and self.real_cost <= other.real_cost
            ):
                return True
        return False

    def compute_c_value(self, parent, Os_vertex, Os_edge, Os_target, cfuture):
        c_conflicts = 0

        # Vertex soft constraints: all timestamped conflicts from other agents' paths.
        # These are purely conflict-based.
        for (v_obs, t_obs) in Os_vertex.union(Os_target):
            if v_obs == self.v and t_obs >= self.low and t_obs < self.high:
                c_conflicts += 1

        # Edge soft constraint: penalize traversing an edge used by another agent at the same time.
        if parent:
            if ((parent.v, self.v), self.low) in Os_edge:
                c_conflicts += 1

        # Accumulate from parent
        if parent:
            c_conflicts += parent.c_conflicts

        c_conflicts += cfuture
        return c_conflicts


def compute_plan_cbs(starts, goals, failed_actions, states_down, graph, h_maps,
                     initial_paths=None, stop_event=None):
    open_list = []
    closed_tau_set = set()  # Avoids repeated exploration of tau states
    visited_constraints = set()

    root = CBSNode()

    if tuple(starts) in states_down:
        return None, None, None

    # Initialize SafeIntervalCache on graph for incremental T_table updates
    if not hasattr(graph, "_safe_interval_cache"):
        graph._safe_interval_cache = SafeIntervalCache()

    with profile_section("root_compute_low_level_solution"):
        if not root.compute_low_level_solution(
            starts, goals, graph, failed_actions, h_maps,
            initial_paths=initial_paths, stop_event=stop_event
        ):
            return None, None, None

    heapq.heappush(open_list, root)

    cbs_iteration_count = 0
    while open_list:
        if stop_event is not None and stop_event.is_set():
            print("\n[CBS] Stop event received, aborting.")
            return None, None, None

        cbs_iteration_count += 1
        with profile_section(f"CBS_iteration_{cbs_iteration_count}"):
            node = heapq.heappop(open_list)

            with profile_section("build_solution"):
                pi, tau = build_solution(node)
            tau_key = tuple(map(tuple, tau))

            # Solution already explored
            if tau_key in closed_tau_set:
                continue
            closed_tau_set.add(tau_key)

            with profile_section("detect_conflict"):
                conflict = detect_conflict(node.solution)

            if conflict is None:
                found_down_state = False

                # Check if solution contains a down state
                for t, state in enumerate(tau):
                    if state in states_down:
                        found_down_state = True
                        _profiler.increment_counter('cbs_non_resilient_states')

                        for agent, pos in enumerate(state):
                            if (agent, pos, t, "vertex") in node.constraints:
                                continue

                            constraint_key = (agent, pos, t, "vertex")
                            if constraint_key in visited_constraints:
                                continue
                            visited_constraints.add(constraint_key)

                            constraints_new = deepcopy(node.constraints)
                            constraints_new.add(constraint_key)

                            child = CBSNode(constraints_new)
                            if child.compute_low_level_solution(
                                starts, goals, graph, failed_actions, h_maps,
                                parent_solution=node.solution,
                                agent_to_compute=agent,
                                stop_event=stop_event,
                            ):
                                heapq.heappush(open_list, child)

                        break  # Only first down state is handled

                if not found_down_state:
                    return pi, tau, node.solution

            # Conflicts are handled
            else:
                _profiler.increment_counter('cbs_total_conflicts')
                if conflict[-1] == "vertex":
                    with profile_section("CBS_vertex_conflict"):
                        ai, aj, vertex, timestep, _ = conflict

                        constraints_ai = deepcopy(node.constraints)
                        constraints_ai.add((ai, vertex, timestep, "vertex"))
                        child_ai = CBSNode(constraints_ai)
                        if child_ai.compute_low_level_solution(
                            starts, goals, graph, failed_actions, h_maps,
                            parent_solution=node.solution,
                            agent_to_compute=ai,
                            stop_event=stop_event,
                        ):
                            heapq.heappush(open_list, child_ai)

                        constraints_aj = deepcopy(node.constraints)
                        constraints_aj.add((aj, vertex, timestep, "vertex"))
                        child_aj = CBSNode(constraints_aj)
                        if child_aj.compute_low_level_solution(
                            starts, goals, graph, failed_actions, h_maps,
                            parent_solution=node.solution,
                            agent_to_compute=aj,
                            stop_event=stop_event,
                        ):
                            heapq.heappush(open_list, child_aj)

                elif conflict[-1] == "edge":
                    with profile_section("CBS_edge_conflict"):
                        ai, aj, (u, v), timestep, _ = conflict

                        constraints_ai = deepcopy(node.constraints)
                        constraints_ai.add((ai, (u, v), timestep, "edge"))
                        child_ai = CBSNode(constraints_ai)
                        if child_ai.compute_low_level_solution(
                            starts, goals, graph, failed_actions, h_maps,
                            parent_solution=node.solution,
                            agent_to_compute=ai,
                            stop_event=stop_event,
                        ):
                            heapq.heappush(open_list, child_ai)

                        constraints_aj = deepcopy(node.constraints)
                        constraints_aj.add((aj, (v, u), timestep, "edge"))
                        child_aj = CBSNode(constraints_aj)
                        if child_aj.compute_low_level_solution(
                            starts, goals, graph, failed_actions, h_maps,
                            parent_solution=node.solution,
                            agent_to_compute=aj,
                            stop_event=stop_event,
                        ):
                            heapq.heappush(open_list, child_aj)

    return None, None, None


def first_allowed(t_start, hi, edge_key, vertex_key, e_times, v_times):
    """Return the smallest t in [t_start, hi) not blocked by e_times[edge_key] or v_times[vertex_key].

    Uses binary search (bisect_left) and jumps past contiguous blocked runs for O(log C) average cost.
    Returns None if every timestep in the range is blocked.
    """
    t = t_start
    while t < hi:
        # Check edge constraint
        et = e_times.get(edge_key)
        if et is not None:
            idx = bisect_left(et, t)
            if idx < len(et) and et[idx] == t:
                # Advance past the contiguous blocked run
                while idx + 1 < len(et) and et[idx + 1] == et[idx] + 1:
                    idx += 1
                t = et[idx] + 1
                continue
        # Check vertex constraint
        vt = v_times.get(vertex_key)
        if vt is not None:
            idx = bisect_left(vt, t)
            if idx < len(vt) and vt[idx] == t:
                while idx + 1 < len(vt) and vt[idx + 1] == vt[idx] + 1:
                    idx += 1
                t = vt[idx] + 1
                continue
        return t
    return None


def low_level_search_cbs(
    agent_id,
    start,
    goal,
    constraints,
    original_graph,
    failed_actions,
    heuristic_map,
    max_time=500,
    paths=None,
    goals=None,
    stop_event=None,
):
    Oh_vertex, Oh_edge, Oh_target = set(), set(), set()
    Os_vertex, Os_edge, Os_target = set(), set(), set()

    # Hard constraints are populated
    with profile_section(f"populate_hard_constraints_agent_{agent_id}"):
        for c in constraints:
            if c[0] != agent_id:
                continue
            if c[-1] == "vertex":
                Oh_vertex.add((c[1], c[2]))
            elif c[-1] == "edge":
                u, v = c[1]
                t = c[2]
                Oh_edge.add(((u, v), t + 1))

    # Soft constraints are populated
    with profile_section(f"populate_soft_constraints_agent_{agent_id}"):
        for path in paths or []:
            for t in range(len(path) - 1):
                Os_edge.add(((path[t], path[t + 1]), t + 1))
            for t, v in enumerate(path):
                Os_vertex.add((v, t))

    # Remove edges due to failed actions, track them for restoration
    with profile_section(f"graph_modification_agent_{agent_id}"):
        removed_edges = set()
        inv = {v: k for k, v in HIGH_LEVEL_MOVES.items()}
        for act, cell in failed_actions[agent_id]:
            if act not in inv:
                continue
            dr, dc = inv[act]
            to_cell = (cell[0] + dr, cell[1] + dc)
            if original_graph.has_edge(cell, to_cell):
                removed_edges.add((cell, to_cell))

    # Construction of safe interval table using incremental cache
    # Get cache from original graph (initialized in compute_plan_cbs)
    cache = original_graph._safe_interval_cache if hasattr(original_graph, '_safe_interval_cache') else SafeIntervalCache()

    with profile_section(f"build_safe_interval_table_agent_{agent_id}"):
        T_table = cache.get_or_update_table(
            original_graph, Oh_vertex, Oh_target,
            Os_vertex, Os_target, max_time
    )
    if start not in T_table or goal not in original_graph:
        return None, float("inf")

    with profile_section(f"compute_goal_times_agent_{agent_id}"):
        hard_times = [t for (v, t) in Oh_vertex | Oh_edge | Oh_target if v == goal]
        T = max(hard_times) + 1 if hard_times else 0
        soft_times = [t for (v, t) in Os_vertex | Os_target if v == goal]
        Tprime = (max(hard_times + soft_times) + 1) if (hard_times or soft_times) else 0

        # Pre-compute union to avoid repeated set operations in SIPPS loop
        Os_vertex_union = Os_vertex | Os_target

        root_int = T_table[start][0]
        root = SIPPSNode(
            start,
            root_int,
            0,
            root_int[0],
            heuristic_map,
            Os_vertex,
            Os_edge,
            Os_target,
            T,
            Tprime,
        )
    open_list, closed_list = [], []
    heapq.heappush(open_list, root)

    # Sorted constraint indexes so the binary search below runs in O(log C)
    hard_v_times = defaultdict(list)
    soft_v_times  = defaultdict(list)
    hard_e_times  = defaultdict(list)
    soft_e_times  = defaultdict(list)

    for cv, ct in Oh_vertex | Oh_target:
        hard_v_times[cv].append(ct)
    for cv, ct in Os_vertex | Os_target:
        soft_v_times[cv].append(ct)
    for (cu, cv), ct in Oh_edge:
        hard_e_times[(cu, cv)].append(ct)
    for (cu, cv), ct in Os_edge:
        soft_e_times[(cu, cv)].append(ct)
    for idx_d in (hard_v_times, soft_v_times, hard_e_times, soft_e_times):
        for idx_k in idx_d:
            idx_d[idx_k].sort()

    with profile_section(f"SIPPS_loop_agent_{agent_id}"):
        while open_list:
            if stop_event is not None and stop_event.is_set():
                print(f"\n[SIPPS agent {agent_id}] Stop event received, aborting.")
                return None, float("inf")

            # HEAP POP
            with profile_section(f"SIPPS_heap_pop_agent_{agent_id}"):
                n = heapq.heappop(open_list)

            # GOAL CHECK
            with profile_section(f"SIPPS_goal_check_agent_{agent_id}"):
                if n.is_goal:
                    return extract_path(n), n.g

                if n.v == goal and n.low >= T:
                    cf = sum(
                        1 for t in range(n.low, max_time) if (goal, t) in Os_vertex_union
                    )
                    if cf == 0:
                        return extract_path(n), n.g
                    else:
                        goal_node = SIPPSNode(
                            goal,
                            (n.low, n.high),
                            n.interval_id,
                            n.low,
                            heuristic_map,
                            Os_vertex,
                            Os_edge,
                            Os_target,
                            T,
                            Tprime,
                            is_goal=True,
                            parent=n,
                            cfuture=cf,
                        )
                        insert_node(goal_node, open_list, closed_list)

            # SUCCESSOR GENERATION - get valid successors
            with profile_section(f"SIPPS_successor_generation_agent_{agent_id}"):
                I = set()
                # Filter successors through removed_edges set
                for w in get_valid_successors(original_graph, n.v, removed_edges):
                    for idx, (lo, hi) in enumerate(T_table[w]):
                        # Check overlap: interval [n.low+1, n.high) overlaps [lo, hi)
                        if n.low + 1 < hi and lo < n.high:
                            I.add((w, idx))

                # Wait action (stay in current node)
                for idx, (lo, hi) in enumerate(T_table[n.v]):
                    if lo == n.high:
                        I.add((n.v, idx))

            # PROCESS SUCCESSORS
            for v, idx in I:
                with profile_section(f"SIPPS_successor_processing_agent_{agent_id}"):
                    lo, hi = T_table[v][idx]

                    # Avoid hard constraints (binary search)
                    with profile_section(f"SIPPS_hard_constraint_check_agent_{agent_id}"):
                        t_start = max(n.g + 1, lo)
                        t_hard = first_allowed(t_start, hi, (n.v, v), v, hard_e_times, hard_v_times)
                    if t_hard is None:
                        continue

                    # Avoid soft constraints (binary search)
                    with profile_section(f"SIPPS_soft_constraint_check_agent_{agent_id}"):
                        t_soft = first_allowed(t_hard, hi, (n.v, v), v, soft_e_times, soft_v_times)
                    if t_soft is None:
                        continue

                    # CREATE AND INSERT NODES
                    with profile_section(f"SIPPS_node_creation_agent_{agent_id}"):
                        if t_soft > t_hard:
                            n1 = SIPPSNode(
                                v,
                                (lo, t_soft),
                                idx,
                                t_hard,
                                heuristic_map,
                                Os_vertex,
                                Os_edge,
                                Os_target,
                                T,
                                Tprime,
                                parent=n,
                            )
                            insert_node(n1, open_list, closed_list)

                            n2 = SIPPSNode(
                                v,
                                (t_soft, hi),
                                idx,
                                t_soft,
                                heuristic_map,
                                Os_vertex,
                                Os_edge,
                                Os_target,
                                T,
                                Tprime,
                                parent=n,
                            )
                            insert_node(n2, open_list, closed_list)
                        else:
                            # No soft collision, t_hard is arrival time
                            n3 = SIPPSNode(
                                v,
                                (lo, hi),  # [lo, hi)
                                idx,
                                t_hard,  # arrival time reale
                                heuristic_map,
                                Os_vertex,
                                Os_edge,
                                Os_target,
                                T,
                                Tprime,
                                parent=n,
                            )
                            insert_node(n3, open_list, closed_list)
            
            # Add to closed list AFTER processing all successors
            with profile_section(f"SIPPS_node_close_agent_{agent_id}"):
                closed_list.append(n)
    
    return None, float("inf")


def build_solution(node):
    # Build joint states and macroactions
    if node.solution is None:
        return [], []

    paths = node.solution
    max_len = max(len(p) for p in paths)
    num_agents = len(paths)

    extended_paths = [path + [path[-1]] * (max_len - len(path)) for path in paths]

    joint_states = []
    for t in range(max_len):
        state_t = tuple(extended_paths[i][t] for i in range(num_agents))
        joint_states.append(state_t)

    return extract_pi_from_tau(joint_states), joint_states


def heuristic(graph, goal):
    h_map = {node: float("inf") for node in graph.nodes}
    h_map[goal] = 0
    heap = [(0, goal)]

    while heap:
        cost, current = heapq.heappop(heap)

        if cost > h_map[current]:
            continue

        for neighbor in graph.predecessors(current):
            edge_weight = graph[neighbor][current].get("weight", 1)
            new_cost = cost + edge_weight

            if new_cost < h_map[neighbor]:
                h_map[neighbor] = new_cost
                heapq.heappush(heap, (new_cost, neighbor))
    return h_map


def insert_node(n, open_list, closed_dict):
    n_list = set()

    for node in set(open_list).union(closed_dict):
        if n.is_identical(node):
            n_list.add(node)

    for q in n_list:
        if q.dominates_weakly(n):
            return

        elif n.dominates_weakly(q):
            if q in open_list:
                open_list.remove(q)
            if q in closed_dict:
                closed_dict.remove(q)

        elif n.low < q.high and q.low < n.high:
            if n.low < q.low:
                n.high = q.low
            else:
                q.high = n.low

            if n.high <= n.low:
                return

            if q.high <= q.low:
                if q in open_list:
                    open_list.remove(q)
                if q in closed_dict:
                    closed_dict.remove(q)
    heapq.heappush(open_list, n)



def extract_path(n):
    path_nodes = []
    node = n
    while node is not None:
        path_nodes.append(node)
        node = node.parent
    path_nodes.reverse()

    path = []
    current_time = path_nodes[0].g

    for i in range(len(path_nodes)):
        node = path_nodes[i]
        while current_time < node.g:
            path.append(path[-1] if path else node.v)
            current_time += 1

        path.append(node.v)
        current_time += 1

    return path


def extract_pi_from_tau(joint_states):
    macroactions = []

    for t in range(len(joint_states) - 1):
        current = joint_states[t]
        next_ = joint_states[t + 1]
        macroaction = []

        for i in range(len(current)):
            from_cell = current[i]
            to_cell = next_[i]
            action_name = infer_action(from_cell, to_cell)
            macroaction.append((action_name, from_cell))

        macroactions.append(tuple(macroaction))

    return macroactions


def detect_conflict(paths):
    max_len = max(len(p) for p in paths)

    # Vertex conflicts
    for t in range(max_len):
        positions = {}
        for i, path in enumerate(paths):
            pos = path[t] if t < len(path) else path[-1]

            if pos in positions:
                return (positions[pos], i, pos, t, "vertex")
            positions[pos] = i

    # Edge conflicts
    for t in range(max_len - 1):
        for i in range(len(paths)):
            if t + 1 >= len(paths[i]):
                continue

            pos_i_t = paths[i][t]
            pos_i_t1 = paths[i][t + 1]

            for j in range(i + 1, len(paths)):
                if t + 1 >= len(paths[j]):
                    continue

                pos_j_t = paths[j][t]
                pos_j_t1 = paths[j][t + 1]

                # Direct position swap (cardinal or diagonal)
                if pos_i_t == pos_j_t1 and pos_i_t1 == pos_j_t:
                    return (i, j, (pos_i_t, pos_i_t1), t, "edge")

                # Diagonal crossing: two agents traverse the same 2×2 square in
                # opposite diagonal directions.  They physically cross even though
                # they never occupy the same cell at the same timestep.
                if (abs(pos_i_t1[0] - pos_i_t[0]) == 1 and
                    abs(pos_i_t1[1] - pos_i_t[1]) == 1 and
                    abs(pos_j_t1[0] - pos_j_t[0]) == 1 and
                    abs(pos_j_t1[1] - pos_j_t[1]) == 1 and
                    pos_i_t[0] + pos_i_t1[0] == pos_j_t[0] + pos_j_t1[0] and
                    pos_i_t[1] + pos_i_t1[1] == pos_j_t[1] + pos_j_t1[1]):
                    return (i, j, (pos_i_t, pos_i_t1), t, "edge")

    return None


def infer_action(from_cell, to_cell):
    drow = to_cell[0] - from_cell[0]
    dcol = to_cell[1] - from_cell[1]

    if drow == 0 and dcol == 0:
        return "wait"
    elif drow == 0 and dcol == 1:
        return "right"
    elif drow == 0 and dcol == -1:
        return "left"
    elif drow == 1 and dcol == 0:
        return "down"
    elif drow == -1 and dcol == 0:
        return "up"
    elif drow == 1 and dcol == 1:
        return "down_right"
    elif drow == 1 and dcol == -1:
        return "down_left"
    elif drow == -1 and dcol == 1:
        return "up_right"
    elif drow == -1 and dcol == -1:
        return "up_left"
    else:
        return "invalid"
