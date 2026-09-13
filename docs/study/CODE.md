# Code Bases — reference implementations to learn from
### (study existing code, don't build from scratch — direction not yet chosen)

> **Why this file:** the project will *understand and build on existing implementations*, not
> write a PF from zero. These are the reference code bases worth reading. Direction (which to
> base the project on) is **not decided yet** — this is survey-stage capture.

## The repos
| Repo | Lang | What it is | Best for | Paper link |
|---|---|---|---|---|
| ⭐ **jelfring/particle-filter-tutorial** | Python | Joris Elfring's minimal, pedagogical PF tutorial code — **already implements 4 resampling schemes: multinomial · residual · stratified · systematic** | **the starting point AND the sampling-experiment base** — small, readable, maps 1:1 to the tutorial paper; swap/add resampling schemes on top of it | ↔ **`tutorial_2021_Elfring_PF_HandsOn.pdf`** (direct companion) |
| ⭐ **rlabbe/Kalman-and-Bayesian-Filters-in-Python** | Python | Roger Labbe's interactive Jupyter book + the **`filterpy`** library (Bayes → KF → EKF → UKF → PF) | learning-by-code across the whole filter family; use `filterpy` to *check* your own code | the primary in `learning/slam_engineer/slam_theory/estimation_filters/STUDY_GUIDE.md` |
| **orocos/orocos-bayesian-filtering** (BFL) | **C++** | Bayesian Filtering Library — production framework for recursive Bayesian estimation (KF + particle filters); Orocos/ROS ecosystem | seeing a *real C++* PF/KF architecture (closer to SLAM back-ends) | — |

## Links (as provided)
- **BFL (Orocos Bayesian Filtering Library)** — https://github.com/orocos/orocos-bayesian-filtering *(accessed 17 Dec 2020)*
- **Kalman-and-Bayesian-Filters-in-Python** (Roger Labbe) — https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python *(accessed 17 Dec 2020)*
- **particle-filter-tutorial** (Joris Elfring) — https://github.com/jelfring/particle-filter-tutorial

## How to use them (when the build phase starts)
1. **Start with `jelfring/particle-filter-tutorial`** while reading its paper (`tutorial_2021_Elfring_PF_HandsOn.pdf`) — smallest gap between theory and code.
2. **`rlabbe` / `filterpy`** — reference for the broader family and a *checker* for your hand-rolled versions (don't just import it — re-derive, then compare).
3. **BFL** — read if the project goes the **C++** route (aligns with the SLAM back-end skill track); heavier, but production-grade.
> **Note:** Python repos (jelfring, rlabbe) = fastest path to understanding; BFL (C++) = closer to real SLAM systems. Pick per the direction chosen later.

*(Repos are linked, not cloned — clone into a `code/` sibling of this folder when the build phase starts, or ask Claude to clone them.)*
