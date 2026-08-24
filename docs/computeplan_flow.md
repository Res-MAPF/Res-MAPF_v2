# Flusso di esecuzione — `computeplan.py`

Documento di riferimento per il file `src/domain/solver/computeplan.py`.
Segue la catena di chiamate a partire dall'entry point `compute_plan_cbs`.

---

## Strutture dati principali

### `CBSNode`
Nodo dell'albero di ricerca ad alto livello (CBS).

| Campo | Tipo | Descrizione |
|---|---|---|
| `constraints` | `set` | Vincoli hard assegnati finora (agente, vertice/arco, tempo, tipo) |
| `solution` | `list[list[pos]]` | Un percorso per agente |
| `cost` | `int` | Somma delle lunghezze dei percorsi − 1 |

Ordinamento: `cost` crescente (usato da `heapq`).

---

### `SIPPSNode`
Nodo della ricerca a basso livello (SIPPS).

| Campo | Tipo | Descrizione |
|---|---|---|
| `v` | `tuple(row, col)` | Vertice corrente |
| `low`, `high` | `int` | Estremi dell'intervallo sicuro corrente |
| `interval_id` | `int` | Indice dell'intervallo in `T_table[v]` |
| `g` | `int` | Tempo di arrivo reale in `v` |
| `h` | `int` | Stima euristica al goal |
| `f` | `int` | `g + h` |
| `c_conflicts` | `int` | Conflitti soft cumulati (vertice + arco) |
| `c_entrance_penalty` | `float` | Penalità area critica cumulata |
| `is_goal` | `bool` | Il nodo rappresenta il goal sintetico |
| `parent` | `SIPPSNode` | Nodo predecessore (per `extract_path`) |

**Ordinamento heap**: `(c_conflicts, c_entrance_penalty, f)` — lessicografico.  
**Identità**: `(v, interval_id, is_goal)` — usata per dominanza e lookup O(1).

---

### `SafeIntervalCache`
Cache incrementale della `T_table`, salvata direttamente sull'oggetto grafo (`graph._safe_interval_cache`).

| Campo | Tipo | Descrizione |
|---|---|---|
| `cached_T` | `dict[vertex → list[(lo,hi)]]` | Intervalli già calcolati |
| `cached_hard_by_vertex` | `dict[vertex → set[int]]` | Vincoli hard per vertice |
| `cached_soft_by_vertex` | `dict[vertex → set[int]]` | Vincoli soft per vertice |

Viene aggiornata solo sui vertici in cui i vincoli sono cambiati rispetto alla chiamata precedente.

---

## 1. `compute_plan_cbs` — Entry point CBS

```
compute_plan_cbs(starts, goals, failed_actions, states_down, graph, h_maps,
                 os_entrances=None, stop_event=None)
→ (pi, tau) | (None, None)
```

**Scopo**: orchestrare la ricerca CBS (Conflict-Based Search) completa.

### Passi

1. **Guard iniziale**: se `tuple(starts) ∈ states_down`, ritorna `(None, None)` immediatamente.
2. **Inizializzazione cache**: se `graph._safe_interval_cache` non esiste, crea un `SafeIntervalCache()`.
3. **Root node**: crea `CBSNode()` con `constraints = ∅`.
4. **Soluzione root**: chiama `root.compute_low_level_solution(...)` per tutti gli agenti. Se fallisce → `(None, None)`.
5. **Push root** sull'`open_list` (min-heap su `cost`).

### Loop principale CBS

```
while open_list:
    if stop_event.is_set(): return None, None

    node = heapq.heappop(open_list)
    pi, tau = build_solution(node)

    if tau_key in closed_tau_set: continue   ← deduplication
    closed_tau_set.add(tau_key)

    conflict = detect_conflict(node.solution)
```

**Caso A — nessun conflitto**:
- Scansiona `tau` cercando uno stato "down" (`states_down`).
- Se trovato: per ogni agente nello stato down crea un `CBSNode` figlio con un vincolo hard `(agent, pos, t, "vertex")` e lo spinge nell'open list.
- Se non trovato: **ritorna `(pi, tau)`** → soluzione trovata.

**Caso B — conflitto di vertice** `(ai, aj, vertex, timestep, "vertex")`:
- Crea due figli:
  - `child_ai`: aggiunge `(ai, vertex, timestep, "vertex")` ai vincoli.
  - `child_aj`: aggiunge `(aj, vertex, timestep, "vertex")` ai vincoli.
