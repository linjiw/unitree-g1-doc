# Retrieval Evaluation

- Total cases: 18
- Passed: 6
- Pass rate: 33.33%
- Top-K: 8
- Threshold: 70%

| Case | Pass | Reason |
| --- | --- | --- |
| codex_goal_statement | False | no expected path pattern found in top-k |
| codex_answer_contract | False | no expected path pattern found in top-k |
| codex_source_priority | True | matched pattern `skills/unitree-g1-expert/SKILL.md` at rank 1 |
| codex_refresh_pipeline | False | no expected path pattern found in top-k |
| codex_query_interface_json | False | no expected path pattern found in top-k |
| codex_repo_lock_builder | False | no expected path pattern found in top-k |
| codex_coverage_and_blocking | True | matched pattern `docs/verification/g1_docs_verification.md` at rank 1 |
| codex_support_manifest_mapping | False | no expected path pattern found in top-k |
| codex_deployment_remote_first | True | matched pattern `docs/pipelines/deployment-onboard-vs-remote-pc.md` at rank 1 |
| codex_sim2real_stages | True | matched pattern `docs/pipelines/sim2sim-sim2real.md` at rank 5 |
| codex_sdk2_python_install | True | matched pattern `docs/source-digests/unitree_sdk2_python.md` at rank 1 |
| codex_ros2_lowlevel_example | True | matched pattern `data/repos/unitree_ros2/README.md` at rank 1 |
| codex_eval_thresholds | False | no expected path pattern found in top-k |
| codex_question_bank_pipeline | False | no expected path pattern found in top-k |
| codex_stretch_experiment_doc | False | no expected path pattern found in top-k |
| codex_site_method_pages | False | no expected path pattern found in top-k |
| codex_site_example_payload | False | no expected path pattern found in top-k |
| codex_repo_catalog_scope | False | no expected path pattern found in top-k |
