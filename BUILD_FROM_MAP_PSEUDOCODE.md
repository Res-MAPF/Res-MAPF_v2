# BUILD_FROM_MAP Algorithm Pseudocode

## Overview
This algorithm identifies and organizes critical areas (bottlenecks) in a grid map by analyzing passage widths, connectivity patterns, and spatial constraints. It produces an AreaManager structure for efficient area lookups and neighbor queries.

The implementation decomposes the algorithm into major computational phases, each handled by dedicated procedures for maintainability and clarity.

---

## Algorithm 1: BuildFromMap

**Algorithm 1:** `BuildFromMap(M, DistThreshold = 4)`
- **Input:** Grid map M (with '.' = walkable, '@' = wall), distance threshold DistThreshold  
- **Output:** AreaManager Γ, skeleton coordinates S, entrance cells Cent, shared borders B

```
1   BinaryGrid, Skeleton ← ComputeSkeletonAndMetrics(M)
2   WidthH, WidthV, CriticalCells ← ExpandCriticalRegion(BinaryGrid, Skeleton, DistThreshold)
3   CriticalDirs ← ComputeCriticalDirections(CriticalCells, WidthH, WidthV, DistThreshold)
4   EntranceCells ← IdentifyEntrances(CriticalCells, CriticalDirs, BinaryGrid)
5   
6   Areas, CellToArea, SharedBorders ← BuildAreas(CriticalCells, EntranceCells, BinaryGrid, CriticalDirs, WidthH, WidthV)
7   Areas, CellToArea ← MergeAreasByCorners(Areas, CellToArea, BinaryGrid)
8   Areas, CellToArea ← MergeAreasByBridges(Areas, CellToArea, BinaryGrid, WidthH, WidthV, CriticalDirs)
9   Areas ← FinalizeSingleCellAreas(Areas)
10  Areas, CellToArea ← ClaimOrphanedFreeCells(Areas, CellToArea, BinaryGrid)
11  Areas, CellToArea ← ValidateEntrances(Areas, CellToArea, BinaryGrid)
12  
13  AreaMgr ← AreaManager()
14  for each (aid, ainfo) ∈ Areas do
15      AreaMgr.AddArea(aid, ainfo.cells, ainfo.entrances)
16  end for
17  
18  return (AreaMgr, Skeleton, EntranceCells, SharedBorders)
```

---

## Major Procedures

### Procedure 1: ComputeSkeletonAndMetrics

**Procedure 1:** `ComputeSkeletonAndMetrics(M)`

Converts the grid to binary format and extracts the topological skeleton.

```
1   rows ← |M|; cols ← |M[0]|
2   BinaryGrid ← [[1 if M[i][j]='.' else 0 for j in range(cols)] for i in range(rows)]
3   Skeleton ← ExtractSkeleton(BinaryGrid)   // Topological centerline
4   return (BinaryGrid, Skeleton)
```

### Procedure 2: ExpandCriticalRegion

**Procedure 2:** `ExpandCriticalRegion(BinaryGrid, Skeleton, DistThreshold)`

Identifies critical cells (bottlenecks) on the skeleton and expands the region to include adjacent corner cells.

```
1   WidthH ← ∅; WidthV ← ∅
2   
3   // Compute distance metrics for all walkable cells
4   for each v ∈ BinaryGrid where BinaryGrid[v]=1 do
5       WidthH[v] ← DistToWall(v, 0, ±1, BinaryGrid) + 1     // Horizontal width
6       WidthV[v] ← DistToWall(v, ±1, 0, BinaryGrid) + 1     // Vertical width
7   end for
8   
9   // Identify critical cells on skeleton
10  CriticalSeed ← {v ∈ Skeleton | WidthH[v] < DistThreshold ∨ WidthV[v] < DistThreshold}
11  
12  // DFS expansion to include corner cells (uses LIFO stack semantics)
13  CriticalCells ← CriticalSeed; Queue ← CriticalSeed
14  while Queue ≠ ∅ do
15      v ← Queue.pop()  // LIFO: pop from end for depth-first exploration
16      for each nbr ∈ Neighbors8(v) do
17          if nbr ∈ CriticalCells ∨ ¬CanMove(v, nbr, BinaryGrid) then continue end if
18          if WidthH[nbr] < DistThreshold ∨ WidthV[nbr] < DistThreshold ∨ IsCornerCell(nbr, BinaryGrid) then
19              CriticalCells ← CriticalCells ∪ {nbr}
20              Queue.append(nbr)
21          end if
22      end for
23  end while
24  
25  return (WidthH, WidthV, CriticalCells)
```

