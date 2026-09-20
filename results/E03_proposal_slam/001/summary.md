# Which proposal distribution? (FastSLAM 1.0 vs 2.0) (001)

**Question.** Does FastSLAM 2.0, which samples the pose from a proposal that includes the current observation, give better pose and map estimates than FastSLAM 1.0, and does the advantage shrink with more particles?

**Hypothesis.** FastSLAM 2.0 is more accurate and keeps a higher ESS, especially with few particles, at a higher runtime per step (Montemerlo et al., 2003).

## Setup

- Result set 001
- Filter: fastslam
- Fixed: resampler = systematic
- Varied: proposal: fastslam1, fastslam2; n_particles: 5, 10, 25, 100
- Seeds: 20 (each seed fixes the world and the filter's randomness, the same for every variant), 160 runs

## Results

| Proposal     |   Particles |   Seeds | Position RMSE (m)   | ATE (aligned) (m)   | Map error (aligned) (m)   | Mean ESS / N   | Runtime per step (ms)   |
|:-------------|------------:|--------:|:--------------------|:--------------------|:--------------------------|:---------------|:------------------------|
| FastSLAM 1.0 |           5 |      20 | 1.12 ± 0.56         | 0.335 ± 0.052       | 0.16 ± 0.047              | 0.764 ± 0.0061 | 1.28 ± 0.0076           |
| FastSLAM 1.0 |          10 |      20 | 0.958 ± 0.61        | 0.255 ± 0.033       | 0.111 ± 0.034             | 0.753 ± 0.0043 | 1.39 ± 0.0064           |
| FastSLAM 1.0 |          25 |      20 | 0.673 ± 0.4         | 0.212 ± 0.05        | 0.0946 ± 0.025            | 0.75 ± 0.0023  | 1.86 ± 0.013            |
| FastSLAM 1.0 |         100 |      20 | 0.777 ± 0.35        | 0.247 ± 0.094       | 0.0565 ± 0.016            | 0.748 ± 0.0022 | 3.19 ± 0.018            |
| FastSLAM 2.0 |           5 |      20 | 0.773 ± 0.43        | 0.257 ± 0.037       | 0.102 ± 0.029             | 0.813 ± 0.0042 | 1.98 ± 0.013            |
| FastSLAM 2.0 |          10 |      20 | 0.774 ± 0.47        | 0.215 ± 0.046       | 0.0909 ± 0.026            | 0.802 ± 0.0038 | 2.15 ± 0.012            |
| FastSLAM 2.0 |          25 |      20 | 0.748 ± 0.47        | 0.275 ± 0.089       | 0.078 ± 0.015             | 0.795 ± 0.0025 | 2.66 ± 0.028            |
| FastSLAM 2.0 |         100 |      20 | 0.737 ± 0.33        | 0.228 ± 0.067       | 0.0479 ± 0.012            | 0.793 ± 0.0024 | 4.79 ± 0.27             |

Mean ± standard deviation over seeds.

## Findings (computed automatically)

- At n particles = 5: clear differences in ATE (aligned) (FastSLAM 2.0 0.257 vs FastSLAM 1.0 0.335, 23%), Map error (aligned) (FastSLAM 2.0 0.102 vs FastSLAM 1.0 0.16, 36%), Mean ESS / N (FastSLAM 2.0 0.813 vs FastSLAM 1.0 0.764, 6%) and Runtime per step (FastSLAM 1.0 1.28 vs FastSLAM 2.0 1.98, 36%).
- At n particles = 5: no difference beyond the seed-to-seed spread in Position RMSE.
- At n particles = 10: clear differences in ATE (aligned) (FastSLAM 2.0 0.215 vs FastSLAM 1.0 0.255, 16%), Mean ESS / N (FastSLAM 2.0 0.802 vs FastSLAM 1.0 0.753, 6%) and Runtime per step (FastSLAM 1.0 1.39 vs FastSLAM 2.0 2.15, 35%).
- At n particles = 10: no difference beyond the seed-to-seed spread in Position RMSE and Map error (aligned).
- At n particles = 25: clear differences in ATE (aligned) (FastSLAM 1.0 0.212 vs FastSLAM 2.0 0.275, 23%), Mean ESS / N (FastSLAM 2.0 0.795 vs FastSLAM 1.0 0.75, 6%) and Runtime per step (FastSLAM 1.0 1.86 vs FastSLAM 2.0 2.66, 30%).
- At n particles = 25: no difference beyond the seed-to-seed spread in Position RMSE and Map error (aligned).
- At n particles = 100: clear differences in Mean ESS / N (FastSLAM 2.0 0.793 vs FastSLAM 1.0 0.748, 6%) and Runtime per step (FastSLAM 1.0 3.19 vs FastSLAM 2.0 4.79, 33%).
- At n particles = 100: no difference beyond the seed-to-seed spread in Position RMSE, ATE (aligned) and Map error (aligned).

## Notes

- 160 of 160 runs were made with a different version of the code than the current one.

## Figures

![metrics](figures/metrics.png)
