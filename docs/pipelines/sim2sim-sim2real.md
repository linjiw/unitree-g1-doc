# G1 Sim2Sim and Sim2Real Workflow

This workflow is the default for Unitree G1 policy development using official Unitree RL repositories.

## Stage 1: Build in Simulation

1. Use `unitree_rl_lab` as the primary training/deployment framework for G1.
2. Keep task and robot configs versioned beside checkpoints.
3. Record reward settings, command ranges, and observation normalization with each run.

## Stage 2: Sim2Sim Validation

1. Replay checkpoints in the same framework with `--play` to validate behavior.
2. Validate in an additional simulator path when needed:
   - `unitree_mujoco` for fast dynamics checks.
   - `unitree_sim_isaaclab` when matching IsaacLab stacks.
3. Track failure modes before hardware transfer:
   - falls after command transitions
   - unstable yaw control
   - contact-sensitive oscillation

## Stage 3: Sim2Real Bring-Up

1. Start with conservative command envelopes and stop conditions.
2. Verify DDS/SDK communication path first, then policy loop timing.
3. Promote from tethered tests to full commands only after repeatable stability.

## Current Practical Constraint

`unitree_rl_lab` guidance indicates G1 3.0 may be compute-limited for direct onboard deployment of heavy learned policies, and recommends remote high-performance PC deployment in that case.

Use this as the default path until onboard latency and thermal budgets are proven for your model size and runtime.

## Related

- [deployment-onboard-vs-remote-pc.md](/Users/linji/projects/unitree-g1-doc/docs/pipelines/deployment-onboard-vs-remote-pc.md)
- [unitree_rl_lab.md](/Users/linji/projects/unitree-g1-doc/docs/source-digests/unitree_rl_lab.md)