- Per ciascuno chiama `compute_low_level_solution` (solo per l'agente vincolato, riusando i percorsi degli altri).
- Se la soluzione è valida e `tau` non è in `closed_tau_set`, spinge il figlio.

**Caso C — conflitto di arco** `(ai, aj, (u,v), timestep, "edge")`:
- Crea due figli:
  - `child_ai`: vincolo `(ai, (u,v), timestep, "edge")`.
  - `child_aj`: vincolo `(aj, (v,u), timestep, "edge")` (arco inverso).
- Stessa logica di push.

Se l'open list si svuota senza trovare una soluzione → `(None, None)`.

---

## 2. `CBSNode.compute_low_level_solution`

```
compute_low_level_solution(starts, goals, original_graph, failed_actions, h_maps,
                           parent_solution=None, agent_to_compute=None,
                           os_entrances=None, stop_event=None)
→ bool
```

**Ottimizzazione single-agent**: se `agent_to_compute` è specificato, ricicla tutti i percorsi dal `parent_solution` eccetto quello dell'agente da ricalcolare, evitando di rifare la ricerca SIPPS per tutti.

### Passi

1. Determina `agents_to_compute` (tutti o solo `[agent_to_compute]`).
2. Se ottimizzazione attiva: `paths = [parent_solution[j] for j != agent_to_compute]`.
3. Per ogni agente `i`:
   - chiama `low_level_search_cbs(i, start, goal, self.constraints, ...)`.
   - Se `path is None` → ritorna `False`.
   - Appende `path` a `paths` (gli agenti successivi vedono i percorsi di quelli precedenti).
4. **Merge finale**:
   - Ottimizzazione attiva: `self.solution = list(parent_solution)` poi sovrascrive `solution[agent_to_compute]`.
   - Caso normale: `self.solution = paths`.
5. `self.cost = sum(len(p) - 1 for p in self.solution)`.
6. Ritorna `True`.

---

## 3. `low_level_search_cbs` — Setup SIPPS per singolo agente

```
low_level_search_cbs(agent_id, start, goal, constraints, original_graph,
                     failed_actions, heuristic_map, max_time=10000,
                     paths=None, os_entrances=None, goals=None, stop_event=None)
→ (path, cost) | (None, inf)
```

### 3.1 Popolamento vincoli hard

Scansiona `constraints` filtrando solo quelli per `agent_id`:
- `"vertex"` → aggiunge `(pos, t)` a `Oh_vertex`
- `"edge"` → aggiunge `((u,v), t)` a `Oh_edge`

`Oh_target` rimane vuoto in questa implementazione (usato come placeholder per future estensioni).

### 3.2 Popolamento vincoli soft

Per ogni percorso già calcolato (altri agenti):
- Ogni posizione `(v, t)` → `Os_vertex.add((v, t))`
- Ogni arco `(path[t], path[t+1])` al tempo `t` → `Os_edge.add(((a,b), t))`

### 3.3 Occupancy table + split strutturali T_table

```python
occupancy_table = build_occupancy_table(paths, area_manager, goal, goals)
```

Per ogni area con capacità satura ad un certo timestep `t_occ`:
- Per ogni vertice di ingresso `entrance_v` dell'area (escluso il goal dell'agente corrente):
  - `Os_vertex.add((entrance_v, t_occ))`

**Effetto**: la `T_table` viene spezzata su quei timestep → SIPPS produce nodi distinti per "arriva prima che l'area sia piena" vs "arriva quando è piena", e `compute_c_value` li ordina tramite la penalità di occupazione.

### 3.4 Rimozione archi per `failed_actions`

Converte le azioni fallite dell'agente in archi `(cell, to_cell)` e li inserisce in `removed_edges`. Gli archi vengono esclusi logicamente da `get_valid_successors`, senza modificare il grafo.

### 3.5 Costruzione `T_table` (incrementale)

```python
T_table = cache.get_or_update_table(
    original_graph, Oh_vertex, Oh_target, Os_vertex, Os_target, max_time
)
```

