# Retrieval Evaluation

- Total cases: 12
- Passed: 11
- Pass rate: 91.67%
- Top-K: 8
- Threshold: 75%

| Case | Pass | Reason |
| --- | --- | --- |
| remote_pc_deployment | True | matched pattern `docs/pipelines/deployment-onboard-vs-remote-pc.md` at rank 1 |
| sim2real_workflow | True | matched pattern `docs/pipelines/sim2sim-sim2real.md` at rank 1 |
| sdk2_python_requirements | True | matched pattern `data/repos/unitree_sdk2_python/README.md` at rank 1 |
| ros2_g1_lowlevel | True | matched pattern `data/repos/unitree_ros2/README.md` at rank 1 |
| sdk2_g1_examples | False | no expected path pattern found in top-k |
| mujoco_bridge | True | matched pattern `data/repos/unitree_mujoco/readme.md` at rank 1 |
| isaaclab_repo | True | matched pattern `data/repos/unitree_sim_isaaclab/README.md` at rank 3 |
| ros2_to_real | True | matched pattern `docs/source-digests/unitree_ros2_to_real.md` at rank 1 |
| repo_coverage_report | True | matched pattern `docs/verification/coverage_report.md` at rank 4 |
| doc_blocking_status | True | matched pattern `docs/verification/g1_docs_verification.md` at rank 1 |
| max_collect_command | True | matched pattern `README.md` at rank 3 |
| skill_guidance | True | matched pattern `skills/unitree-g1-expert/SKILL.md` at rank 1 |
