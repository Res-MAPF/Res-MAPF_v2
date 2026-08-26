import os
import pickle
import networkx as nx
from pathlib import Path
import random

from src.utils.map_handler import build_graph, load_map


TEST_INSTANCES_DIR = str(Path("data/test_instances"))
MAX_DST_RANGE = 5

def generate_test_instances(n_instances, n_agents, min_dst, name, map_name):
    """Build n_instances random start/goal assignments for n_agents on map_name and pickle the
    resulting (map_name, starts, goals) list to TEST_INSTANCES_DIR/<name>.pkl. Each start/goal pair
    is separated by a shortest-path distance in [min_dst, min_dst + MAX_DST_RANGE]."""
    grid = load_map(map_name)
    graph = build_graph(grid, n_agents)

    instances = []
    for i in range(n_instances):
        starts = list()
        goals = list()
        for j in range(n_agents):
            start, goal = extract_start_goal_with_min_distance(
                graph, min_dst, starts, goals
            )
            if start is None or goal is None:
                raise ValueError(
                    f"Impossible to find couples of cells with {min_dst=} in {name}"
                )
            starts.append(start)
            goals.append(goal)
        instance = (map_name, starts, goals)
        instances.append(instance)

    os.makedirs(TEST_INSTANCES_DIR, exist_ok=True)
    with open(f"{TEST_INSTANCES_DIR}/{name}.pkl", "wb") as f:
        pickle.dump(instances, f)

def extract_start_goal_with_min_distance(graph, min_dst, starts, goals):
    """Sample a (start, goal) pair at shortest-path distance in [min_dst, min_dst + MAX_DST_RANGE],
    avoiding cells already used as starts/goals. Tries random sampling first; if that doesn't hit
    the distance window within max_attempts, falls back to a single-source search from a random
    start to find any goal at or beyond min_dst. Returns (None, None) if no pair can be found."""
    max_dst = min_dst + MAX_DST_RANGE
    max_attempts = 100
    nodes = list(graph.nodes)

    for i in range(max_attempts):
        start, goal = random.sample(nodes, 2)
        try:
            dist = nx.shortest_path_length(graph, start, goal)
            if dist >= min_dst and dist <= max_dst:
                if start in starts or goal in goals:
                    continue
                return start, goal
        except nx.NetworkXNoPath:
            continue

    for _ in range(len(nodes)):
        start = random.choice(nodes)
        lengths = nx.single_source_shortest_path_length(graph, start)

        candidates = [goal for goal, dist in lengths.items() if dist >= min_dst]
        if candidates:
            goal = random.choice(candidates)
            if start in starts or goal in goals:
                continue
            return start, goal
    return None, None