Vedi sezione [4 — SafeIntervalCache](#4-safeintervalcache).

### 3.6 Calcolo `T` e `T'`

- `T` = max timestep con vincolo hard sul goal + 1 (o 0). Threshold oltre cui il goal è accettabile senza conflitti hard.
- `T'` = max timestep con vincolo hard o soft sul goal + 1 (o 0). Usato nell'euristica per nodi con conflitti soft.

### 3.7 Root SIPPS

```python
root_int = T_table[start][0]   # primo intervallo sicuro dalla start
root = SIPPSNode(
    v=start, interval=root_int, interval_id=0, g=root_int[0],
    heuristic_map, Os_vertex, Os_edge, Os_target, T, Tprime,
    area_manager=..., occupancy_table=...
)
```

Root spinto in `open_list` e `open_dict`.

### 3.8 Loop SIPPS

```
while open_list:
    if stop_event.is_set(): return None, inf

    n = heapq.heappop(open_list)
    open_dict.pop(n.identity(), None)
    
    ① GOAL CHECK
    ② SUCCESSOR GENERATION
    ③ PROCESS SUCCESSORS
    ④ CLOSE NODE
```

---

## 4. `SafeIntervalCache`

### `get_or_update_table`

1. Indicizza i vincoli in ingresso per vertice (`new_hard_by_vertex`, `new_soft_by_vertex`).
2. Identifica i vertici `changed_vertices`:
   - Vertici già in cache con vincoli cambiati.
   - Vertici in `graph.nodes` non ancora presenti in cache.
3. Aggiorna i dizionari interni.
4. Per ogni vertice in `changed_vertices` chiama `_compute_vertex_intervals`.
5. Ritorna `{v: cached_T[v] for v in graph.nodes}` — T_table completa.

### `_compute_vertex_intervals(hard_times, soft_times, max_time)`

Scansione lineare del tempo `t ∈ [0, max_time)`:
- Se `t ∈ hard_times`: salta (timestep bloccato).
- Altrimenti: registra `soft_flag = t ∈ soft_times`, avanza finché il flag non cambia o si incontra un hard.
- Ogni segmento omogeneo → un intervallo `(start, end)`.

**Proprietà chiave**: due timestep consecutivi con diverso `soft_flag` appartengono a intervalli distinti. Questo è il meccanismo che permette a SIPPS di distinguere strutturalmente i timestep con e senza conflitti soft.

---

## 5. SIPPS — Loop interno

### ① Goal Check

```python
if n.is_goal:
    return extract_path(n), n.g

if n.v == goal and n.low >= T:
    cf = count future conflicts on goal in [n.low, max_time)
    if cf == 0:
        return extract_path(n), n.g
    else:
        goal_node = SIPPSNode(..., is_goal=True, cfuture=cf)
        insert_node(goal_node, ...)
```

Due casi per il goal:
1. **Nodo goal sintetico** (`is_goal=True`): già processato, ritorna direttamente.
2. **Vertice goal raggiunto** dopo `T`: conta i conflitti futuri. Se zero → ritorna. Se nonzero → crea un nodo goal sintetico con `cfuture=cf` per gestire correttamente l'ordinamento.

### ② Successor Generation

```python
I = set()
for w in get_valid_successors(graph, n.v, removed_edges):
    for idx, (lo, hi) in enumerate(T_table[w]):
        if n.low + 1 < hi and lo < n.high:   # overlap check
            I.add((w, idx))

# Wait action
for idx, (lo, hi) in enumerate(T_table[n.v]):
    if lo == n.high:
        I.add((n.v, idx))
```

**Condizione di overlap**: l'agente può arrivare in `w` al tempo `n.low + 1` (un passo). L'intervallo `[lo, hi)` deve contenere almeno quel timestep.

**Wait**: l'agente rimane in `n.v` fino alla fine del suo intervallo corrente (`n.high`) e rientra nel prossimo intervallo adiacente di `n.v`.

### ③ Process Successors

Per ogni `(v, idx) ∈ I`:

**Hard constraint check**:
```
t_start = max(n.g + 1, lo)
t_hard = primo t ∈ [t_start, hi) tale che
         (n.v, v, t) ∉ Oh_edge  AND  (v, t) ∉ Oh_vertex
```
Se `t_hard is None` → skip (nessun arrivo sicuro rispetto ai vincoli hard).

**Soft constraint check**:
```
t_soft = primo t ∈ [t_hard, hi) tale che
         (n.v, v, t) ∉ Os_edge  AND  (v, t) ∉ Os_vertex
```
Se `t_soft is None` → skip (l'intervallo è interamente coperto da vincoli soft).

**Creazione nodi**:

- **`t_soft > t_hard`** (c'è una finestra con conflitto soft prima di quella pulita):
  - `n1 = SIPPSNode(v, interval=(lo, t_soft), g=t_hard, parent=n, ...)` — arriva nella zona con conflitti
  - `n2 = SIPPSNode(v, interval=(t_soft, hi), g=t_soft, parent=n, ...)` — arriva nella zona pulita
  - Entrambi inseriti via `insert_node`.

- **`t_soft == t_hard`** (arrivo direttamente in zona pulita):
  - `n3 = SIPPSNode(v, interval=(lo, hi), g=t_hard, parent=n, ...)` — un solo nodo

### ④ Close Node

```python
closed_dict[n.identity()] = n
```

Nodo aggiunto al closed set **dopo** aver processato tutti i suoi successori.

---

## 6. `SIPPSNode.__init__` e `compute_c_value`

### Costruzione

```python
self.c_conflicts, self.c_entrance_penalty = self.compute_c_value(
    parent, Os_vertex, Os_edge, Os_target, cfuture, area_manager, occupancy_table
)

# Euristica
if is_goal:
    self.h = 0
elif c_conflicts + c_entrance_penalty == 0:
    self.h = max(heuristic_map[v], Tprime - self.g)
else:
    self.h = max(heuristic_map[v], T - self.g)

self.f = self.g + self.h
```

L'euristica si adatta: nodi senza conflitti puntano a `T'` (più lontano), nodi con conflitti puntano a `T` (più vicino), incentivando la ricerca di percorsi senza conflitti.

### `compute_c_value` — due canali di costo

**Canale 1: `c_entrance_penalty` (float)**

```python
# Penalità area (tempo-indipendente)
if current_area:
    c_entrance_penalty += 1.0 / max(current_area.capacity, 1)

# Penalità occupazione (tempo-dipendente)
if occupancy_table and current_area:
    occ = occupancy_table[current_area.id].get(self.g, 0)
    if occ >= capacity:
        c_entrance_penalty += occ / capacity
```

- **Penalità area**: applicata a **qualunque vertice** dentro un'area critica, incondizionatamente. Filosofia: "meno si sta nelle aree critiche, meglio è, sempre."
- **Penalità occupazione**: proporzionale al rapporto `occ/capacity`, attivata solo quando l'area è satura al tempo di arrivo. Lavora in sinergia con i T_table split (sezione 3.3).

**Canale 2: `c_conflicts` (int)**

```python
# Conflitti soft su vertice
for (v_obs, t_obs) in Os_vertex ∪ Os_target:
    if v_obs == self.v and t_obs ∈ [self.low, self.high):
        c_conflicts += 1

# Conflitto soft su arco
if parent and ((parent.v, self.v), self.low) in Os_edge:
    c_conflicts += 1

# Accumulo da parent
c_conflicts += parent.c_conflicts
c_entrance_penalty += parent.c_entrance_penalty

# Conflitti futuri (solo per nodi goal sintetici)
c_conflicts += cfuture
```

I valori si **accumulano dal parent**: ogni nodo porta il costo totale del percorso fino a quel punto, non solo il costo locale.

---

## 7. `insert_node`

```
insert_node(n, open_list, open_dict, closed_dict)
```

Lookup O(1) tramite `open_dict` e `closed_dict` (keyed su `identity()`).

### Logica di dominanza

`q.dominates_weakly(n)` è `True` se:
- Stessa identity `(v, interval_id, is_goal)`
- `q.low ≤ n.low` e `q.high ≥ n.high` (intervallo più ampio)
- `q.c_conflicts < n.c_conflicts` OR (`q.c_conflicts == n.c_conflicts` AND `q.c_entrance_penalty ≤ n.c_entrance_penalty`)

**Contro un nodo in open**:
1. `q_open` domina `n` → skip.
2. `n` domina `q_open` → rimuove `q_open`, poi inserisce `n`.
3. Intervalli sovrapposti → tronca il più vecchio o il nuovo, rimuove se diventa vuoto.

**Contro un nodo in closed**: stessa logica. Se `n` domina un nodo chiuso, lo rimuove dal closed (permette la riapertura).

Infine: `heapq.heappush(open_list, n)` + `open_dict[key] = n`.

---

## 8. `extract_path`

Ricostruisce il percorso dalla catena di parent.

```python
path_nodes = []
node = n
while node is not None:
    path_nodes.append(node)
    node = node.parent
path_nodes.reverse()

path = []
current_time = path_nodes[0].low

for node in path_nodes:
    while current_time < node.low:
        path.append(path[-1])   # wait step
        current_time += 1
    path.append(node.v)
    current_time += 1
```

I gap temporali tra nodi consecutivi (wait impliciti) vengono espansi in posizioni ripetute.

---

## 9. `build_solution`

```
build_solution(node) → (pi, tau)
```

1. Estende tutti i percorsi alla lunghezza massima (agenti già arrivati al goal restano fermi).
2. `tau`: lista di stati congiunti `(pos_agent0, pos_agent1, ..., pos_agentN)` per ogni timestep.
3. `pi = extract_pi_from_tau(tau)`: lista di macroazioni `((action, from_cell), ...)` per ogni transizione.

---

## 10. `detect_conflict`

Scansiona i percorsi in due fasi:

**Conflitti di vertice**: per ogni `t`, se due agenti `i, j` occupano la stessa posizione → `(i, j, pos, t, "vertex")`.

**Conflitti di arco** (swap): per ogni `t`, se agente `i` si muove da `u` a `v` e agente `j` si muove da `v` a `u` nello stesso timestep → `(i, j, (u,v), t, "edge")`.

Ritorna il **primo** conflitto trovato, o `None` se nessuno.

---

## 11. `build_occupancy_table`

```
build_occupancy_table(paths, area_manager, current_agent_goal, all_agent_goals)
→ {area_id: {t: count}}
```

Per ogni agente, per ogni timestep, identifica l'area occupata tramite `area_manager.get_area_by_position`.  
**Esclude** gli agenti il cui goal si trova nell'area stessa (sono "residenti legittimi", non contribuiscono alla saturazione).

---

## Diagramma flusso sintetico

```
compute_plan_cbs
│
├─ CBSNode.root → compute_low_level_solution (tutti gli agenti)
│                   └─ low_level_search_cbs × N
│                         ├─ populate hard constraints  (Oh_vertex, Oh_edge)
│                         ├─ populate soft constraints  (Os_vertex, Os_edge) ← altri agenti
│                         ├─ build_occupancy_table
│                         │    └─ T_table split sugli entrance_vertices saturi → Os_vertex
│                         ├─ failed_actions → removed_edges
│                         ├─ SafeIntervalCache.get_or_update_table → T_table
│                         ├─ root SIPPSNode
│                         └─ SIPPS loop
│                               ├─ heappop
│                               ├─ goal check → extract_path
│                               ├─ successor gen (overlap check + wait)
│                               ├─ hard/soft constraint scan → t_hard, t_soft
│                               ├─ SIPPSNode creation (n1+n2 o n3)
│                               │    └─ compute_c_value
│                               │         ├─ area penalty (incondizionale)
│                               │         ├─ occupancy penalty (se satura)
│                               │         ├─ c_conflicts (soft vertex + edge)
│                               │         └─ accumulo da parent
│                               └─ insert_node (dominance check)
│
├─ heappop → build_solution → detect_conflict
│
├─ Conflitto → 2 CBSNode figli con nuovo vincolo hard → compute_low_level_solution (1 agente)
│
└─ No conflitto, no down state → return (pi, tau)
```

---

## Note implementative rilevanti

- **`os_entrances`** è un parametro accettato ma attualmente non usato internamente (rimasto per compatibilità API con `resplan_mapf`).
- **`add_area_capacity_soft_constraints`** è una funzione definita nel file ma non più richiamata nel flusso principale: era la versione precedente basata su `Os_edge`; sostituita dall'approccio `Os_vertex + occupancy_table`.
- **`build_safe_interval_table`** è la versione non cached, mantenuta come riferimento ma non più chiamata direttamente (si usa `SafeIntervalCache.get_or_update_table`).
- **`heuristic`** è chiamata esternamente (da `main.py` / `resplan_mapf`) per pre-calcolare `h_maps` prima di entrare in `compute_plan_cbs`. Non è invocata dentro il solver.
- Il `stop_event` è controllato sia nel loop CBS che in ogni istanza del loop SIPPS: garantisce interruzione pulita senza eccezioni.
