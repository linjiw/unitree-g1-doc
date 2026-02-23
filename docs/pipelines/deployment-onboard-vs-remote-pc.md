# Policy Deployment: Onboard vs Remote PC

## Decision Summary

- Default to **remote PC inference** for early G1 policy deployment.
- Move to **onboard inference** only after proving timing and thermal headroom.

## Comparison

| Dimension | Onboard Inference | Remote PC Inference |
| --- | --- | --- |
| Compute budget | Strict | High |
| Integration complexity | Lower network complexity | Higher network + ops complexity |
| Iteration speed | Slower for large models | Faster model iteration |
| Failure surface | Thermal and frame-drop risk | Network latency/drop risk |
| Recommended first step | No (unless model is lightweight) | Yes |

## Remote PC Pipeline

1. Run policy inference on a workstation GPU.
2. Use Unitree SDK2/DDS channel for command/telemetry exchange.
3. Keep control safety gates local and deterministic.
4. Pin network interfaces and monitor RTT/jitter continuously.

## Onboard Pipeline

1. Reduce model size and runtime cost (export/prune/optimize).
2. Confirm stable control loop frequency under full sensor workload.
3. Add watchdog fallback to a conservative controller.
4. Run extended thermal and long-horizon drift tests.

## Validation Gate Before Production

1. 10+ repeated trials with no emergency stop trigger.
2. Stable command tracking under scripted disturbance tests.
3. Reproducible startup and recovery procedure documented in ops notes.
