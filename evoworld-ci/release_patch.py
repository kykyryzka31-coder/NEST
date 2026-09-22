from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
p = root / "main.gd"
s = p.read_text(encoding="utf-8")

# EvoWorld 1.2 core balance.
def replace_once(old: str, new: str) -> None:
    global s
    if old in s:
        s = s.replace(old, new, 1)

replace_once("const PERCEPTION_RADIUS := 20.0", "const PERCEPTION_RADIUS := 26.0")
replace_once("const SOCIAL_RADIUS := 8.0", "const SOCIAL_RADIUS := 10.0")
replace_once(
    '    for i in range(42):\n        _create_resource("food", 0.0, rng.randf_range(0.46, 0.68))',
    '    for i in range(60):\n        _create_resource("food", 0.0, rng.randf_range(0.46, 0.68))',
)
replace_once(
    '    for i in range(14):\n        _create_resource("water", 0.0, 0.9)',
    '    for i in range(20):\n        _create_resource("water", 0.0, 0.9)',
)
replace_once(
"""    if speed > 0.0:
        var remaining: float = delta * speed
        while remaining > 0.00001:
            var step: float = minf(0.15, remaining)
            sim_time += step
            _simulate_step(step)
            remaining -= step
""",
"""    if speed > 0.0:
        var remaining: float = delta * speed
        var max_step: float = 0.15
        if speed >= 50.0:
            max_step = 0.85
        elif speed >= 20.0:
            max_step = 0.45
        elif speed >= 5.0:
            max_step = 0.25
        while remaining > 0.00001:
            var step: float = minf(max_step, remaining)
            sim_time += step
            _simulate_step(step)
            remaining -= step
""",
)
replace_once(
"""    a["age"] = float(a["age"]) + dt / YEAR_SECONDS
    a["hunger"] = clampf(float(a["hunger"]) + dt * 0.00255 * metabolism, 0.0, 1.0)
    a["thirst"] = clampf(float(a["thirst"]) + dt * 0.00385 * metabolism, 0.0, 1.0)
    a["fatigue"] = clampf(float(a["fatigue"]) + dt * 0.0016, 0.0, 1.0)
""",
"""    a["age"] = float(a["age"]) + dt / YEAR_SECONDS
    var age_factor = 0.72 if float(a["age"]) < 14.0 else 1.0
    var culture_factor = 0.92 if int(a["culture_id"]) >= 0 else 1.0
    var storage_factor = 0.88 if a["techniques"].has("storage") else 1.0
    a["hunger"] = clampf(float(a["hunger"]) + dt * 0.00185 * metabolism * age_factor * culture_factor * storage_factor, 0.0, 1.0)
    a["thirst"] = clampf(float(a["thirst"]) + dt * 0.00265 * metabolism * age_factor, 0.0, 1.0)
    a["fatigue"] = clampf(float(a["fatigue"]) + dt * 0.00135, 0.0, 1.0)
""",
)
replace_once(
"""    if float(a["hunger"]) > 0.96:
        a["health"] = float(a["health"]) - dt * 0.0029
    if float(a["thirst"]) > 0.96:
        a["health"] = float(a["health"]) - dt * 0.0055
    if float(a["cold_stress"]) > 0.62:
        a["health"] = float(a["health"]) - dt * 0.0017 * float(a["cold_stress"])
""",
"""    if float(a["hunger"]) > 0.985:
        a["health"] = float(a["health"]) - dt * 0.0018
    if float(a["thirst"]) > 0.985:
        a["health"] = float(a["health"]) - dt * 0.0032
    if float(a["cold_stress"]) > 0.78:
        a["health"] = float(a["health"]) - dt * 0.0010 * float(a["cold_stress"])
""",
)
replace_once(
    '        r["respawn_at"] = sim_time + (32.0 if kind in ["food", "water"] else 110.0)',
    '        r["respawn_at"] = sim_time + (18.0 if kind == "food" else (10.0 if kind == "water" else 110.0))',
)
replace_once('    if sim_time - float(a["last_birth"]) < YEAR_SECONDS * 1.8:', '    if sim_time - float(a["last_birth"]) < YEAR_SECONDS * 1.25:')
replace_once(
    '    if float(a["health"]) < 0.70 or float(a["hunger"]) > 0.68 or float(a["thirst"]) > 0.68:',
    '    if float(a["health"]) < 0.60 or float(a["hunger"]) > 0.78 or float(a["thirst"]) > 0.78:',
)
replace_once(
    '    var chance = (0.08 + fertility * 0.16 + social * 0.06) * crowd_factor',
    '    var chance = (0.14 + fertility * 0.22 + social * 0.08) * crowd_factor',
)

