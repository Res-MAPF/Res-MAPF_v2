import networkx as nx
from pathlib import Path

MAPS_DIR = str(Path("maps/")) + "/"


def load_map(file_path):
    """Read a map file from MAPS_DIR, skipping its header up to the "map" marker line, and
    return the remaining lines as a 2D list of characters."""
    with open(MAPS_DIR + file_path, "r") as file:
        lines = file.readlines()

    map_start = lines.index("map\n") + 1
    grid = [list(line.strip()) for line in lines[map_start:] if line.strip()]
    return grid


def build_graph(grid, num_agents = None):
    """
    Build a NetworkX directed graph connecting every walkable ('.') cell to its 8-connected
    walkable neighbors, with edge weight 1 for cardinal moves and 1.414 (sqrt(2)) for diagonals;
    diagonal moves that would cut through a wall corner are disallowed.

    Args:
        grid: 2D grid where '.' = walkable, '@' = wall
        num_agents: accepted for signature compatibility with call sites elsewhere in the
            codebase (build_graph(grid, len(starts))); unused in this version of the solver

    Returns:
        NetworkX directed graph with weighted edges
    """
    if num_agents is None:
        num_agents = 1
    
    graph_dict = {}
    rows = len(grid)
    cols = len(grid[0])
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == ".":
                vertex = (i, j)
                neighbors = []
                directions = [
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                    (-1, -1),
                    (-1, 1),
                    (1, -1),
                    (1, 1),
                ]
                for dx, dy in directions:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < rows and 0 <= nj < cols and grid[ni][nj] == ".":
                        if dx != 0 and dy != 0:
                            if grid[i + dx][j] == "@" or grid[i][j + dy] == "@":  # disallow cutting a wall corner
                                continue
                        # Cost: cardinal=1, diagonal=1.414
                        cost = 1.414 if dx != 0 and dy != 0 else 1
                        
                        neighbors.append(((ni, nj), cost))
                graph_dict[vertex] = neighbors

    nx_graph = convert_to_nx_graph(graph_dict)
    return nx_graph


def convert_to_nx_graph(graph_dict):
    """
    Convert a {vertex: [(neighbor, cost), ...]} dictionary into a NetworkX directed graph.

    Args:
        graph_dict: Dictionary mapping vertices to neighbors with costs

    Returns:
        NetworkX directed graph with weighted edges
    """
    nx_graph = nx.DiGraph()
    for vertex, edges in graph_dict.items():
        for neighbor, cost in edges:
            nx_graph.add_edge(vertex, neighbor, weight=cost)
    
    return nx_graph