### Procedure 3: ComputeCriticalDirections

**Procedure 3:** `ComputeCriticalDirections(CriticalCells, WidthH, WidthV, DistThreshold)`

Determines the orientation of each critical cell (H=horizontal bottleneck, V=vertical bottleneck, or both).

```
1   CriticalDirs ← ∅
2   for each v ∈ CriticalCells do
3       dirs ← []
4       if WidthH[v] < DistThreshold then dirs ← dirs ⊕ ["H"] end if
5       if WidthV[v] < DistThreshold then dirs ← dirs ⊕ ["V"] end if
6       CriticalDirs[v] ← dirs
7   end for
8   return CriticalDirs
```

### Procedure 4: IdentifyEntrances

**Procedure 4:** `IdentifyEntrances(CriticalCells, CriticalDirs, BinaryGrid)`

Marks entrance cells: boundary cells between critical and free space, or cells with significant orientation changes.

```
1   EntranceCells ← ∅
2   for each v ∈ CriticalCells do
3       has_crit ← ∃nbr ∈ Neighbors8(v) : nbr ∈ CriticalCells ∧ CanMove(v, nbr, BinaryGrid)
4       has_free ← ∃nbr ∈ Neighbors8(v) : nbr ∉ CriticalCells ∧ CanMove(v, nbr, BinaryGrid)
5       
6       if has_crit ∧ has_free ∧ ¬IsSingleCellIsolated(v, CriticalDirs) then
7           EntranceCells ← EntranceCells ∪ {v}
8           continue
9       end if
10      
11      // Check perpendicular orientation changes
12      for each nbr ∈ Neighbors4(v) do
13          if ¬CanMove(v, nbr, BinaryGrid) then continue end if
14          if CheckPerpendicularity(v, nbr, CriticalDirs) then
15              if ¬IsSingleCellIsolated(v, CriticalDirs) then
16                  EntranceCells ← EntranceCells ∪ {v}
17              end if
18          end if
19      end for
20  end for
21  return EntranceCells
```

### Procedure 5: BuildAreas

**Procedure 5:** `BuildAreas(CriticalCells, EntranceCells, BinaryGrid, CriticalDirs, WidthH, WidthV)`

Constructs initial areas from internal cells using BFS, links entrances to areas, and creates corridor areas from isolated entrances.

