import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon as MplPolygon
from scipy.spatial import ConvexHull
import random
import heapq
import os
import sys
import colorsys
from pathlib import Path

# Add path to import area_manager
sys.path.insert(0, str(Path(__file__).parent / "utils"))
from area_manager import AreaManager


def load_map(file_name):
    with open(file_name, "r") as f:
        lines = f.readlines()
    if lines[0].startswith("type"):
        lines = lines[4:]
    return [line.rstrip("\n") for line in lines]


def visualize_critical_areas(area_manager, grid, skeleton_coords, entrance_cells, shared_borders):
    """
    Visualizes critical areas and saves the image.
    
    Args:
        area_manager: AreaManager with already built areas
        grid: List of map strings
        skeleton_coords: Coordinates of the skeleton
        entrance_cells: Set of entrance/exit cells
        shared_borders: List of (y, x, area1, area2)
    """
    # Prepare binary grid for visualization
    char_grid = np.array([list(row) for row in grid])
    binary = (char_grid == ".").astype(np.uint8)
    
    # Random colors for areas
    rng = random.Random(42)
    def rand_color():
        return colorsys.hsv_to_rgb(rng.random(), 0.85, 0.95)
    
    area_colors = {aid: rand_color() for aid in area_manager.get_all_area_ids()}

    # ============================================================
    # VISUALIZATION
    # ============================================================
    fig, ax = plt.subplots(figsize=(14, 14))
    ax.imshow(binary, cmap="gray", origin="lower")

    # Draw Convex Hulls of areas
    for aid in area_manager.get_all_area_ids():
        color = area_colors[aid]
        area = area_manager.get_area(aid)
        all_cells = area.all_cells
        
        if len(all_cells) < 3:
            continue
        
        pts = np.array([[cx, cy] for cy, cx in all_cells])
        try:
            hull = ConvexHull(pts)
            patch = MplPolygon(
                pts[hull.vertices],
                closed=True,
                facecolor=color,
                edgecolor=color,
                alpha=0.22,
                linewidth=0,
                zorder=2,
            )
            ax.add_patch(patch)
        except Exception:
            pass

    # Draw spanning trees of areas
    for aid in area_manager.get_all_area_ids():
        color = area_colors[aid]
        area = area_manager.get_area(aid)
        all_cells = list(area.all_cells)
        
        if len(all_cells) < 2:
            continue
        
        pts = np.array([[cx, cy] for cy, cx in all_cells])
        n = len(pts)
        
        # Prim's algorithm for MST
        in_tree = [False] * n
        min_dist = [np.inf] * n
        parent = [-1] * n
        min_dist[0] = 0.0
        heap = [(0.0, 0)]
        
        while heap:
            d, u = heapq.heappop(heap)
            if in_tree[u]:
                continue
            in_tree[u] = True
            for v in range(n):
                if in_tree[v]:
                    continue
                dist = np.hypot(pts[u, 0] - pts[v, 0], pts[u, 1] - pts[v, 1])
                if dist < min_dist[v]:
                    min_dist[v] = dist
                    parent[v] = u
                    heapq.heappush(heap, (dist, v))
        
        # Draw edges of MST
        for v in range(1, n):
            u = parent[v]
            if u == -1:
                continue
            ax.plot(
                [pts[u, 0], pts[v, 0]],
                [pts[u, 1], pts[v, 1]],
                color=color,
                linewidth=1.2,
                alpha=0.75,
                zorder=3,
            )

    # Skeleton (red points)
    if skeleton_coords:
        sy, sx = zip(*skeleton_coords)
        ax.scatter(sx, sy, c="red", s=8, zorder=4)

    # Internal cells (colored scatter)
    for aid in area_manager.get_all_area_ids():
        color = area_colors[aid]
        area = area_manager.get_area(aid)
        int_only = area.cells - area.entrances
        
        if int_only:
            iy, ix = zip(*int_only)
            ax.scatter(ix, iy, color=color, s=90, edgecolors="none", alpha=0.9, zorder=5)

    # Simple entrances vs shared borders
    shared_border_cells = {(y, x) for y, x, a1, a2 in shared_borders}
    
    for aid in area_manager.get_all_area_ids():
        color = area_colors[aid]
        area = area_manager.get_area(aid)
        simple_ent = area.entrances - shared_border_cells
        
        if simple_ent:
            ey_l, ex_l = zip(*simple_ent)
            ax.scatter(
                ex_l,
                ey_l,
                facecolors=color,
                edgecolors="navy",
                linewidths=1.8,
                s=180,
                zorder=6,
            )

    # Shared borders between areas (white circles)
    if shared_border_cells:
        sy_l, sx_l = zip(*shared_border_cells)
        ax.scatter(
            sx_l,
            sy_l,
            facecolors="white",
            edgecolors="black",
            linewidths=2.5,
            s=220,
            zorder=7,
        )

    # Area labels
    for aid in area_manager.get_all_area_ids():
        area = area_manager.get_area(aid)
        all_cells = area.all_cells
        
        if not all_cells:
            continue
        
        cy_arr = np.array([c[0] for c in all_cells])
        cx_arr = np.array([c[1] for c in all_cells])
        
        ax.text(
            cx_arr.mean(),
            cy_arr.mean(),
            str(aid),
            fontsize=7,
            fontweight="bold",
            color="black",
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="round,pad=0.15",
                facecolor="white",
                alpha=0.75,
                edgecolor="none",
            ),
            zorder=8,
        )

    # Legend
    patches = [
        mpatches.Patch(color="red", label="Skeleton"),
        mpatches.Patch(color="gray", label="Internal critical cell"),
        mpatches.Patch(
            facecolor="white", edgecolor="navy", linewidth=1.8, label="Entrance/Exit"
        ),
        mpatches.Patch(
            facecolor="white", edgecolor="black", linewidth=2.5, label="Shared border (2 areas)"
        ),
    ]
    ax.legend(handles=patches, loc="lower right", fontsize=9)
    
    # Title
    ax.set_title(
        f"MAPF Areas  |  "
        f"{len(area_manager.get_all_area_ids())} areas  |  "
        f"{len(entrance_cells)} entrances/exits",
        fontsize=11,
    )
    ax.axis("equal")
    ax.invert_yaxis()
    plt.tight_layout()

    # Save image
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mapf_areas.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"\n✓ Image saved to: {out_path}")
    plt.close()

    return area_manager


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(current_dir, "../maps/random18_3.map")
    grid = load_map(map_path)
    
    # Build areas using AreaManager
    DIST_THRESHOLD = 4
    result = AreaManager.build_from_map(grid, DIST_THRESHOLD)
    area_manager = result["area_manager"]
    skeleton_coords = result["skeleton"]
    entrance_cells = result["entrance_cells"]
    shared_borders = result["shared_borders"]
    
    print(f"\n{'='*60}")
    print(f"  {area_manager}")
    print(f"{'='*60}")
    for aid in area_manager.get_all_area_ids():
        area = area_manager.get_area(aid)
        print(f"  Area {area.id:>3} | int={area.internal_count:>3} | ent={area.entrance_count:>2} "
              f"| tot={area.size:>3}")
    print(f"{'='*60}\n")
    
    # Visualize and save image
    visualize_critical_areas(area_manager, grid, skeleton_coords, entrance_cells, shared_borders)
    
    # Save areas for future use
    areas_json_path = Path(os.path.dirname(os.path.abspath(__file__))) / "mapf_areas.json"
    area_manager.save(areas_json_path)
    print(f"✓ Areas saved to: {areas_json_path}\n")
