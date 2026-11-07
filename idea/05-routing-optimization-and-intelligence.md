# 05 — Routing, departure optimization, fleet planning and ML

**Status:** design hypothesis; solver performance and accuracy require measurement.

## Four different engines, not one black box

| Engine | Primary task | Candidate implementation |
|---|---|---|
| Road Routing | Road-feasible path between waypoints | Valhalla / HERE / PTV / local provider; adapter-based |
| Schedule and Departure | Best departure time, appointment and stops | Deterministic time-dependent evaluation + search over windows |
| Fleet Optimizer | Match orders, vehicles and drivers, select stop sequences | Timefold Solver or OR-Tools |
| Prediction | ETA residuals, fuel, dwell time and incident probability | Java Tribuo, optional after baseline |

A Decision Engine checks feasibility first, ranks cost/service/risk tradeoffs second, and produces human-readable reasons. Timefold is a constraint optimizer, **not** a machine-learning predictor or road data provider.

## Road graph and time

Road segments have length, permitted direction, vehicle constraints, tolls, predicted speed by time and incident/closure intervals. Travel time must be calculated at the estimated arrival time for that segment. The solver must account for turn restrictions and any waiting-policy assumptions.

For FIFO-compliant time-dependent edge costs, time-dependent Dijkstra/A* can apply. Temporary closures, permitted waiting and non-FIFO behavior require explicit treatment; do not assume static Dijkstra is always valid.

Vehicle eligibility: dimensions, total and axle weight, trailer, cargo hazard class, road restrictions, driver rules and facility gates. Unknown restriction data should produce warnings/verification requirements, not silently be treated as safe.

## VRP constraints

Hard:
- one pickup before its paired delivery;
- vehicle gross capacity and compartment constraints, weight/volume and incompatible cargo;
- locked appointments, mandatory stops, minimum fuel reserve;
- driver legal rest/duty intervals according to jurisdiction and service conditions;
- assignment availability and tenant/partner authorization;
- cargo, road and customs compliance.

Soft:
- total expected cost;
- missed service preference / lateness risk within permitted boundaries;
- empty kilometers, waiting, excess detours and number of active vehicles;
- customer preference and partner SLA.

Never turn a legally required hard constraint into a mere penalty.

## Departure-time strategy

1. Generate permissible departure candidates in the contractual planning window (e.g., every 15–30 minutes).
2. For each, fetch or estimate traffic state at arrival times along the path, plus mandatory rest/fueling and facility service durations.
3. Compute total expected cost and ETA uncertainty band.
4. Remove candidates that violate binding deadlines or road/legal rules.
5. Rank the remainder by defined objective (cost subject to reliability threshold, or a Pareto set).
6. Save the chosen source snapshot, quote input version, traffic freshness and route version.

Historical and live traffic are distinct signals. When future predictions are unavailable, use an explicitly calibrated fallback and wider uncertainty.

## Stops and refueling

RouteStop types: PICKUP, DELIVERY, REST, FUEL, CUSTOMS, WAREHOUSE, SERVICE, MANUAL. Each includes location, service duration, earliest/latest arrival, lock state, responsible party, evidence expectation and optional price.

Choose fuel stops only after checking station access for the vehicle, opening/service availability, tank capacity, safety reserve, contracted price, deviation time and payment eligibility. Fuel price alone is not the optimization objective.

## ML introduction

- Baseline: rule-based ETA from routing provider and calibrated fuel norms by vehicle, load and route class.
- Collect immutable feature snapshots **as known at prediction time**, labeled from verified trip facts to prevent future-data leakage.
- Evaluate Tribuo models offline using chronological splits and per-region/vehicle segments; compare against baseline MAE, p90 error, calibration, drift and cold-start behavior.
- A model registry stores version, compatible feature schema, checksum, data window, evaluation, approval and rollback target.
- Store signed/approved serialized models in controlled RustFS/S3 location; verify checksum and runtime compatibility before activation.
- Keep baseline fallback available; do not depend on model download or external inference for booking safety.
- No automatic online retraining into production without review and canary.

## API conceptual contracts

RouteRequest: tenant context (server-supplied), vehicle profile, origin/waypoints, departure window, required stops, constraint set, traffic preference.
RouteCandidate: geometry, distance, ETA range, toll estimate, restrictions/warnings, provider provenance, source time, price inputs.
OptimizationRequest: orders, vehicles, driver availability, costs, stop/service windows, locked assignments, objective weights and deadline.
OptimizationResult: feasible/infeasible, assignments, route plan versions, objective components, conflicts and explanations.

Use async job execution for expensive optimization, with cancellation, deadline, per-tenant budget, deterministic seed where supported and result versioning.

## Proof of usefulness

Compare 50–100 historical completed trips and prospective pilot results against dispatcher decisions with comparable constraints; measure feasibility, cost, empty distance, lateness, runtime and quality of explanations. Test stale traffic, closures, no viable route, missing vehicle restrictions, inconsistent provider estimates, solver timeout and fallback.

## Cargo compatibility as a hard constraint

Fleet optimizer must query `CargoCompatibilityPort` for every candidate vehicle/compartment, planned co-load, ordered stop timeline and route jurisdiction. Rules are mode- and time-aware and stored in `CompatibilityAssessment` snapshots. A solver cannot lower a hard legal or hygiene prohibition into a soft optimization penalty. Tribuo predicts risks, not compliance permissions. See [18 — Cargo Classification & Compatibility](18-cargo-classification-and-compatibility.md).

## Vehicle capacity as a multidimensional hard constraint

Routing and Timefold candidate eligibility must use actual capacity of assigned vehicle combination, not marketing class: available payload, volumetric/geometry fit, pallet placements, loading opening, permitted axle and gross weight by route, driver/equipment and tank/refrigerator certifications. CargoCompatibilityPort and VehicleCapabilityPort both gate assignment. A solver may optimize after hard feasibility is established. See [20 — Vehicle Classification & Capacity](20-vehicle-classification-capacity-and-special-equipment.md).
