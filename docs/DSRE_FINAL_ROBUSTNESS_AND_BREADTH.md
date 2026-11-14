# DSRE: registered observation sensitivity, witnesses and breadth

Evidence: `results/dsre-operational/20261114T180630Z`. Same frozen observations and actual paired outcomes; no detector, new skill or sensor deployment.

Noise repetitions are averaged within parent before 4000 parent-bootstrap draws. Conditions/repetitions are not independent parents. Every fixed grid point is retained. Clean statistical eligibility does not transfer to corrupted packets. UNKNOWN is never known false. Factual contradictions are retrospective comparisons with clean telemetry, not an online fault detector.

| Population | Task/method | Scenario | Effective N / parents | Good% [95%] | Bad% [95%] | Defer% [95%] | Action instability% [95%] | Contradicted-fact proposal% [95%] |
|---|---|---|---:|---:|---:|---:|---:|---:|
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_strict | clean | 332.0/166 | 56.33 [53.92,59.04] | 0.00 [0.00,0.00] | 43.67 [40.96,46.08] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_risk | clean | 332.0/166 | 72.59 [68.98,76.51] | 0.00 [0.00,0.00] | 27.41 [23.49,31.02] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B7_risk | clean | 332.0/166 | 72.59 [68.98,76.51] | 0.00 [0.00,0.00] | 27.41 [23.49,31.02] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B5_beta10 | clean | 332.0/166 | 67.47 [63.86,71.08] | 5.12 [3.01,7.53] | 27.41 [23.49,31.02] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/CART2_beta10 | clean | 332.0/166 | 72.29 [68.67,76.20] | 0.00 [0.00,0.00] | 27.71 [23.80,31.33] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_continue | clean | 332.0/166 | 67.47 [63.86,71.08] | 32.53 [28.92,36.14] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_recover | clean | 332.0/166 | 74.70 [68.07,80.72] | 25.30 [19.28,31.93] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_strict | clean | 334.0/167 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_risk | clean | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B7_risk | clean | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B5_beta10 | clean | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/CART2_beta10 | clean | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_continue | clean | 334.0/167 | 50.00 [50.00,50.00] | 50.00 [50.00,50.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_recover | clean | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_strict | missing_optional | 332.0/166 | 43.67 [39.46,47.89] | 0.00 [0.00,0.00] | 56.33 [52.11,60.54] | 12.65 [9.34,16.57] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_risk | missing_optional | 332.0/166 | 72.29 [68.67,76.20] | 0.00 [0.00,0.00] | 27.71 [23.80,31.33] | 0.30 [0.00,0.90] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B7_risk | missing_optional | 332.0/166 | 72.29 [68.67,76.20] | 0.00 [0.00,0.00] | 27.71 [23.80,31.33] | 0.30 [0.00,0.90] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B5_beta10 | missing_optional | 332.0/166 | 67.47 [63.86,71.08] | 4.82 [2.71,7.23] | 27.71 [23.80,31.33] | 0.30 [0.00,0.90] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/CART2_beta10 | missing_optional | 332.0/166 | 4.82 [2.71,7.23] | 0.00 [0.00,0.00] | 95.18 [92.77,97.29] | 67.47 [63.86,71.08] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_continue | missing_optional | 332.0/166 | 67.47 [63.86,71.08] | 32.53 [28.92,36.14] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_recover | missing_optional | 332.0/166 | 74.70 [68.07,80.72] | 25.30 [19.28,31.93] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_strict | missing_optional | 334.0/167 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_risk | missing_optional | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B7_risk | missing_optional | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B5_beta10 | missing_optional | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/CART2_beta10 | missing_optional | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_continue | missing_optional | 334.0/167 | 50.00 [50.00,50.00] | 50.00 [50.00,50.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_recover | missing_optional | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_strict | missing_history | 332.0/166 | 56.02 [53.61,58.73] | 0.00 [0.00,0.00] | 43.98 [41.27,46.39] | 0.30 [0.00,0.90] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_risk | missing_history | 332.0/166 | 72.29 [68.67,76.20] | 0.00 [0.00,0.00] | 27.71 [23.80,31.33] | 0.30 [0.00,0.90] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B7_risk | missing_history | 332.0/166 | 72.29 [68.67,76.20] | 0.00 [0.00,0.00] | 27.71 [23.80,31.33] | 0.30 [0.00,0.90] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B5_beta10 | missing_history | 332.0/166 | 67.47 [63.86,71.08] | 4.82 [2.71,7.23] | 27.71 [23.80,31.33] | 0.30 [0.00,0.90] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/CART2_beta10 | missing_history | 332.0/166 | 72.29 [68.67,76.20] | 0.00 [0.00,0.00] | 27.71 [23.80,31.33] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_continue | missing_history | 332.0/166 | 67.47 [63.86,71.08] | 32.53 [28.92,36.14] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_recover | missing_history | 332.0/166 | 74.70 [68.07,80.72] | 25.30 [19.28,31.93] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_strict | missing_history | 334.0/167 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_risk | missing_history | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B7_risk | missing_history | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B5_beta10 | missing_history | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/CART2_beta10 | missing_history | 334.0/167 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_continue | missing_history | 334.0/167 | 50.00 [50.00,50.00] | 50.00 [50.00,50.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_recover | missing_history | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_strict | missing_pose | 332.0/166 | 38.86 [35.54,41.87] | 0.00 [0.00,0.00] | 61.14 [58.13,64.46] | 17.47 [13.55,21.39] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_risk | missing_pose | 332.0/166 | 38.86 [35.54,41.87] | 0.00 [0.00,0.00] | 61.14 [58.13,64.46] | 33.73 [27.71,40.06] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B7_risk | missing_pose | 332.0/166 | 38.86 [35.54,41.87] | 0.00 [0.00,0.00] | 61.14 [58.13,64.46] | 33.73 [27.71,40.06] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B5_beta10 | missing_pose | 332.0/166 | 38.86 [35.54,41.87] | 0.00 [0.00,0.00] | 61.14 [58.13,64.46] | 33.73 [27.71,40.06] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/CART2_beta10 | missing_pose | 332.0/166 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 72.29 [68.67,76.20] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_continue | missing_pose | 332.0/166 | 67.47 [63.86,71.08] | 32.53 [28.92,36.14] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_recover | missing_pose | 332.0/166 | 74.70 [68.07,80.72] | 25.30 [19.28,31.93] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_strict | missing_pose | 334.0/167 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_risk | missing_pose | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B7_risk | missing_pose | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B5_beta10 | missing_pose | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/CART2_beta10 | missing_pose | 334.0/167 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_continue | missing_pose | 334.0/167 | 50.00 [50.00,50.00] | 50.00 [50.00,50.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_recover | missing_pose | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_strict | noise001 | 332.0/166 | 59.34 [57.03,61.95] | 0.00 [0.00,0.00] | 40.66 [38.05,42.97] | 4.82 [3.31,6.43] | 3.92 [2.61,5.32] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_risk | noise001 | 332.0/166 | 72.49 [68.78,76.20] | 0.00 [0.00,0.00] | 27.51 [23.80,31.22] | 0.30 [0.00,0.80] | 3.92 [2.61,5.32] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B7_risk | noise001 | 332.0/166 | 72.49 [68.78,76.20] | 0.00 [0.00,0.00] | 27.51 [23.80,31.22] | 0.30 [0.00,0.80] | 3.92 [2.61,5.32] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B5_beta10 | noise001 | 332.0/166 | 67.47 [63.86,71.08] | 5.02 [2.91,7.33] | 27.51 [23.80,31.22] | 0.30 [0.00,0.80] | 0.10 [0.00,0.30] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/CART2_beta10 | noise001 | 332.0/166 | 71.79 [68.07,75.60] | 0.00 [0.00,0.00] | 28.21 [24.40,31.93] | 0.50 [0.00,1.31] | 4.52 [3.01,6.22] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_continue | noise001 | 332.0/166 | 67.47 [63.86,71.08] | 32.53 [28.92,36.14] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_recover | noise001 | 332.0/166 | 74.70 [68.07,80.72] | 25.30 [19.28,31.93] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_strict | noise001 | 334.0/167 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_risk | noise001 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B7_risk | noise001 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B5_beta10 | noise001 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/CART2_beta10 | noise001 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_continue | noise001 | 334.0/167 | 50.00 [50.00,50.00] | 50.00 [50.00,50.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_recover | noise001 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_strict | noise005 | 332.0/166 | 65.76 [63.15,68.57] | 0.50 [0.10,1.00] | 33.73 [30.92,36.35] | 11.95 [9.74,14.36] | 10.94 [8.63,13.25] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_risk | noise005 | 332.0/166 | 73.49 [69.88,77.21] | 0.50 [0.10,1.00] | 26.00 [22.29,29.72] | 3.71 [2.51,4.92] | 10.94 [8.63,13.25] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B7_risk | noise005 | 332.0/166 | 73.49 [69.88,77.21] | 0.50 [0.10,1.00] | 26.00 [22.29,29.72] | 3.71 [2.51,4.92] | 10.94 [8.63,13.25] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B5_beta10 | noise005 | 332.0/166 | 67.47 [63.86,71.08] | 6.53 [4.42,8.94] | 26.00 [22.29,29.72] | 2.01 [1.10,3.11] | 2.01 [1.10,3.11] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/CART2_beta10 | noise005 | 332.0/166 | 72.09 [68.37,75.80] | 0.30 [0.00,0.70] | 27.61 [23.80,31.33] | 2.21 [1.31,3.31] | 10.24 [7.93,12.65] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_continue | noise005 | 332.0/166 | 67.47 [63.86,71.08] | 32.53 [28.92,36.14] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_recover | noise005 | 332.0/166 | 74.70 [68.07,80.72] | 25.30 [19.28,31.93] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_strict | noise005 | 334.0/167 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_risk | noise005 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B7_risk | noise005 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B5_beta10 | noise005 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/CART2_beta10 | noise005 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 12.97 [11.18,14.77] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_continue | noise005 | 334.0/167 | 50.00 [50.00,50.00] | 50.00 [50.00,50.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_recover | noise005 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_strict | delay1 | 332.0/166 | 56.33 [53.92,59.04] | 0.00 [0.00,0.00] | 43.67 [40.96,46.08] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_risk | delay1 | 332.0/166 | 72.59 [68.98,76.51] | 0.00 [0.00,0.00] | 27.41 [23.49,31.02] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B7_risk | delay1 | 332.0/166 | 72.59 [68.98,76.51] | 0.00 [0.00,0.00] | 27.41 [23.49,31.02] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B5_beta10 | delay1 | 332.0/166 | 67.47 [63.86,71.08] | 5.12 [3.01,7.53] | 27.41 [23.49,31.02] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/CART2_beta10 | delay1 | 332.0/166 | 72.29 [68.67,76.20] | 0.00 [0.00,0.00] | 27.71 [23.80,31.33] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_continue | delay1 | 332.0/166 | 67.47 [63.86,71.08] | 32.53 [28.92,36.14] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_recover | delay1 | 332.0/166 | 74.70 [68.07,80.72] | 25.30 [19.28,31.93] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_strict | delay1 | 334.0/167 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_risk | delay1 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B7_risk | delay1 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B5_beta10 | delay1 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/CART2_beta10 | delay1 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_continue | delay1 | 334.0/167 | 50.00 [50.00,50.00] | 50.00 [50.00,50.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_recover | delay1 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_strict | delay5 | 332.0/166 | 56.33 [53.61,59.34] | 1.81 [0.30,3.92] | 41.87 [39.16,44.58] | 3.31 [1.20,5.72] | 3.31 [1.20,5.72] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/DSRE_risk | delay5 | 332.0/166 | 70.78 [66.87,74.70] | 1.81 [0.30,3.92] | 27.41 [23.49,31.02] | 1.81 [0.30,3.92] | 3.31 [1.20,5.72] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B7_risk | delay5 | 332.0/166 | 70.78 [66.87,74.70] | 1.81 [0.30,3.92] | 27.41 [23.49,31.02] | 1.81 [0.30,3.92] | 3.31 [1.20,5.72] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B5_beta10 | delay5 | 332.0/166 | 67.47 [63.86,71.08] | 5.12 [3.01,7.53] | 27.41 [23.49,31.02] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/CART2_beta10 | delay5 | 332.0/166 | 67.47 [62.95,71.99] | 4.82 [2.41,7.53] | 27.71 [23.80,31.33] | 4.82 [2.41,7.53] | 6.33 [3.61,9.34] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_continue | delay5 | 332.0/166 | 67.47 [63.86,71.08] | 32.53 [28.92,36.14] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PickCube-v1/B0_recover | delay5 | 332.0/166 | 74.70 [68.07,80.72] | 25.30 [19.28,31.93] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_strict | delay5 | 334.0/167 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/DSRE_risk | delay5 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B7_risk | delay5 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B5_beta10 | delay5 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/CART2_beta10 | delay5 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 49.70 [49.10,50.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_continue | delay5 | 334.0/167 | 50.00 [50.00,50.00] | 50.00 [50.00,50.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| INSPECTED_HISTORICAL_333 | PushCube-v1/B0_recover | delay5 | 334.0/167 | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_strict | clean | 160.0/80 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_risk | clean | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B7_risk | clean | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B5_beta10 | clean | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/CART2_beta10 | clean | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_continue | clean | 160.0/80 | 49.38 [48.12,50.00] | 50.62 [50.00,51.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_recover | clean | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_strict | missing_optional | 160.0/80 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_risk | missing_optional | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B7_risk | missing_optional | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B5_beta10 | missing_optional | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/CART2_beta10 | missing_optional | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_continue | missing_optional | 160.0/80 | 49.38 [48.12,50.00] | 50.62 [50.00,51.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_recover | missing_optional | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_strict | missing_history | 160.0/80 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_risk | missing_history | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B7_risk | missing_history | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B5_beta10 | missing_history | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/CART2_beta10 | missing_history | 160.0/80 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_continue | missing_history | 160.0/80 | 49.38 [48.12,50.00] | 50.62 [50.00,51.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_recover | missing_history | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_strict | missing_pose | 160.0/80 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_risk | missing_pose | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B7_risk | missing_pose | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B5_beta10 | missing_pose | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/CART2_beta10 | missing_pose | 160.0/80 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_continue | missing_pose | 160.0/80 | 49.38 [48.12,50.00] | 50.62 [50.00,51.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_recover | missing_pose | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_strict | noise001 | 160.0/80 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_risk | noise001 | 160.0/80 | 99.38 [98.12,100.00] | 0.63 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B7_risk | noise001 | 160.0/80 | 99.38 [98.12,100.00] | 0.63 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B5_beta10 | noise001 | 160.0/80 | 99.38 [98.12,100.00] | 0.63 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/CART2_beta10 | noise001 | 160.0/80 | 99.38 [98.12,100.00] | 0.63 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_continue | noise001 | 160.0/80 | 49.38 [48.13,50.00] | 50.63 [50.00,51.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_recover | noise001 | 160.0/80 | 99.38 [98.12,100.00] | 0.63 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_strict | noise005 | 160.0/80 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_risk | noise005 | 160.0/80 | 99.38 [98.12,100.00] | 0.63 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B7_risk | noise005 | 160.0/80 | 99.38 [98.12,100.00] | 0.63 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B5_beta10 | noise005 | 160.0/80 | 99.38 [98.12,100.00] | 0.63 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/CART2_beta10 | noise005 | 160.0/80 | 99.38 [98.12,100.00] | 0.63 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 12.50 [9.79,15.42] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_continue | noise005 | 160.0/80 | 49.38 [48.13,50.00] | 50.63 [50.00,51.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_recover | noise005 | 160.0/80 | 99.38 [98.12,100.00] | 0.63 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_strict | delay1 | 160.0/80 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_risk | delay1 | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B7_risk | delay1 | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B5_beta10 | delay1 | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/CART2_beta10 | delay1 | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_continue | delay1 | 160.0/80 | 49.38 [48.12,50.00] | 50.62 [50.00,51.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_recover | delay1 | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_strict | delay5 | 160.0/80 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/DSRE_risk | delay5 | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B7_risk | delay5 | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B5_beta10 | delay5 | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/CART2_beta10 | delay5 | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 50.00 [50.00,50.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_continue | delay5 | 160.0/80 | 49.38 [48.12,50.00] | 50.62 [50.00,51.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PushCube-v1/B0_recover | delay5 | 160.0/80 | 99.38 [98.12,100.00] | 0.62 [0.00,1.88] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_strict | clean | 158.0/79 | 53.80 [51.27,56.96] | 0.00 [0.00,0.00] | 46.20 [43.04,48.73] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_risk | clean | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B7_risk | clean | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B5_beta10 | clean | 158.0/79 | 69.62 [64.56,74.68] | 3.16 [0.63,6.33] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/CART2_beta10 | clean | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_continue | clean | 158.0/79 | 69.62 [64.56,74.68] | 30.38 [25.32,35.44] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_recover | clean | 158.0/79 | 65.82 [55.70,75.95] | 34.18 [24.05,44.30] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_strict | missing_optional | 158.0/79 | 40.51 [34.81,46.20] | 0.00 [0.00,0.00] | 59.49 [53.80,65.19] | 13.29 [8.23,18.99] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_risk | missing_optional | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B7_risk | missing_optional | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B5_beta10 | missing_optional | 158.0/79 | 69.62 [64.56,74.68] | 3.16 [0.63,6.33] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/CART2_beta10 | missing_optional | 158.0/79 | 3.16 [0.63,6.33] | 0.00 [0.00,0.00] | 96.84 [93.67,99.37] | 69.62 [64.56,74.68] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_continue | missing_optional | 158.0/79 | 69.62 [64.56,74.68] | 30.38 [25.32,35.44] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_recover | missing_optional | 158.0/79 | 65.82 [55.70,75.95] | 34.18 [24.05,44.30] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_strict | missing_history | 158.0/79 | 53.80 [51.27,56.96] | 0.00 [0.00,0.00] | 46.20 [43.04,48.73] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_risk | missing_history | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B7_risk | missing_history | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B5_beta10 | missing_history | 158.0/79 | 69.62 [64.56,74.68] | 3.16 [0.63,6.33] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/CART2_beta10 | missing_history | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_continue | missing_history | 158.0/79 | 69.62 [64.56,74.68] | 30.38 [25.32,35.44] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_recover | missing_history | 158.0/79 | 65.82 [55.70,75.95] | 34.18 [24.05,44.30] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_strict | missing_pose | 158.0/79 | 37.34 [32.28,41.77] | 0.00 [0.00,0.00] | 62.66 [58.23,67.72] | 16.46 [11.39,22.15] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_risk | missing_pose | 158.0/79 | 37.34 [32.28,41.77] | 0.00 [0.00,0.00] | 62.66 [58.23,67.72] | 35.44 [26.58,44.94] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B7_risk | missing_pose | 158.0/79 | 37.34 [32.28,41.77] | 0.00 [0.00,0.00] | 62.66 [58.23,67.72] | 35.44 [26.58,44.94] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B5_beta10 | missing_pose | 158.0/79 | 37.34 [32.28,41.77] | 0.00 [0.00,0.00] | 62.66 [58.23,67.72] | 35.44 [26.58,44.94] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/CART2_beta10 | missing_pose | 158.0/79 | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 100.00 [100.00,100.00] | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_continue | missing_pose | 158.0/79 | 69.62 [64.56,74.68] | 30.38 [25.32,35.44] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_recover | missing_pose | 158.0/79 | 65.82 [55.70,75.95] | 34.18 [24.05,44.30] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_strict | noise001 | 158.0/79 | 59.28 [56.12,62.87] | 0.21 [0.00,0.63] | 40.51 [36.92,43.67] | 5.70 [3.59,8.02] | 5.70 [3.59,8.02] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_risk | noise001 | 158.0/79 | 72.78 [67.72,78.48] | 0.21 [0.00,0.63] | 27.00 [21.51,32.28] | 0.21 [0.00,0.63] | 5.70 [3.59,8.02] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B7_risk | noise001 | 158.0/79 | 72.78 [67.72,78.48] | 0.21 [0.00,0.63] | 27.00 [21.51,32.28] | 0.21 [0.00,0.63] | 5.70 [3.59,8.02] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B5_beta10 | noise001 | 158.0/79 | 69.62 [64.56,74.68] | 3.38 [0.84,6.33] | 27.00 [21.51,32.28] | 0.21 [0.00,0.63] | 0.21 [0.00,0.63] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/CART2_beta10 | noise001 | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 5.49 [3.38,7.81] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_continue | noise001 | 158.0/79 | 69.62 [64.56,74.68] | 30.38 [25.32,35.44] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_recover | noise001 | 158.0/79 | 65.82 [55.70,75.95] | 34.18 [24.05,44.30] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_strict | noise005 | 158.0/79 | 65.19 [61.18,69.41] | 2.32 [0.84,4.22] | 32.49 [28.27,36.71] | 15.40 [11.60,19.20] | 14.56 [10.76,18.57] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_risk | noise005 | 158.0/79 | 72.57 [67.51,77.85] | 2.32 [0.84,4.22] | 25.11 [19.83,30.17] | 5.91 [3.59,8.44] | 14.56 [10.76,18.57] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B7_risk | noise005 | 158.0/79 | 72.57 [67.51,77.85] | 2.32 [0.84,4.22] | 25.11 [19.83,30.17] | 5.91 [3.59,8.44] | 14.56 [10.76,18.57] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B5_beta10 | noise005 | 158.0/79 | 69.62 [64.56,74.68] | 5.27 [2.74,8.44] | 25.11 [19.83,30.17] | 2.95 [1.27,5.06] | 2.74 [1.05,4.64] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/CART2_beta10 | noise005 | 158.0/79 | 71.52 [66.45,77.00] | 0.84 [0.00,1.90] | 27.64 [22.15,32.91] | 3.38 [1.69,5.27] | 12.45 [8.65,16.46] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_continue | noise005 | 158.0/79 | 69.62 [64.56,74.68] | 30.38 [25.32,35.44] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_recover | noise005 | 158.0/79 | 65.82 [55.70,75.95] | 34.18 [24.05,44.30] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_strict | delay1 | 158.0/79 | 53.80 [51.27,56.96] | 0.00 [0.00,0.00] | 46.20 [43.04,48.73] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_risk | delay1 | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B7_risk | delay1 | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B5_beta10 | delay1 | 158.0/79 | 69.62 [64.56,74.68] | 3.16 [0.63,6.33] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/CART2_beta10 | delay1 | 158.0/79 | 72.78 [67.72,78.48] | 0.00 [0.00,0.00] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_continue | delay1 | 158.0/79 | 69.62 [64.56,74.68] | 30.38 [25.32,35.44] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_recover | delay1 | 158.0/79 | 65.82 [55.70,75.95] | 34.18 [24.05,44.30] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_strict | delay5 | 158.0/79 | 52.53 [48.73,56.33] | 3.80 [0.00,8.86] | 43.67 [39.87,46.84] | 5.06 [1.27,10.13] | 5.06 [1.27,10.13] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/DSRE_risk | delay5 | 158.0/79 | 68.99 [62.66,74.68] | 3.80 [0.00,8.86] | 27.22 [21.52,32.28] | 3.80 [0.00,8.86] | 5.06 [1.27,10.13] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B7_risk | delay5 | 158.0/79 | 68.99 [62.66,74.68] | 3.80 [0.00,8.86] | 27.22 [21.52,32.28] | 3.80 [0.00,8.86] | 5.06 [1.27,10.13] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B5_beta10 | delay5 | 158.0/79 | 69.62 [64.56,74.68] | 3.16 [0.63,6.33] | 27.22 [21.52,32.28] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/CART2_beta10 | delay5 | 158.0/79 | 63.92 [56.33,71.52] | 8.86 [3.80,14.56] | 27.22 [21.52,32.28] | 8.86 [3.80,14.56] | 10.13 [5.06,15.82] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_continue | delay5 | 158.0/79 | 69.62 [64.56,74.68] | 30.38 [25.32,35.44] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |
| NEW_159_SECONDARY_SHIFT_SENSITIVITY | PickCube-v1/B0_recover | delay5 | 158.0/79 | 65.82 [55.70,75.95] | 34.18 [24.05,44.30] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] |

Full17-method, both-mode, threshold-proximity and separate replicate results are in historical_robustness.json/heldout_robustness.json and their referenced prediction records. Action instability uses the action appropriate to the mode; certificate instability concerns proposed facts. Noise families aggregate all three exact registered replicates, never a favorable one. Empty proximity subgroups are NOT ESTIMABLE. Proposals/gates do not change physical outcomes or controller input streams.

## Grounded insufficiency and adequacy examples

- Case A: `PickCube-v1/102571/offset002`, source `results/recovery-claims/20261112T152155Z/parents/confirmation/PickCube-v1/102571-offset002/traces.json.gz`, SHA256 `e9693d3d09deef3a895815fc0052c8d212381549fd6ebe7e9c9240ae69c9b173`; paired outcomes {'continue_value': False, 'recover_value': True}.
- Case B: `PickCube-v1/102892/offset002`, source `results/recovery-claims/20261112T152155Z/parents/confirmation/PickCube-v1/102892-offset002/traces.json.gz`, SHA256 `762f24667f89272a104f86c1262937649b5a88feda453bdc1d13a591dc395b9a`; paired outcomes {'continue_value': False, 'recover_value': False}.
- Case C: `PickCube-v1/100098/nominal`, source `results/recovery-claims/20261112T152155Z/parents/confirmation/PickCube-v1/100098-nominal/traces.json.gz`, SHA256 `38bc3d238601d799e486307a5ce5a2686050a409da00669e529fcdf237617b6e`; paired outcomes {'continue_value': True, 'recover_value': True}.
- Case D: `PushCube-v1/103984/nominal`, source `results/recovery-claims/20261112T152155Z/parents/confirmation/PushCube-v1/103984-nominal/traces.json.gz`, SHA256 `d837739879520065e090774fd4898b477d44a8c3bacbb4c185a10fc1e6182809`; paired outcomes {'continue_value': False, 'recover_value': True}.
- Case E: `PushCube-v1/105544/nominal`, source `results/recovery-claims/20261112T152155Z/parents/confirmation/PushCube-v1/105544-nominal/traces.json.gz`, SHA256 `05820216448c1a3590ed03401073badb9bc826c39ed98815d3e4b2ff72b9f822`; paired outcomes {'continue_value': True, 'recover_value': False}.
- Case F: `PickCube-v1/103839/offset002`, source `results/recovery-claims/20261112T152155Z/parents/confirmation/PickCube-v1/103839-offset002/traces.json.gz`, SHA256 `a309921e2e2f00b1df0b77f6f41d313e92758439aa5dc0110700c45ace4232d4`; paired outcomes {'continue_value': False, 'recover_value': False}. Reference insufficiency and repertoire inadequacy may both apply; neither is exclusive.
- Case G: `PickCube-v1/101735/offset002`, source `results/recovery-claims/20261112T152155Z/parents/confirmation/PickCube-v1/101735-offset002/traces.json.gz`, SHA256 `7478dbc849c910db38e1e25cca63d1fc7fe1819946b9365d2b8543df42e11c1a`; paired outcomes {'continue_value': False, 'recover_value': True}. The supported broader pure rule acts despite unseen exact signature and is physically inadequate. This is NOT labeled an emitted reference-insufficiency obstruction; finite support diagnostics cannot detect every unrepresented adverse state.

A/B share six facts and differ in the registered left-of-goal predicate; B remains neither-success. C is both-success and initially successful. D/E share all 12 facts with opposing adequate actions: the existing Boolean menu cannot separate them, while raw poses differ. F has only one independent compatible parent under the registered full 12-fact scope and also neither-success: support and repertoire obstructions overlap. G has no exact signature in an original inspected cross-fit reference, yet a supported broader pure rule chooses inadequate continue. G is not mislabeled as an emitted reference-insufficiency obstruction. Finite diagnostics cannot discover every unrepresented adverse state. No extra controller, predicate, failure condition or hypothesis is introduced.

The preserved finite frontier remains Pick183->235/422 at one added predicate, all six248/422; Push0through all budgets. These full-reference masses differ from held-out success. The old333-parent result remains145->187/332 strict Pick successes, mostly maintenance and only one extra required recovery. No historical result is overwritten.

## Optional third task

Read-only source assessment finds no additional already registered pair of semantically distinct, source-replayable recovery actions with the unchanged horizon/objective and qualified full-prefix/controller state. Installed nominal task solvers do not supply that paired protocol. Existing Lift/Panda only clips nominal speed and its retained210starts are both-success; it cannot be relabeled recovery validation. Creating a skill, fault, pipeline or selecting another task by DSRE gains is forbidden. The optional arm stops before any new third-task physics; external validity remains two scripted simulator tasks.

Inventory time: 0.07s (<=60min). New third-task physics: 0s. Source inventory/hashes are in breadth_feasibility.json. No task selected for favorable DSRE performance, new controller or invented failure.
