# Agent Source-Selection Evaluation

- Total cases: 12
- Passed: 10
- Pass rate: 83.33%
- Avg precision: 37.50%
- Avg recall: 62.50%
- Model: `llama3.1`
- API base: `http://127.0.0.1:11434/v1`

| Case | Pass | Precision | Recall |
| --- | --- | --- | --- |
| remote_pc_deployment | True | 0.67 | 1.00 |
| sim2real_workflow | True | 0.50 | 0.50 |
| sdk2_python_requirements | True | 0.67 | 1.00 |
| ros2_g1_lowlevel | True | 0.33 | 1.00 |
| sdk2_g1_examples | False | 0.00 | 0.00 |
| mujoco_bridge | True | 0.33 | 1.00 |
| isaaclab_repo | True | 0.33 | 0.50 |
| ros2_to_real | True | 0.67 | 1.00 |
| repo_coverage_report | False | 0.00 | 0.00 |
| doc_blocking_status | True | 0.33 | 0.50 |
| max_collect_command | True | 0.33 | 0.50 |
| skill_guidance | True | 0.33 | 0.50 |