# EvoWorld 1.2 family cohesion and culture-centered movement.
replace_once(
"""    var hunt_score = 0.0
    if a["techniques"].has("spear") or a["techniques"].has("bow"):
        hunt_score = float(a["hunger"]) * 0.58 + float(a["aggression"]) * 0.16
""",
"""    var hunt_score = 0.0
    if a["techniques"].has("spear") or a["techniques"].has("bow"):
        hunt_score = float(a["hunger"]) * 0.58 + float(a["aggression"]) * 0.16
    var family_score = 0.0
    if float(a["age"]) < 12.0 and float(a["hunger"]) < 0.72 and float(a["thirst"]) < 0.72:
        family_score = 0.70 + float(a["sociability"]) * 0.18
""",
)
replace_once(
"""    if hunt_score > best:
        action = "Охотится"
""",
"""    if hunt_score > best:
        best = hunt_score
        action = "Охотится"
    if family_score > best:
        action = "Следует за семьёй"
""",
)
replace_once(
"""    elif action == "Экспериментирует":
        var material = _nearest_material(a)
        a["target"] = (material["node"] as Node3D).position if material != null else _random_near(a, 9.0)
    else:
        a["target"] = _random_near(a, 12.0)
""",
"""    elif action == "Экспериментирует":
        var material = _nearest_material(a)
        a["target"] = (material["node"] as Node3D).position if material != null else _random_near(a, 9.0)
    elif action == "Следует за семьёй":
        var parent: Variant = _agent_by_id(int(a["mother_id"]))
        if parent == null:
            parent = _agent_by_id(int(a["father_id"]))
        a["target"] = (parent["root"] as Node3D).position if parent != null else _random_near(a, 7.0)
    else:
        var culture: Variant = _culture_by_id(int(a["culture_id"]))
        if culture != null and rng.randf() < 0.62:
            var center: Vector3 = culture["center"]
            a["target"] = _clamp_world(center + Vector3(rng.randf_range(-9.0, 9.0), 0.0, rng.randf_range(-9.0, 9.0)))
        else:
            a["target"] = _random_near(a, 12.0)
""",
)

# Explicit nullable return types for Godot 4.7.
for old, new in {
    "func _best_matching_culture(center: Vector3, dialect: float):": "func _best_matching_culture(center: Vector3, dialect: float) -> Variant:",
    "func _culture_by_id(culture_id: int):": "func _culture_by_id(culture_id: int) -> Variant:",
    "func _structure_by_id(sid: int):": "func _structure_by_id(sid: int) -> Variant:",
    "func _agent_by_id(agent_id: int):": "func _agent_by_id(agent_id: int) -> Variant:",
    "func _nearest_agent(a: Dictionary, radius: float):": "func _nearest_agent(a: Dictionary, radius: float) -> Variant:",
    "func _nearest_material(a: Dictionary):": "func _nearest_material(a: Dictionary) -> Variant:",
}.items():
    s = s.replace(old, new)
s = s.replace("    var best = null\n", "    var best: Variant = null\n")

