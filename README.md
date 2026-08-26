# Res-MAPF v2

## Version Description

v2 computes resilient multi-agent path-finding plans: given several agents with start and goal positions on a grid map, and a specification of how many action failures the plan must be able to survive during execution — how many failures in total, how many agents they're allowed to affect, and how many failures a single agent can individually suffer — it searches for a joint plan for all agents that stays valid no matter which of the tolerated failures actually happens once execution starts.

v2 is a performance-optimized version of the original Baseline implementation of this same idea. The optimization only changes how efficiently the plan is computed — the underlying approach and the kind of plan produced are the same as the Baseline's; nothing about the algorithm itself was restructured. A graphical interface lets you set up an instance, solve it, and then step through — or simulate failures on — the resulting plan.

## Project Overview

Res-MAPF is a resilient multi-agent path-finding (MAPF) research project, developed across several related repositories, each a different version or contribution. This repository is **v2** — see [Version Description](#version-description) above for what makes it different from the others.

Related repositories: [Baseline/v1](https://github.com/drossi99/resilient_mapf) (external, the original implementation v2 optimizes), [v2.1](https://github.com/Res-MAPF/Res-MAPF_v2.1), [v3](https://github.com/Res-MAPF/Res-MAPF_v3), [benchmark](https://github.com/Res-MAPF/Res-MAPF_benchmark).

### Setup Instructions

#### Prerequisites

- Python 3.11 or newer
- Git
- On Linux, the `tkinter` system package (the GUI is built on it via `customtkinter`): `sudo apt install python3-tk` (Debian/Ubuntu) or `sudo dnf install python3-tkinter` (Fedora)

#### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Res-MAPF/Res-MAPF_v2.git
   cd Res-MAPF_v2
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   See [requirements.txt](requirements.txt) for the full list.

### Documentation

📘 **[Usage Guide](https://github.com/Res-MAPF/.github/blob/main/profile/Res-MAPF%20Solver%20-%20guide.md)** — organization-wide, end-to-end walkthrough covering installation, launching the CLI/GUI, solving instances, running batches at scale, and analyzing results. v2 is covered for the whole pipeline (its CLI is `run_cli_v2.py`); its one gap versus v3 is that it has no empirical-robustness check — see the guide's version-coverage note at the top for details.

The `src/` package is organized in layers: a domain layer that models a MAPF instance and its resilience budget and generates test instances, a solver layer underneath it that implements the ResPlaN resilient-planning algorithm (CBS + SIPPS for the nominal plan, wrapped in the failure-branching search), a utilities layer for map loading, plan persistence, and profiling/experiment output, and a view layer that provides the customtkinter GUI on top of all of it. Each folder below has its own README with per-file detail.

**Package layout:**
- **[Source Overview](src/README.md)** — The `src/` entry points (GUI launcher, headless CLI runner, parallel batch driver) and how the package is organized.

**Domain and solving:**
- **[Domain Layer](src/domain/README.md)** — The MAPF instance/robustness data model and random test-instance generation.
- **[Solver](src/domain/solver/README.md)** — The ResPlaN resilient-planning algorithm itself: failure-branching search plus the CBS/SIPPS nominal planner it calls.

**Support layers:**
- **[Utilities](src/utils/README.md)** — Map loading, instance/plan persistence, profiling infrastructure, and experiment CSV output.
- **[GUI / View Layer](src/view/README.md)** — The customtkinter interface for building, solving, and interactively simulating failures on a plan.

### Citations

Cite this repository using the metadata in [CITATION.cff](CITATION.cff).

Suggested software citation:

> Turini, A. C. (2026). *Res-MAPF v2* [Software]. GitHub. <https://github.com/Res-MAPF/Res-MAPF_v2>

### License

[MIT License](LICENSE)