```
1   InternalCells ← CriticalCells \ EntranceCells
2   CellToArea ← ∅; Areas ← ∅; areaId ← 0; SharedBorders ← ∅; EntranceToAreas ← ∅
3   
4   // Phase 1: BFS on internal cells
4   for each seed ∈ InternalCells where seed ∉ CellToArea do
5       component ← ∅; Queue ← [seed]  // FIFO queue for BFS
6       while Queue ≠ ∅ do
7           v ← Queue.popleft()  // FIFO - Breadth-First Search
8           if v ∈ CellToArea then continue end if
9           CellToArea[v] ← areaId; component ← component ∪ {v}
10          for each nbr ∈ Neighbors8(v) do
11              if nbr ∉ InternalCells ∨ nbr ∈ CellToArea then continue end if
12              if ¬CanMove(v, nbr, BinaryGrid) ∨ ¬Compatible(v, nbr, CriticalDirs, WidthH, WidthV) then continue end if
13              Queue.append(nbr)
14          end for
15      end while
16      Areas[areaId] ← {cells: component, entrances: ∅}
17      areaId ← areaId + 1
18  end for
19  
20  // Phase 2: Link entrances to compatible adjacent areas
21  for each ent ∈ EntranceCells do
22      AdjacentAreas ← ∅
23      for each nbr ∈ Neighbors8(ent) do
24          nbr_areaId ← CellToArea[nbr]
25          if nbr_areaId ≠ null ∧ Compatible(ent, nbr, CriticalDirs, WidthH, WidthV) then
26              AdjacentAreas ← AdjacentAreas ∪ {nbr_areaId}
27          end if
28      end for
29      EntranceToAreas[ent] ← AdjacentAreas
30      for each aid ∈ AdjacentAreas do
31          Areas[aid].entrances ← Areas[aid].entrances ∪ {ent}
32      end for
33      if |AdjacentAreas| = 2 then
30          SharedBorders ← SharedBorders ∪ {(ent, AdjacentAreas[0], AdjacentAreas[1])}
31      end if
32  end for
33  
34  // Phase 3: Create corridors from isolated entrances
35  IsolatedEntrances ← {e ∈ EntranceCells | EntranceToAreas[e] = ∅}
36  IsolatedVisited ← ∅
37  for each seed ∈ IsolatedEntrances where seed ∉ IsolatedVisited do
38      corridor ← ∅; Queue ← [seed]  // FIFO queue for BFS
39      while Queue ≠ ∅ do
40          v ← Queue.popleft()  // FIFO - Breadth-First Search
41          if v ∈ IsolatedVisited then continue end if
42          IsolatedVisited ← IsolatedVisited ∪ {v}; corridor ← corridor ∪ {v}
43          for each nbr ∈ Neighbors8(v) do
44              if nbr ∉ IsolatedEntrances ∨ nbr ∈ IsolatedVisited then continue end if
45              if ¬CanMove(v, nbr, BinaryGrid) ∨ ¬Compatible(v, nbr, CriticalDirs, WidthH, WidthV) then continue end if
46              Queue.append(nbr)
47          end for
48      end while
49      Areas[areaId] ← {cells: corridor, entrances: corridor}
50      areaId ← areaId + 1
51  end for
52  
53  return (Areas, CellToArea, SharedBorders)
```

### Procedure 6: MergeAreasByCorners

**Procedure 6:** `MergeAreasByCorners(Areas, CellToArea, BinaryGrid)`

Merges areas that are connected via corner cells (4-neighbor connected components of corners).

```
1   // Build corner-based adjacency graph
2   AreaAdjacency ← {aid → ∅ | aid ∈ Keys(Areas)}
3   for each (aid, ainfo) ∈ Areas do
4       AllCells ← ainfo.cells ∪ ainfo.entrances
5       for each v ∈ AllCells do
6           if ¬IsCornerCell(v, BinaryGrid) then continue end if
7           for each nbr ∈ Neighbors4(v) do
8               if ¬InBounds(nbr) ∨ BinaryGrid[nbr]=0 then continue end if
9               nbr_areaId ← CellToArea[nbr]
10              if nbr_areaId ≠ null ∧ nbr_areaId ≠ aid then
11                  AreaAdjacency[aid] ← AreaAdjacency[aid] ∪ {nbr_areaId}
12                  AreaAdjacency[nbr_areaId] ← AreaAdjacency[nbr_areaId] ∪ {aid}
13              end if
14          end for
15      end for
16  end for
17  
18  // DFS-based component merging
19  VisitedComponents ← ∅; MergedAreas ← ∅; newAreaId ← 0
20  for each aid ∈ Keys(Areas) where aid ∉ VisitedComponents do
21      stack ← [aid]; component ← ∅
22      while stack ≠ ∅ do
23          cur ← stack.pop()
24          if cur ∈ VisitedComponents then continue end if
25          VisitedComponents ← VisitedComponents ∪ {cur}; component ← component ∪ {cur}
26          stack.extend(AreaAdjacency[cur] \ VisitedComponents)
27      end while
28      mergedCells ← ∪{Areas[a].cells | a ∈ component}
29      mergedEnts ← ∪{Areas[a].entrances | a ∈ component}
30      MergedAreas[newAreaId] ← {cells: mergedCells, entrances: mergedEnts}
31      newAreaId ← newAreaId + 1
32  end for
33  
34  Areas ← MergedAreas; CellToArea ← MakeMapping(Areas)
35  return (Areas, CellToArea)
```

### Procedure 7: MergeAreasByBridges

**Procedure 7:** `MergeAreasByBridges(Areas, CellToArea, BinaryGrid, WidthH, WidthV, CriticalDirs)`