# Farming and irrigation create a real local food surplus.
replace_once("        var farming_count = 0\n        var masonry_count = 0", "        var farming_count = 0\n        var irrigation_count = 0\n        var masonry_count = 0")
replace_once(
"""            if a["techniques"].has("farming"):
                farming_count += 1
            if a["techniques"].has("masonry"):
""",
"""            if a["techniques"].has("farming"):
                farming_count += 1
            if a["techniques"].has("irrigation"):
                irrigation_count += 1
            if a["techniques"].has("masonry"):
""",
)
replace_once(
"""                _upgrade_settlement(settlement, culture, farming_count, masonry_count)

func _create_settlement(culture: Dictionary, has_fire: bool) -> Dictionary:
""",
"""                _upgrade_settlement(settlement, culture, farming_count, masonry_count)
                _support_settlement_food(settlement, farming_count, irrigation_count)

func _support_settlement_food(settlement: Dictionary, farming_count: int, irrigation_count: int) -> void:
    if farming_count < 2:
        return
    var center = (settlement["node"] as Node3D).position
    var nearby_food = 0
    var target_food = 6 + mini(4, irrigation_count)
    for i in range(resources.size()):
        var r: Dictionary = resources[i]
        if String(r["kind"]) != "food":
            continue
        if center.distance_to((r["node"] as Node3D).position) > 12.0:
            continue
        nearby_food += 1
        if float(r["amount"]) <= 0.05:
            r["respawn_at"] = minf(float(r["respawn_at"]), sim_time + (6.0 if irrigation_count > 0 else 10.0)) if float(r["respawn_at"]) >= 0.0 else sim_time + 10.0
            resources[i] = r
    while nearby_food < target_food and resources.size() < 220:
        _create_resource("food", 0.0, rng.randf_range(0.48, 0.66), _clamp_world(center + Vector3(rng.randf_range(-10.0, 10.0), 0.0, rng.randf_range(-10.0, 10.0))))
        nearby_food += 1

func _create_settlement(culture: Dictionary, has_fire: bool) -> Dictionary:
""",
)

# EvoWorld 1.2 persistence fixes.
deserialize_memory = """func _deserialize_memory(raw: Dictionary) -> Dictionary:
    var out = {}
    for key in raw.keys():
        var k: Dictionary = raw[key]
        var p: Array = k["pos"]
        out[int(key)] = {
            "kind": k["kind"], "pos": Vector3(float(p[0]), float(p[1]), float(p[2])),
            "value": float(k["value"]), "danger": float(k["danger"]), "confidence": float(k["confidence"])
        }
    return out
"""
if "func _deserialize_trust" not in s:
    replace_once(
        deserialize_memory,
        deserialize_memory + """
func _deserialize_trust(raw: Dictionary) -> Dictionary:
    var out = {}
    for key in raw.keys():
        out[int(key)] = float(raw[key])
    return out
""",
    )

replace_once(
"""        "cold_snap_until": cold_snap_until, "heat_wave_until": heat_wave_until,
        "global_discoveries": global_discoveries, "relations": relations, "history": history,
""",
"""        "cold_snap_until": cold_snap_until, "heat_wave_until": heat_wave_until,
        "lightning_bonus_until": lightning_bonus_until, "lightning_position": [lightning_position.x, lightning_position.y, lightning_position.z],
        "global_discoveries": global_discoveries, "relations": relations, "history": history,
""",
)
replace_once(
"""    cold_snap_until = float(data.get("cold_snap_until", -1.0))
    heat_wave_until = float(data.get("heat_wave_until", -1.0))
    global_discoveries = data.get("global_discoveries", {})
""",
"""    cold_snap_until = float(data.get("cold_snap_until", -1.0))
    heat_wave_until = float(data.get("heat_wave_until", -1.0))
    lightning_bonus_until = float(data.get("lightning_bonus_until", -1.0))
    var lightning_raw: Array = data.get("lightning_position", [0.0, 0.0, 0.0])
    lightning_position = Vector3(float(lightning_raw[0]), float(lightning_raw[1]), float(lightning_raw[2]))
    global_discoveries = data.get("global_discoveries", {})
""",
)
s = s.replace('agent["trust"] = raw.get("trust", {})', 'agent["trust"] = _deserialize_trust(raw.get("trust", {}))')

