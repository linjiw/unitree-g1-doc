# Retrieval Evaluation

- Total cases: 12
- Passed: 9
- Pass rate: 75.00%
- Top-K: 8
- Threshold: 75%

| Case | Pass | Reason |
| --- | --- | --- |
| remote_pc_deployment | True | matched pattern `docs/pipelines/deployment-onboard-vs-remote-pc.md` at rank 2 |
| sim2real_workflow | True | matched pattern `docs/pipelines/sim2sim-sim2real.md` at rank 1 |
| sdk2_python_requirements | True | matched pattern `data/repos/unitree_sdk2_python/README.md` at rank 1 |
| ros2_g1_lowlevel | True | matched pattern `data/repos/unitree_ros2/README.md` at rank 1 |
| sdk2_g1_examples | False | no expected path pattern found in top-k |
| mujoco_bridge | True | matched pattern `data/repos/unitree_mujoco/readme.md` at rank 3 |
| isaaclab_repo | False | no expected path pattern found in top-k |
| ros2_to_real | False | no expected path pattern found in top-k |
| repo_coverage_report | True | matched pattern `docs/verification/coverage_report.md` at rank 7 |
| doc_blocking_status | True | matched pattern `docs/verification/g1_docs_verification.md` at rank 6 |
| max_collect_command | True | matched pattern `scripts/max_collect.sh` at rank 2 |
| skill_guidance | True | matched pattern `skills/unitree-g1-expert/SKILL.md` at rank 1 |