Iteratively merges areas connected via bridge cells (cells where compatible neighbors from different areas meet). Corner cells always trigger merging.

```
1   changed ← true
2   while changed do
3       changed ← false
4       for each (aid, ainfo) ∈ Areas do
5           AllCells ← ainfo.cells ∪ ainfo.entrances
6           
7           for each v ∈ AllCells do
8               NeighborAreas ← ∅
9               // Regular compatibility-based merging
10              for each nbr ∈ Neighbors4(v) do
11                  if ¬InBounds(nbr) ∨ BinaryGrid[nbr]=0 then continue end if
12                  nbr_areaId ← CellToArea[nbr]
13                  if nbr_areaId ≠ null ∧ nbr_areaId ≠ aid then
14                      if Compatible(v, nbr, CriticalDirs, WidthH, WidthV) then
15                          NeighborAreas ← NeighborAreas ∪ {nbr_areaId}
16                      end if
17                  end if
18              end for
19              
20              // Corner cells always trigger merging (no compatibility check)
21              if IsCornerCell(v, BinaryGrid) then
22                  for each nbr ∈ Neighbors4(v) do
23                      if ¬InBounds(nbr) ∨ BinaryGrid[nbr]=0 then continue end if
24                      nbr_areaId ← CellToArea[nbr]
25                      if nbr_areaId ≠ null ∧ nbr_areaId ≠ aid then
26                          NeighborAreas ← NeighborAreas ∪ {nbr_areaId}
27                      end if
28                  end for
29              end if
30          end for
31          
32          // Perform merge if compatible neighbors found
33          if NeighborAreas ≠ ∅ then
34              AreasToMerge ← NeighborAreas ∪ {aid}
35              mergedCells ← ∪{Areas[a].cells | a ∈ AreasToMerge}
36              mergedEnts ← ∪{Areas[a].entrances | a ∈ AreasToMerge}
37              Areas[aid] ← {cells: mergedCells, entrances: mergedEnts}
38              for each a ∈ (AreasToMerge \ {aid}) do Delete(Areas, a) end for
39              changed ← true
40              break
41          end if
42      end for
43      
44      if changed then
45          CellToArea ← MakeMapping(Areas)
46      end if
47  end while
48  return (Areas, CellToArea)
```

### Procedure 8: FinalizeSingleCellAreas

**Procedure 8:** `FinalizeSingleCellAreas(Areas)`

Reclassifies single-cell areas as entrances (since they are too small to be meaningful internal regions).

```
1   for each (aid, ainfo) ∈ Areas do
2       if |ainfo.cells| = 1 then
3           v ← ExtractSingle(ainfo.cells)
4           ainfo.cells ← ∅
5           ainfo.entrances ← ainfo.entrances ∪ {v}
6       end if
7   end for
8   return Areas
```

### Procedure 9: ClaimOrphanedFreeCells

**Procedure 9:** `ClaimOrphanedFreeCells(Areas, CellToArea, BinaryGrid)`

Assigns free cells (walkable cells not belonging to any area) to their surrounding area if they meet specific isolation criteria.