new_func = r'''func _update_cultures() -> void:
    if agents.size() < 5:
        return
    var unassigned: Array[int] = []
    var lookup: Dictionary = {}
    for a in agents:
        var aid = int(a["id"])
        unassigned.append(aid)
        lookup[aid] = a
    var components: Array = []

    while not unassigned.is_empty():
        var start_id = int(unassigned.pop_front())
        var start_agent = lookup.get(start_id)
        if start_agent == null:
            continue
        var component: Array = [start_agent]
        var queue: Array = [start_agent]
        while not queue.is_empty():
            var current: Dictionary = queue.pop_front()
            var current_pos = (current["root"] as Node3D).position
            var current_dialect = float(current["dialect"])
            var joined_ids: Array[int] = []
            for other_id in unassigned:
                var other = lookup.get(other_id)
                if other == null:
                    continue
                var other_pos = (other["root"] as Node3D).position
                if current_pos.distance_to(other_pos) <= 12.5 and absf(current_dialect - float(other["dialect"])) <= 0.25:
                    component.append(other)
                    queue.append(other)
                    joined_ids.append(other_id)
            for joined_id in joined_ids:
                unassigned.erase(joined_id)
        if component.size() >= 5:
            components.append(component)

    var active_ids: Array[int] = []
    for component in components:
        var centroid = Vector3.ZERO
        var dialect = 0.0
        var existing_counts: Dictionary = {}
        for member in component:
            centroid += (member["root"] as Node3D).position
            dialect += float(member["dialect"])
            var old_id = int(member["culture_id"])
            if old_id >= 0:
                existing_counts[old_id] = int(existing_counts.get(old_id, 0)) + 1
        centroid /= float(component.size())
        dialect /= float(component.size())

        var culture: Variant = null
        var majority_id = -1
        var majority_count = 0
        for old_cid in existing_counts.keys():
            var count = int(existing_counts[old_cid])
            if count > majority_count:
                majority_count = count
                majority_id = int(old_cid)
        var continuity_needed = maxi(2, int(ceil(float(component.size()) * 0.35)))
        if majority_id >= 0 and majority_count >= continuity_needed:
            culture = _culture_by_id(majority_id)
        if culture == null:
            culture = _best_matching_culture(centroid, dialect)
        if culture == null and component.size() >= 6:
            culture = _create_culture(centroid, dialect)
        if culture == null:
            continue

        culture["center"] = centroid
        culture["dialect"] = lerpf(float(culture["dialect"]), dialect, 0.18)
        culture["population"] = component.size()
        culture["leader_id"] = _choose_leader(component)
        var new_cid = int(culture["id"])
        if not active_ids.has(new_cid):
            active_ids.append(new_cid)
        for member in component:
            member["culture_id"] = new_cid
            _update_agent_visual(member)

    for culture in cultures:
        if not active_ids.has(int(culture["id"])):
            culture["population"] = 0

'''

s, n = re.subn(r'func _update_cultures\(\) -> void:\n.*?(?=func _best_matching_culture)', new_func, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit("culture patch did not match")

p.write_text(s, encoding="utf-8")

project = root / "project.godot"
ps = project.read_text(encoding="utf-8")
ps = re.sub(r'config/version="[^"]+"', 'config/version="1.2.1"', ps)
if 'config/icon=' not in ps:
    ps = ps.replace('config/version="1.2.1"\n', 'config/version="1.2.1"\nconfig/icon="res://icon.svg"\n')
project.write_text(ps, encoding="utf-8")

(root / "icon.svg").write_text("""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><rect width="512" height="512" rx="104" fill="#0b1518"/><circle cx="256" cy="262" r="174" fill="#255d46"/><path d="M120 292C170 184 232 142 292 160c40 12 76 48 100 99-44-18-83-14-116 11 49 4 85 27 112 69-55-24-107-29-153-13-43 15-82 3-115-34z" fill="#8fd3a9"/><path d="M231 297l35-87 35 87-35 61z" fill="#f19b4b"/><circle cx="266" cy="200" r="18" fill="#ffd166"/></svg>""", encoding="utf-8")

preset = root / "export_presets.cfg"
es = preset.read_text(encoding="utf-8")
es = re.sub(r'version/code=\d+', 'version/code=6', es)
es = re.sub(r'version/name="[^"]+"', 'version/name="1.2.1"', es)
preset.write_text(es, encoding="utf-8")
