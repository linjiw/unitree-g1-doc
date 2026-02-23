# Workflow Reference

## Standard Answer Loop

1. Run local retrieval first.
   - Prefer `python3 scripts/query_index.py "<question>" --format json`.
2. Open top-matched records.
3. Identify whether question is about:
   - SDK and DDS interfaces
   - motion/control example usage
   - RL sim2sim/sim2real
   - deployment pipeline
4. Produce:
   - direct answer
   - exact citations (local path + upstream URL)
   - explicit next command when action is required
   - `Verified` versus `Inference` labels for each major claim

## Troubleshooting Flow

1. Communication issue:
   - inspect SDK2 and ROS2 digests
   - verify network interface expectations
2. Policy transfer issue:
   - inspect RL digests and sim2real pipeline doc
   - separate simulator failures from hardware integration failures
3. Deployment performance issue:
   - compare onboard vs remote-PC pipeline
   - classify as compute-bound, network-bound, or control-loop-bound