A free cell is claimed by an area if:
- It has no free cell neighbors (not adjacent to other unassigned cells)
- All reachable neighbors belong to exactly one area (ensuring it's surrounded by a single area, not multiple)

```
1   AllCritical ← Keys(CellToArea)
2   CellsAssigned ← 0
3   
4   for each (y, x) where BinaryGrid[y,x]=1 do
5       if BinaryGrid[y,x]=0 ∨ (y,x) ∈ AllCritical then continue end if  // Wall or already assigned
6       
7       SurroundingAreas ← ∅
8       HasFreeNeighbor ← false
9       
10      for each nbr ∈ Neighbors8(y, x) do
11          if ¬(InBounds(nbr) ∧ BinaryGrid[nbr]=1) then continue end if
12          if ¬CanMove(y, x, nbr, BinaryGrid) then continue end if
13          
14          nbrAreaId ← CellToArea[nbr]
15          if nbrAreaId = null then
16              HasFreeNeighbor ← true
17              break  // Early exit: free neighbor detected
18          else
19              SurroundingAreas ← SurroundingAreas ∪ {nbrAreaId}
20          end if
21      end for
22      
23      // Claim immediately if conditions met (no intermediate list)
24      if ¬HasFreeNeighbor ∧ |SurroundingAreas| = 1 then
25          claimAid ← ExtractSingle(SurroundingAreas)
26          Areas[claimAid].cells ← Areas[claimAid].cells ∪ {(y, x)}
27          CellToArea[(y, x)] ← claimAid
27          AllCritical ← AllCritical ∪ {(y, x)}
28          CellsAssigned ← CellsAssigned + 1
29      end if
30  end for
31  
32  return (Areas, CellToArea)
```

### Procedure 10: ValidateEntrances

**Procedure 10:** `ValidateEntrances(Areas, CellToArea, BinaryGrid)`

Removes entrance cells that don't actually serve as bridges. An entrance cell should be adjacent to at least one of:
- A free cell (walkable cell not in any area), OR
- An entrance cell of another area

Entrance cells that fail these criteria are reclassified as internal cells.

```
1   changed ← true
2   while changed do
3       changed ← false
4       InvalidByArea ← ∅  // aid → set of invalid entrances
5       
6       // Phase 1: Identify all invalid entrances across all areas
7       for each (aid, ainfo) ∈ Areas do
8           for each ent ∈ ainfo.entrances do
9               ey, ex ← ent
10              IsValidEntry ← false
11              
12              for each nbr ∈ Neighbors8(ent) do
13                  ny, nx ← nbr
14                  
15                  // Skip out of bounds and walls
16                  if ¬(InBounds(nbr) ∧ BinaryGrid[nbr]=1) then continue end if
17                  
18                  // Skip if movement is blocked by corner cut
19                  if ¬CanMove(ey, ex, ny, nx) then continue end if
20                  
21                  nbrAreaId ← CellToArea[nbr]
22                  
23                  // Valid if neighbor is a free cell
24                  if nbrAreaId = null then
25                      IsValidEntry ← true
26                      break
27                  end if
28                  
29                  // Valid if neighbor is entrance of another area
30                  if nbrAreaId ≠ aid then
31                      otherArea ← Areas[nbrAreaId]
32                      if otherArea ≠ null ∧ nbr ∈ otherArea.entrances then
33                          IsValidEntry ← true
34                          break
35                      end if
36                  end if
37              end for
38              
39              if ¬IsValidEntry then
40                  if aid ∉ Keys(InvalidByArea) then
40                      InvalidByArea[aid] ← ∅
41                  end if
42                  InvalidByArea[aid] ← InvalidByArea[aid] ∪ {ent}
43              end if
44          end for
45      end for
46      
47      // Phase 2: Apply all changes at once with single mapping rebuild
48      if InvalidByArea ≠ ∅ then
49          changed ← true
50          
51          for each (aid, invalidEnts) ∈ InvalidByArea do
52              Areas[aid].entrances ← Areas[aid].entrances \ invalidEnts
53              Areas[aid].cells ← Areas[aid].cells ∪ invalidEnts
54          end for
55          
56          // Single mapping rebuild at end of iteration (not per-area)
57          CellToArea ← ∅
58          for each (a, ainfo) ∈ Areas do
59              for each c ∈ (ainfo.cells ∪ ainfo.entrances) do
60                  CellToArea[c] ← a
61              end for
62          end for
63      end if
64  end while
65  
66  return (Areas, CellToArea)
```

---

## Utility Procedures

### Procedure U1: CanMove

**Procedure U1:** `CanMove(y, x, ny, nx, BinaryGrid)`

Checks if movement from (y,x) to (ny,nx) is valid (in-bounds, walkable, and diagonal moves are not blocked).

```
1   if ¬InBounds(ny, nx) ∨ BinaryGrid[ny, nx]=0 then return false end if
2   dy ← ny - y; dx ← nx - x
3   if (dy, dx) ∈ DiagonalDirs then
4       if BinaryGrid[y+dy, x]=0 ∨ BinaryGrid[y, x+dx]=0 then return false end if
5   end if
6   return true
```

### Procedure U2: DistToWall

**Procedure U2:** `DistToWall(y, x, dy, dx, BinaryGrid)`

Computes distance from (y,x) to wall in direction (dy,dx).

```
1   d ← 0; cy ← y; cx ← x
2   while true do
3       ny ← cy + dy; nx ← cx + dx
4       if ¬InBounds(ny, nx) ∨ BinaryGrid[ny, nx]=0 then return d end if
5       if (dy, dx) ∈ DiagonalDirs then
6           if BinaryGrid[cy+dy, cx]=0 ∨ BinaryGrid[cy, cx+dx]=0 then return d end if
7       end if
8       cy ← ny; cx ← nx; d ← d + 1
9   end while
```

### Procedure U3: IsCornerCell

**Procedure U3:** `IsCornerCell(y, x, BinaryGrid)`

Detects if (y,x) is a corner cell (has walls in two perpendicular cardinal directions).

```
1   perp_pairs ← [((0,1), (1,0)), ((0,1), (-1,0)), ((0,-1), (1,0)), ((0,-1), (-1,0))]
2   for each ((dy1, dx1), (dy2, dx2)) ∈ perp_pairs do
3       b1 ← ¬InBounds(y+dy1, x+dx1) ∨ BinaryGrid[y+dy1, x+dx1]=0
4       b2 ← ¬InBounds(y+dy2, x+dx2) ∨ BinaryGrid[y+dy2, x+dx2]=0
5       if b1 ∧ b2 then return true end if
6   end for
7   return false
```

### Procedure U4: Compatible

**Procedure U4:** `Compatible(v₁, v₂, CriticalDirs, WidthH, WidthV)`

Checks if two cells are compatible for area membership (share critical direction with matching width).

```
1   d₁ ← CriticalDirs[v₁]; d₂ ← CriticalDirs[v₂]
2   if d₁=∅ ∨ d₂=∅ then return false end if
3   common ← d₁ ∩ d₂
4   for each d ∈ common do
5       w_d¹ ← (d="H") ? WidthH[v₁] : WidthV[v₁]
6       w_d² ← (d="H") ? WidthH[v₂] : WidthV[v₂]
7       if w_d¹ = w_d² then return true end if
8   end for
9   return false
```

### Procedure U5: MakeMapping

**Procedure U5:** `MakeMapping(Areas)`

Rebuilds the cell-to-area lookup table from current area definitions.

```
1   CellToArea ← ∅
2   for each (aid, ainfo) ∈ Areas do
3       allCells ← ainfo.cells ∪ ainfo.entrances
4       for each v ∈ allCells do
5           CellToArea[v] ← aid
6       end for
7   end for
8   return CellToArea
```

### Procedure U6: IsSingleCellIsolated

**Procedure U6:** `IsSingleCellIsolated(v, CriticalDirs, WidthH, WidthV)`

Detects if (v) is a lone narrow point not part of a wider narrow strip.

```
1   dirs ← CriticalDirs[v]
2   for each d ∈ dirs do
3       if d="H" ∧ WidthH[v]=1 then
4           neighbors ← [(v.y-1,v.x), (v.y+1,v.x)]
5           if all(WidthH[nbr]≠1 ∧ ¬IsCornerCell(nbr) for nbr ∈ neighbors, InBounds(nbr)) then
6               return true
7           end if
8       end if
9       if d="V" ∧ WidthV[v]=1 then
10          neighbors ← [(v.y,v.x-1), (v.y,v.x+1)]
11          if all(WidthV[nbr]≠1 ∧ ¬IsCornerCell(nbr) for nbr ∈ neighbors, InBounds(nbr)) then
12              return true
13          end if
14      end if
15  end for
16  return false
```

### Procedure U7: CheckPerpendicularity

**Procedure U7:** `CheckPerpendicularity(v₁, v₂, CriticalDirs, WidthH, WidthV)`

Detects orientation change between adjacent critical cells (same direction, different width).

```
1   d1 ← CriticalDirs[v₁]; d2 ← CriticalDirs[v₂]
2   for each d ∈ d1 do
3       if d ∉ d2 then continue end if
4       if d="H" then
5           if WidthH[v₁] ≠ WidthH[v₂] then return true end if
6       else // d="V"
7           if WidthV[v₁] ≠ WidthV[v₂] then return true end if
8       end if
9   end for
10  return false
```

---

## Variable Naming Convention

The pseudocode uses the following naming scheme for clarity and consistency:

- **Grid-related**: `BinaryGrid`, `Skeleton` — represent grid information
- **Width metrics**: `WidthH`, `WidthV` — passage width measurements  
- **Cell sets**: `CriticalCells`, `InternalCells`, `EntranceCells`, `IsolatedEntrances` — descriptive set names
- **Mappings**: `CriticalDirs`, `CellToArea` — cell-to-property and cell-to-area mappings
- **Areas**: `Areas`, `AreaAdjacency`, `NeighborAreas`, `AreasToMerge` — area structures and relationships
- **Collections**: `Queue`, `Stack`, `component`, `corridor`, `merged*` — temporary working collections
- **Unique values**: `DistThreshold`, `areaId`, `newAreaId`, `SharedBorders` — scalar or unique identifiers

---

## Notation Reference

| Symbol | Meaning |
|--------|---------|
| M | Grid map with '.' (walkable) and '@' (wall) cells |
| BinaryGrid | Binary grid (1=walkable, 0=wall) |
| Skeleton | Skeleton coordinates (topological centerline) |
| DistThreshold | Distance threshold for critical cell identification |
| WidthH[v], WidthV[v] | Horizontal and vertical passage widths at cell v |
| CriticalCells | Set of all critical cells (bottleneck region) |
| CriticalDirs | Map from cell v to critical directions ["H", "V", or both] |
| EntranceCells | Set of entrance/exit cells (boundaries) |
| InternalCells | Set of internal cells (critical but not entrance) |
| IsolatedEntrances | Set of isolated entrance cells (without adjacent internal areas) |
| Areas | Map from area_id to {cells, entrances} pairs |
| AreaMgr | AreaManager data structure |
| CellToArea | Map from cell v to containing area_id |
| AreaAdjacency | Adjacency graph for area merging |
| SharedBorders | Set of shared borders (cells connecting exactly 2 areas) |
| Neighbors8, Neighbors4 | 8-connected and 4-connected neighbor sets |
| Dirs8, Dirs4 | 8-connected and 4-connected neighbor directions |
| DiagonalDirs | Set of diagonal directions: {(±1,±1)} |
| ∪, ∩, \ | Set union, intersection, difference |
| ⊕ | List append operation |
| ∃, ∀, ¬ | Existential, universal quantifiers, negation |
| → | Function mapping arrow |
| ≠, = | Inequality, equality |
| InBounds | Checks if cell is within grid boundaries |

---

## Complexity Analysis

- **Grid preprocessing** (ComputeSkeletonAndMetrics + ExpandCriticalRegion): O(rows × cols × max(rows, cols))
  - Skeleton extraction: O(rows × cols)
  - Distance metrics: O(rows × cols × max(rows, cols))
  - Critical region expansion: O(|CriticalCells|)
  
- **Entrance identification** (IdentifyEntrances): O(|CriticalCells|)

- **Area construction** (BuildAreas phases 1-3): O(|CriticalCells|) total with all BFS traversals

- **Merging operations** (MergeAreasByCorners + MergeAreasByBridges): O(|Areas|²) worst case, typically much faster

- **Overall**: O(rows × cols × max(rows, cols)) dominated by distance metrics computation

---

## Organizational Structure

The algorithm decomposes into clearly separated phases:

1. **Metric Computation** (Procedures 1-2): Grid analysis and distance metrics
2. **Critical Cell Identification** (Procedures 2-3): Classification of bottleneck regions
3. **Entrance Detection** (Procedure 4): Boundary cell identification
4. **Area Construction** (Procedure 5): Initial area formation via BFS
5. **Topological Merging** (Procedure 6): Corner-based component merging
6. **Spatial Merging** (Procedure 7): Bridge-based iterative refinement
7. **Finalization** (Procedure 8): Single-cell area reclassification

Each major procedure represents a distinct computational phase that directly corresponds to modular sections in the implementation.

---

## Output Description

Returns tuple (Γ, S, Cent, B):
- **Γ**: AreaManager with O(1) lookups for area membership, neighbor queries, entrance access
- **S**: Skeleton coordinates used for critical cell seeding
- **Cent**: All entrance/exit cells enabling boundary-aware path planning
- **B**: Shared borders list (cells between exactly 2 areas) identifying critical junctions
