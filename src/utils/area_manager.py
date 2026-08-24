import json
import pickle
from pathlib import Path
from typing import Dict, Set, Tuple, List, Optional
import numpy as np
from collections import deque
from skimage.morphology import skeletonize


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return int(obj) if isinstance(obj, np.integer) else float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class Area:
    """Represents a single critical area."""
    
    def __init__(self, area_id: int, cells: Set[Tuple[int, int]], 
                 entrances: Set[Tuple[int, int]], capacity: int = 0):
        self.id = area_id
        self.cells = cells
        self.entrances = entrances
        self.all_cells = cells | entrances
        self.capacity = capacity  # Minimum passage width in the area (bottleneck limit)
    
    @property
    def size(self) -> int:
        """Total number of cells (internal + entrances)."""
        return len(self.all_cells)
    
    @property
    def internal_count(self) -> int:
        """Number of internal cells (non-entrances)."""
        return len(self.cells - self.entrances)
    
    @property
    def entrance_count(self) -> int:
        """Number of entrances."""
        return len(self.entrances)
    
    def contains_cell(self, y: int, x: int) -> bool:
        """O(1): Check if a cell is in this area."""
        return (y, x) in self.all_cells
    
    def to_dict(self) -> dict:
        """Serialize the area to dict for JSON."""
        return {
            "id": self.id,
            "cells": list(self.cells),
            "entrances": list(self.entrances),
            "capacity": self.capacity,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Area":
        """Deserialize the area from dict."""
        return cls(
            area_id=data["id"],
            cells=set(tuple(c) for c in data["cells"]),
            entrances=set(tuple(c) for c in data["entrances"]),
            capacity=data.get("capacity", 0),
        )


class AreaManager:
    """Efficiently manages areas and their lookups."""
    
    def __init__(self):
        self.areas: Dict[int, Area] = {}
        self.cell_to_area: Dict[Tuple[int, int], int] = {}
    
    def add_area(self, area_id: int, cells: Set[Tuple[int, int]], 
                 entrances: Set[Tuple[int, int]], capacity: int = 0) -> None:
        """Adds an area to the manager.
        
        Args:
            area_id: Unique identifier for the area
            cells: Set of internal cells
            entrances: Set of entrance cells
            capacity: Minimum passage width (bottleneck limit for agent capacity)
        """
        area = Area(area_id, cells, entrances, capacity)
        self.areas[area_id] = area
        
        # Populates cell_to_area for fast lookups
        for cell in area.all_cells:
            self.cell_to_area[cell] = area_id
    
    def get_area_by_position(self, y: int, x: int) -> Optional[Area]:
        """
        O(1): Finds the area to which a position belongs.
        
        Args:
            y, x: Coordinates of the position
            
        Returns:
            Area if found, None otherwise
        """
        area_id = self.cell_to_area.get((y, x))
        if area_id is not None:
            return self.areas.get(area_id)
        return None
    
    def get_area(self, area_id: int) -> Optional[Area]:
        """O(1): Retrieves an area by ID."""
        return self.areas.get(area_id)
    
    def get_area_cells(self, area_id: int) -> Set[Tuple[int, int]]:
        """O(1): Retrieves all cells (internal + entrances) of an area."""
        area = self.areas.get(area_id)
        return area.all_cells if area else set()
    
    def get_area_internal_cells(self, area_id: int) -> Set[Tuple[int, int]]:
        """O(1): Retrieves only internal cells (non-entrances)."""
        area = self.areas.get(area_id)
        return area.cells if area else set()
    
    def get_area_entrances(self, area_id: int) -> Set[Tuple[int, int]]:
        """O(1): Retrieves the entrances of an area."""
        area = self.areas.get(area_id)
        return area.entrances if area else set()
    
    def get_all_areas(self) -> Dict[int, Area]:
        """Returns all areas."""
        return self.areas.copy()
    
    def get_all_area_ids(self) -> List[int]:
        """Returns the sorted list of all area_ids."""
        return sorted(self.areas.keys())
    
    def is_in_critical_area(self, y: int, x: int) -> bool:
        """O(1): Checks if a position is in a critical area."""
        return (y, x) in self.cell_to_area
    
    def get_neighbor_areas(self, area_id: int) -> Set[int]:
        """
        O(n) where n is the number of cells of the area.
        Finds all areas adjacent to this one.
        """
        area = self.areas.get(area_id)
        if not area:
            return set()
        
        neighbor_ids = set()
        for y, x in area.all_cells:
            # Checks the 8 neighbors
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    neighbor_id = self.cell_to_area.get((ny, nx))
                    if neighbor_id is not None and neighbor_id != area_id:
                        neighbor_ids.add(neighbor_id)
        
        return neighbor_ids
    
    def get_path_areas(self, path: List[Tuple[int, int]]) -> List[Tuple[int, Area]]:
        """
        O(len(path)): Returns the areas traversed by a path,
        removing duplicates and maintaining order.
        
        Returns:
            List of (timestep, area) where timestep is the first moment
            the agent occupies an area
        """
        areas_in_path = []
        last_area_id = None
        
        for t, (y, x) in enumerate(path):
            area_id = self.cell_to_area.get((y, x))
            if area_id is not None and area_id != last_area_id:
                area = self.areas[area_id]
                areas_in_path.append((t, area))
                last_area_id = area_id
        
        return areas_in_path
    
    def save(self, filepath: Path) -> None:
        """Saves areas in JSON format."""
        data = {
            "areas": {
                str(aid): area.to_dict() 
                for aid, area in self.areas.items()
            }
        }
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, cls=NumpyEncoder)
    
    def save_binary(self, filepath: Path) -> None:
        """Saves areas in pickle format (faster for large datasets)."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump({
                "areas": self.areas,
                "cell_to_area": self.cell_to_area,
            }, f)
    
    @classmethod
    def load(cls, filepath: Path) -> "AreaManager":
        """Loads areas from JSON file."""
        manager = cls()
        with open(filepath, "r") as f:
            data = json.load(f)
        
        for aid_str, area_data in data.get("areas", {}).items():
            area = Area.from_dict(area_data)
            manager.areas[area.id] = area
            for cell in area.all_cells:
                manager.cell_to_area[cell] = area.id
        
        return manager
    
    @classmethod
    def load_binary(cls, filepath: Path) -> "AreaManager":
        """Loads areas from pickle file."""
        manager = cls()
        with open(filepath, "rb") as f:
            data = pickle.load(f)
        
        manager.areas = data["areas"]
        manager.cell_to_area = data["cell_to_area"]
        return manager
    
    def __repr__(self) -> str:
        total_cells = sum(area.size for area in self.areas.values())
        return (f"AreaManager(areas={len(self.areas)}, "
                f"total_cells={total_cells})")
    
    @classmethod
    def build_from_map(cls, grid: List[str], num_agents: int = 1) -> Dict:
        """
        Builds an AreaManager from a map, identifying all critical areas.
        
        Args:
            grid: List of strings representing the map ('.' = walkable, '@' = wall)
            num_agents: Number of agents; areas with passage width < num_agents are critical (default 1)
            
        Returns:
            Dict with:
                - 'area_manager': Configured AreaManager
                - 'skeleton': skeleton coordinates
                - 'entrance_cells': set of entrance/exit cells
                - 'shared_borders': list of (y, x, area1, area2) shared borders
        """
        dist_threshold = num_agents
        char_grid = np.array([list(row) for row in grid])
        binary = (char_grid == ".").astype(np.uint8)
        rows, cols = binary.shape

        skeleton = skeletonize(binary)
        sk_coords = list(zip(*np.where(skeleton)))

        dirs8 = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        dirs4 = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        diag_dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

        def can_move(y, x, ny, nx):
            if not (0 <= ny < rows and 0 <= nx < cols):
                return False
            if binary[ny, nx] == 0:
                return False
            dy, dx = ny - y, nx - x
            if (dy, dx) in diag_dirs:
                if binary[y + dy, x] == 0 or binary[y, x + dx] == 0:
                    return False
            return True

        def dist_to_wall(y, x, dy, dx):
            d, cy, cx = 0, y, x
            while True:
                ny, nx = cy + dy, cx + dx
                if not (0 <= ny < rows and 0 <= nx < cols):
                    return d
                if binary[ny, nx] == 0:
                    return d
                if (dy, dx) in diag_dirs:
                    if binary[cy + dy, cx] == 0 or binary[cy, cx + dx] == 0:
                        return d
                cy, cx = ny, nx
                d += 1

        def is_critical_cell(y, x):
            if dist_to_wall(y, x, 0, 1) + dist_to_wall(y, x, 0, -1) + 1 < dist_threshold:
                return True
            if dist_to_wall(y, x, 1, 0) + dist_to_wall(y, x, -1, 0) + 1 < dist_threshold:
                return True
            return False

        def critical_directions(y, x):
            dirs = []
            if dist_to_wall(y, x, 0, 1) + dist_to_wall(y, x, 0, -1) + 1 < dist_threshold:
                dirs.append("H")
            if dist_to_wall(y, x, 1, 0) + dist_to_wall(y, x, -1, 0) + 1 < dist_threshold:
                dirs.append("V")
            return dirs

        def is_corner_cell(y, x):
            for (dy1, dx1), (dy2, dx2) in [
                [(0, 1), (1, 0)],
                [(0, 1), (-1, 0)],
                [(0, -1), (1, 0)],
                [(0, -1), (-1, 0)],
            ]:
                b1 = (not (0 <= y + dy1 < rows and 0 <= x + dx1 < cols) or 
                      binary[y + dy1, x + dx1] == 0)
                b2 = (not (0 <= y + dy2 < rows and 0 <= x + dx2 < cols) or 
                      binary[y + dy2, x + dx2] == 0)
                if b1 and b2:
                    return True
            return False

        # Identify critical cells
        critical_seed = {(y, x) for y, x in sk_coords if is_critical_cell(y, x)}
        critical_all = set(critical_seed)
        queue = list(critical_seed)
        # Take one critical cell, check its 8 neighbors, if they are walkable and not already in critical_all, check if they are critical or corner cells. If yes, add them to critical_all and the queue. Repeat until the queue is empty.
        while queue:
            y, x = queue.pop()
            for dy, dx in dirs8:
                ny, nx = y + dy, x + dx
                if not can_move(y, x, ny, nx):
                    continue
                if (ny, nx) in critical_all:
                    continue
                if is_critical_cell(ny, nx) or is_corner_cell(ny, nx):
                    critical_all.add((ny, nx))
                    queue.append((ny, nx))

        critical_dirs = {(y, x): critical_directions(y, x) for y, x in critical_all}

        width_h, width_v = {}, {}
        for y, x in critical_all:
            width_h[(y, x)] = dist_to_wall(y, x, 0, 1) + dist_to_wall(y, x, 0, -1) + 1
            width_v[(y, x)] = dist_to_wall(y, x, 1, 0) + dist_to_wall(y, x, -1, 0) + 1

        # Detects a cell that is a lone narrow point, not part of a longer narrow strip/corner chain.
        # This is used later to avoid adding such cells to entrance_cells
        def single_cell_isolated(y, x):                 
            dirs = critical_dirs[(y, x)]
            for d in dirs:
                if d == "H" and width_h[(y, x)] == 1:
                    neighbors = [(y - 1, x), (y + 1, x)]
                    if all(
                        width_h.get((ny, nx), 0) != 1 and not is_corner_cell(ny, nx)
                        for ny, nx in neighbors
                        if 0 <= ny < rows and 0 <= nx < cols
                    ):
                        return True
                if d == "V" and width_v[(y, x)] == 1:
                    neighbors = [(y, x - 1), (y, x + 1)]
                    if all(
                        width_v.get((ny, nx), 0) != 1 and not is_corner_cell(ny, nx)
                        for ny, nx in neighbors
                        if 0 <= ny < rows and 0 <= nx < cols
                    ):
                        return True
            return False

        # it flags a local geometric change between neighboring critical cells (same orientation, different shape), used to mark entrance cells.
        # It returns True only when: 
        # the two cells share at least one critical direction ("H" or "V"),
        # in that shared direction, their corridor width differs (width_h or width_v)
        def check_perpendicular_entry(y, x, ny, nx):
            dirs = critical_directions(y, x)
            dirs_n = critical_directions(ny, nx)
            for d in dirs:
                if d in dirs_n:
                    if d == "H":
                        if width_h[(y, x)] != width_h[(ny, nx)]:
                            return True
                    elif d == "V":
                        if width_v[(y, x)] != width_v[(ny, nx)]:
                            return True
            return False

        entrance_cells = set()
        for y, x in critical_all:
            has_crit_nb = any(
                can_move(y, x, y + dy, x + dx) and (y + dy, x + dx) in critical_all
                for dy, dx in dirs8
            )
            has_free_nb = any(
                can_move(y, x, y + dy, x + dx) and (y + dy, x + dx) not in critical_all
                for dy, dx in dirs8
            )

            if has_crit_nb and has_free_nb:
                if not single_cell_isolated(y, x):
                    entrance_cells.add((y, x))
                continue

            for dy, dx in dirs4:
                ny, nx = y + dy, x + dx
                if not can_move(y, x, ny, nx):
                    continue
                if check_perpendicular_entry(y, x, ny, nx):
                    if not single_cell_isolated(y, x):
                        entrance_cells.add((y, x))
                    if not single_cell_isolated(ny, nx):
                        entrance_cells.add((ny, nx))

        # Compatibility between cells
        def same_area_compatible(y1, x1, y2, x2):
            d1 = set(critical_dirs.get((y1, x1), []))
            d2 = set(critical_dirs.get((y2, x2), []))
            if not d1 or not d2:
                return False

            common = d1 & d2
            for d in common:
                w1 = (
                    width_h.get((y1, x1), 0) if d == "H" else width_v.get((y1, x1), 0)
                )
                w2 = (
                    width_h.get((y2, x2), 0) if d == "H" else width_v.get((y2, x2), 0)
                )
                if w1 == w2:
                    return True

            return False

        # Build areas
        def build_areas(critical_all, entrance_cells):
            internal = critical_all - entrance_cells
            visited = {}
            areas = {}
            area_id = 0

            # Step 1: BFS on internal cells
            for seed in internal:
                if seed in visited:
                    continue
                component = set()
                q = deque([seed])
                while q:
                    cy, cx = q.popleft()
                    if (cy, cx) in visited:
                        continue
                    visited[(cy, cx)] = area_id
                    component.add((cy, cx))
                    for dy, dx in dirs8:
                        ny, nx = cy + dy, cx + dx
                        if (ny, nx) not in internal:
                            continue
                        if (ny, nx) in visited:
                            continue
                        if not can_move(cy, cx, ny, nx):
                            continue
                        if not same_area_compatible(cy, cx, ny, nx):
                            continue
                        q.append((ny, nx))
                areas[area_id] = {"cells": component, "entrances": set()}
                area_id += 1

            # Step 2: assign entrances to areas: Link entrance to all compatible neighboring areas
            entrance_to_areas = {}
            shared_borders = []

            for ey, ex in entrance_cells:
                neighboring = set()
                for dy, dx in dirs8:
                    nb = (ey + dy, ex + dx)
                    aid = visited.get(nb)
                    if aid is None:
                        continue
                    if same_area_compatible(ey, ex, nb[0], nb[1]):
                        neighboring.add(aid)
                entrance_to_areas[(ey, ex)] = neighboring
                for aid in neighboring:
                    areas[aid]["entrances"].add((ey, ex))
                if len(neighboring) == 2:
                    a1, a2 = tuple(neighboring)
                    shared_borders.append((ey, ex, a1, a2))

            # Step 3: isolated entrances → corridors
            isolated = {e for e, aids in entrance_to_areas.items() if not aids}
            iso_visited = set()
            for seed in isolated:
                if seed in iso_visited:
                    continue
                component = set()
                q = deque([seed])
                while q:
                    cy, cx = q.popleft()
                    if (cy, cx) in iso_visited:
                        continue
                    iso_visited.add((cy, cx))
                    component.add((cy, cx))
                    for dy, dx in dirs8:
                        ny, nx = cy + dy, cx + dx
                        if (ny, nx) not in isolated:
                            continue
                        if (ny, nx) in iso_visited:
                            continue
                        if not can_move(cy, cx, ny, nx):
                            continue
                        if not same_area_compatible(cy, cx, ny, nx):
                            continue
                        q.append((ny, nx))
                areas[area_id] = {"cells": component, "entrances": component.copy()}
                area_id += 1

            return areas, visited, shared_borders

        areas, cell_to_area, shared_borders = build_areas(critical_all, entrance_cells)

        # Merge areas by corner cells
        def merge_areas_on_corners(areas, cell_to_area):
            adjacency = {aid: set() for aid in areas}

            for aid, info in areas.items():
                all_cells = info["cells"] | info["entrances"]

                for (y, x) in all_cells:
                    if not is_corner_cell(y, x):
                        continue

                    for dy, dx in dirs4:
                        ny, nx = y + dy, x + dx

                        if not (0 <= ny < rows and 0 <= nx < cols):
                            continue

                        if binary[ny, nx] == 0:
                            continue

                        other_aid = cell_to_area.get((ny, nx))
                        if other_aid is None:
                            continue

                        if other_aid != aid:
                            adjacency[aid].add(other_aid)
                            adjacency[other_aid].add(aid)

            visited = set()
            new_areas = {}
            new_id = 0

            for aid in areas:
                if aid in visited:
                    continue

                stack = [aid]
                component = set()

                while stack:
                    cur = stack.pop()
                    if cur in visited:
                        continue
                    visited.add(cur)
                    component.add(cur)
                    stack.extend(adjacency[cur] - visited)

                merged_cells = set()
                merged_ent = set()

                for old_id in component:
                    merged_cells |= areas[old_id]["cells"]
                    merged_ent |= areas[old_id]["entrances"]

                new_areas[new_id] = {"cells": merged_cells, "entrances": merged_ent}
                new_id += 1

            new_cell_to_area = {}
            for aid, info in new_areas.items():
                for c in info["cells"] | info["entrances"]:
                    new_cell_to_area[c] = aid

            return new_areas, new_cell_to_area

        areas, cell_to_area = merge_areas_on_corners(areas, cell_to_area)

        # Merge areas by bridge cells
        changed = True
        while changed:
            changed = False

            for aid, info in list(areas.items()):
                all_cells = info["cells"] | info["entrances"]

                for (y, x) in list(all_cells):
                    neighbor_areas = set()

                    for dy, dx in dirs4:
                        ny, nx = y + dy, x + dx
                        if not (0 <= ny < rows and 0 <= nx < cols):
                            continue
                        if binary[ny, nx] == 0:
                            continue
                        other_aid = cell_to_area.get((ny, nx))
                        if other_aid is None or other_aid == aid:
                            continue
                        if same_area_compatible(y, x, ny, nx):
                            neighbor_areas.add(other_aid)

                    if is_corner_cell(y, x):
                        for dy, dx in dirs4:
                            ny, nx = y + dy, x + dx
                            if not (0 <= ny < rows and 0 <= nx < cols):
                                continue
                            if binary[ny, nx] == 0:
                                continue
                            other_aid = cell_to_area.get((ny, nx))
                            if other_aid is None or other_aid == aid:
                                continue
                            neighbor_areas.add(other_aid)

                    if neighbor_areas:
                        all_to_merge = neighbor_areas | {aid}
                        new_cells = set()
                        new_ent = set()
                        for old_id in all_to_merge:
                            new_cells |= areas[old_id]["cells"]
                            new_ent |= areas[old_id]["entrances"]
                            if old_id != aid:
                                del areas[old_id]
                        areas[aid]["cells"] = new_cells
                        areas[aid]["entrances"] = new_ent

                        changed = True
                        break

                if changed:
                    cell_to_area = {}
                    for a, inf in areas.items():
                        for c in inf["cells"] | inf["entrances"]:
                            cell_to_area[c] = a
                    break

        # Add single-cell areas to entrance_cells
        for aid, info in areas.items():
            if len(info["cells"]) == 1:
                single_cell = list(info["cells"])[0]
                entrance_cells.add(single_cell)
                # Move from internal cells to entrances
                info["cells"].remove(single_cell)
                info["entrances"].add(single_cell)

        # Claim orphaned free cells that are surrounded by a single area
        # A free cell belongs to an area if:
        # - All 8 neighbors are either walls or cells from exactly one area
        # - It has no free cell neighbors
        def claim_orphaned_free_cells(areas, cell_to_area):
            """
            Assigns free cells to their surrounding area if they are:
            - Not adjacent to any other free cells
            - Surrounded by only one area (not multiple areas)
            """
            all_critical = set(cell_to_area.keys())
            cells_assigned = 0
            
            # Only iterate over walkable cells not yet assigned
            for y in range(rows):
                for x in range(cols):
                    if binary[y, x] == 0 or (y, x) in all_critical:
                        continue  # Wall or already assigned
                    
                    # This is a free cell - check if it should be claimed
                    surrounding_areas = set()
                    has_free_neighbor = False
                    
                    # Early exit if any condition fails
                    for dy, dx in dirs8:
                        ny, nx = y + dy, x + dx
                        
                        if not (0 <= ny < rows and 0 <= nx < cols) or binary[ny, nx] == 0:
                            continue
                        if not can_move(y, x, ny, nx):
                            continue
                        
                        neighbor_aid = cell_to_area.get((ny, nx))
                        if neighbor_aid is None:
                            has_free_neighbor = True
                            break
                        surrounding_areas.add(neighbor_aid)
                    
                    # Claim immediately if conditions are met
                    if not has_free_neighbor and len(surrounding_areas) == 1:
                        aid = list(surrounding_areas)[0]
                        areas[aid]["cells"].add((y, x))
                        cell_to_area[(y, x)] = aid
                        all_critical.add((y, x))
                        cells_assigned += 1
            
            return areas, cell_to_area
        
        areas, cell_to_area = claim_orphaned_free_cells(areas, cell_to_area)

        # Validate and clean up entrance cells
        # Remove entrance cells that don't connect to free cells or other areas' entrances
        def validate_entrances(areas, cell_to_area):
            """
            Removes entrance cells that don't actually serve as bridges.
            An entrance cell should only exist if it's adjacent to:
            - Free cells (walkable cells not in any area), OR
            - Entrance cells of other areas
            """
            changed = True
            while changed:
                changed = False
                invalid_by_area = {}  # aid -> set of invalid entrances
                
                # Phase 1: Identify all invalid entrances
                for aid, info in list(areas.items()):
                    for ent in info["entrances"]:
                        ey, ex = ent
                        is_valid_entrance = False
                        
                        # Check all 8 neighbors (considering corner cut)
                        for dy, dx in dirs8:
                            ny, nx = ey + dy, ex + dx
                            
                            # Skip out of bounds and walls
                            if not (0 <= ny < rows and 0 <= nx < cols) or binary[ny, nx] == 0:
                                continue
                            
                            # Skip if movement is blocked by corner cut
                            if not can_move(ey, ex, ny, nx):
                                continue
                            
                            neighbor_aid = cell_to_area.get((ny, nx))
                            
                            # Valid if neighbor is free
                            if neighbor_aid is None:
                                is_valid_entrance = True
                                break
                            
                            # Valid if neighbor is entrance of another area
                            if neighbor_aid != aid:
                                other_info = areas.get(neighbor_aid)
                                if other_info and (ny, nx) in other_info["entrances"]:
                                    is_valid_entrance = True
                                    break
                        
                        if not is_valid_entrance:
                            if aid not in invalid_by_area:
                                invalid_by_area[aid] = set()
                            invalid_by_area[aid].add(ent)
                
                # Phase 2: Apply all changes at once
                if invalid_by_area:
                    changed = True
                    for aid, invalid_ents in invalid_by_area.items():
                        areas[aid]["entrances"] -= invalid_ents
                        areas[aid]["cells"] |= invalid_ents
                    
                    # Single mapping rebuild at end of iteration
                    cell_to_area = {}
                    for a, inf in areas.items():
                        for c in inf["cells"] | inf["entrances"]:
                            cell_to_area[c] = a
            
            return areas, cell_to_area
        
        areas, cell_to_area = validate_entrances(areas, cell_to_area)

        # Compute capacity (minimum passage width) for each area
        def compute_area_capacity(all_cells):
            """
            Computes area capacity as the minimum bottleneck width.
            """
            if not all_cells:
                return 0
            
            min_capacity = float('inf')
            for y, x in all_cells:
                # Get the minimum width at this cell (bottleneck in this cell)
                cell_width = min(
                    width_h.get((y, x), 1),
                    width_v.get((y, x), 1)
                )
                min_capacity = min(min_capacity, cell_width)
            
            return int(min_capacity) if min_capacity != float('inf') else 1

        # Create AreaManager
        area_manager = cls()
        for aid, info in areas.items():
            all_area_cells = info["cells"] | info["entrances"]
            capacity = compute_area_capacity(all_area_cells)
            area_manager.add_area(aid, info["cells"], info["entrances"], capacity)

        return {
            "area_manager": area_manager,
            "skeleton": sk_coords,
            "entrance_cells": entrance_cells,
            "shared_borders": shared_borders,
        }
