from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
p = root / "main.gd"
s = p.read_text(encoding="utf-8")

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
ps = project.read_text(encoding="utf-8").replace('config/version="1.2.0"', 'config/version="1.2.1"')
project.write_text(ps, encoding="utf-8")

preset = root / "export_presets.cfg"
es = preset.read_text(encoding="utf-8").replace("version/code=5", "version/code=6").replace('version/name="1.2.0"', 'version/name="1.2.1"')
preset.write_text(es, encoding="utf-8")


# EvoWorld 1.3 wildlife ecosystem
s = p.read_text(encoding="utf-8")

s = s.replace(
    "var next_resource_update = 0.0\n",
    "var next_resource_update = 0.0\nvar wildlife: Array = []\nvar next_wildlife_id = 1\n",
)

s = s.replace(
    "    resources.clear()\n",
    "    resources.clear()\n    wildlife.clear()\n",
)
s = s.replace(
    "    next_resource_id = 1\n",
    "    next_resource_id = 1\n    next_wildlife_id = 1\n",
)

s = s.replace(
    "    _spawn_wildlife_decor()\n    next_culture_update = 15.0\n",
    "    _spawn_wildlife_decor()\n    _spawn_wildlife()\n    next_culture_update = 15.0\n",
)

wildlife_funcs = r'''
func _spawn_wildlife() -> void:
    for i in range(24):
        _spawn_animal("deer", Vector3(rng.randf_range(-WORLD_HALF + 4.0, WORLD_HALF - 4.0), 0.0, rng.randf_range(-WORLD_HALF + 4.0, WORLD_HALF - 4.0)))
    for i in range(7):
        _spawn_animal("wolf", Vector3(rng.randf_range(-WORLD_HALF + 4.0, WORLD_HALF - 4.0), 0.0, rng.randf_range(-WORLD_HALF + 4.0, WORLD_HALF - 4.0)))

func _spawn_animal(kind: String, pos: Vector3, starting_age: float = -1.0) -> Dictionary:
    var root = Node3D.new()
    root.position = _clamp_world(pos)
    world_root.add_child(root)

    var body = MeshInstance3D.new()
    var mesh = CapsuleMesh.new()
    mesh.radius = 0.28 if kind == "deer" else 0.30
    mesh.height = 0.90 if kind == "deer" else 0.72
    body.mesh = mesh
    body.position.y = 0.44 if kind == "deer" else 0.36
    var mat = StandardMaterial3D.new()
    mat.albedo_color = Color(0.50, 0.30, 0.13) if kind == "deer" else Color(0.34, 0.37, 0.41)
    body.material_override = mat
    root.add_child(body)

    var age = starting_age if starting_age >= 0.0 else rng.randf_range(1.0, 8.0)
    var animal = {
        "id": next_wildlife_id,
        "kind": kind,
        "root": root,
        "health": 1.0,
        "hunger": rng.randf_range(0.0, 0.35),
        "age": age,
        "lifespan": rng.randf_range(13.0, 19.0) if kind == "deer" else rng.randf_range(10.0, 16.0),
        "target": root.position,
        "next_think": sim_time + rng.randf_range(0.2, 2.2),
        "last_birth": -999999.0
    }
    next_wildlife_id += 1
    wildlife.append(animal)
    return animal

func _wildlife_by_id(wid: int) -> Variant:
    for animal in wildlife:
        if int(animal["id"]) == wid:
            return animal
    return null

func _count_wildlife(kind: String) -> int:
    var count = 0
    for animal in wildlife:
        if String(animal["kind"]) == kind:
            count += 1
    return count

func _nearest_wildlife(pos: Vector3, kind: String, radius: float) -> Variant:
    var best: Variant = null
    var best_dist = radius
    for animal in wildlife:
        if String(animal["kind"]) != kind or float(animal["health"]) <= 0.0:
            continue
        var dist = pos.distance_to((animal["root"] as Node3D).position)
        if dist < best_dist:
            best_dist = dist
            best = animal
    return best

func _nearest_food_resource(pos: Vector3, radius: float) -> Variant:
    var best: Variant = null
    var best_dist = radius
    for r in resources:
        if String(r["kind"]) != "food" or float(r["amount"]) <= 0.05 or float(r["danger"]) > 0.25:
            continue
        var dist = pos.distance_to((r["node"] as Node3D).position)
        if dist < best_dist:
            best_dist = dist
            best = r
    return best

func _update_wildlife(dt: float) -> void:
    for i in range(wildlife.size() - 1, -1, -1):
        var animal: Dictionary = wildlife[i]
        animal["age"] = float(animal["age"]) + dt / YEAR_SECONDS
        animal["hunger"] = clampf(float(animal["hunger"]) + dt * (0.0010 if String(animal["kind"]) == "deer" else 0.00145), 0.0, 1.0)

        if float(animal["health"]) <= 0.0 or float(animal["age"]) > float(animal["lifespan"]):
            _remove_wildlife_at(i, true)
            continue

        if float(animal["hunger"]) > 0.985:
            animal["health"] = float(animal["health"]) - dt * 0.0015

        if sim_time >= float(animal["next_think"]):
            _wildlife_think(animal)
            animal["next_think"] = sim_time + rng.randf_range(1.0, 3.0)

        var root = animal["root"] as Node3D
        var target: Vector3 = animal["target"]
        var delta = target - root.position
        delta.y = 0.0
        if delta.length_squared() > 0.05:
            var speed_value = 1.75 if String(animal["kind"]) == "deer" else 2.15
            var amount = minf(delta.length(), speed_value * dt)
            var dir = delta.normalized()
            root.position += dir * amount
            root.position = _clamp_world(root.position)
            root.rotation.y = atan2(dir.x, dir.z)
        wildlife[i] = animal

func _wildlife_think(animal: Dictionary) -> void:
    var root = animal["root"] as Node3D
    var pos = root.position
    var kind = String(animal["kind"])

    if kind == "deer":
        var wolf = _nearest_wildlife(pos, "wolf", 9.0)
        if wolf != null:
            var away = pos - (wolf["root"] as Node3D).position
            if away.length_squared() > 0.01:
                animal["target"] = _clamp_world(pos + away.normalized() * 10.0)
                return

        if float(animal["hunger"]) > 0.42:
            var food = _nearest_food_resource(pos, 14.0)
            if food != null:
                animal["target"] = (food["node"] as Node3D).position
                if pos.distance_to((food["node"] as Node3D).position) <= 1.0:
                    var taken = minf(0.08, float(food["amount"]))
                    food["amount"] = float(food["amount"]) - taken
                    animal["hunger"] = clampf(float(animal["hunger"]) - taken * 1.5, 0.0, 1.0)

        if float(animal["age"]) >= 2.0 and sim_time - float(animal["last_birth"]) > YEAR_SECONDS * 1.2 and _count_wildlife("deer") < 70 and rng.randf() < 0.018:
            animal["last_birth"] = sim_time
            _spawn_animal("deer", _clamp_world(pos + Vector3(rng.randf_range(-1.5, 1.5), 0.0, rng.randf_range(-1.5, 1.5))), 0.0)
        elif float(animal["hunger"]) <= 0.42 or animal["target"] == pos:
            animal["target"] = _clamp_world(pos + Vector3(rng.randf_range(-9.0, 9.0), 0.0, rng.randf_range(-9.0, 9.0)))
    else:
        var prey = _nearest_wildlife(pos, "deer", 16.0)
        if prey != null:
            animal["target"] = (prey["root"] as Node3D).position
            if pos.distance_to((prey["root"] as Node3D).position) <= 1.15:
                prey["health"] = float(prey["health"]) - rng.randf_range(0.18, 0.34)
                if float(prey["health"]) <= 0.0:
                    animal["hunger"] = clampf(float(animal["hunger"]) - 0.70, 0.0, 1.0)
        else:
            animal["target"] = _clamp_world(pos + Vector3(rng.randf_range(-12.0, 12.0), 0.0, rng.randf_range(-12.0, 12.0)))

        if float(animal["age"]) >= 2.5 and sim_time - float(animal["last_birth"]) > YEAR_SECONDS * 1.8 and _count_wildlife("wolf") < 18 and rng.randf() < 0.007:
            animal["last_birth"] = sim_time
            _spawn_animal("wolf", _clamp_world(pos + Vector3(rng.randf_range(-1.5, 1.5), 0.0, rng.randf_range(-1.5, 1.5))), 0.0)

func _remove_wildlife_at(index: int, leave_food: bool) -> void:
    if index < 0 or index >= wildlife.size():
        return
    var animal: Dictionary = wildlife[index]
    var pos = (animal["root"] as Node3D).position
    if leave_food and String(animal["kind"]) == "deer":
        _create_resource("food", 0.0, 0.48, pos)
    if is_instance_valid(animal["root"]):
        (animal["root"] as Node).queue_free()
    wildlife.remove_at(index)

func _try_hunt(a: Dictionary, wid: int) -> void:
    var prey = _wildlife_by_id(wid)
    if prey == null:
        a["target_wildlife_id"] = -1
        a["next_think"] = sim_time
        return
    var pos = (a["root"] as Node3D).position
    var prey_pos = (prey["root"] as Node3D).position
    var range_value = 4.5 if a["techniques"].has("bow") else 1.35
    if pos.distance_to(prey_pos) > range_value:
        return

    var damage = 0.10 + float(a["strength"]) * 0.14 + float(a["skills"]["combat"]) * 0.10
    if a["techniques"].has("spear"):
        damage += 0.14
    if a["techniques"].has("bow"):
        damage += 0.12
    if a["techniques"].has("metal_tools"):
        damage += 0.10
    prey["health"] = float(prey["health"]) - damage * rng.randf_range(0.75, 1.20)
    a["skills"]["combat"] = clampf(float(a["skills"]["combat"]) + 0.008, 0.0, 1.0)
    a["skills"]["foraging"] = clampf(float(a["skills"]["foraging"]) + 0.006, 0.0, 1.0)

    if float(prey["health"]) <= 0.0:
        var food_pos = (prey["root"] as Node3D).position
        for i in range(wildlife.size() - 1, -1, -1):
            if int(wildlife[i]["id"]) == wid:
                _remove_wildlife_at(i, false)
                break
        _create_resource("food", 0.0, 0.58, food_pos)
        a["hunger"] = clampf(float(a["hunger"]) - 0.22, 0.0, 1.0)
        a["target_wildlife_id"] = -1
        a["next_think"] = sim_time
'''

s = s.replace("func _spawn_agent(pos: Vector3", wildlife_funcs + "\nfunc _spawn_agent(pos: Vector3", 1)

s = s.replace(
    '        "target_rid": -1,\n',
    '        "target_rid": -1,\n        "target_wildlife_id": -1,\n',
    1,
)

s = s.replace(
    "    var temp = _world_temperature()\n\n    for i in range(agents.size() - 1, -1, -1):\n",
    "    var temp = _world_temperature()\n    _update_wildlife(dt)\n\n    for i in range(agents.size() - 1, -1, -1):\n",
)

s = s.replace(
    '    a["action"] = action\n    a["target_rid"] = -1\n',
    '    a["action"] = action\n    a["target_rid"] = -1\n    a["target_wildlife_id"] = -1\n',
)

s = s.replace(
"""    elif action == "Экспериментирует":
        var material = _nearest_material(a)
        a["target"] = (material["node"] as Node3D).position if material != null else _random_near(a, 9.0)
    elif action == "Следует за семьёй":
""",
"""    elif action == "Экспериментирует":
        var material = _nearest_material(a)
        a["target"] = (material["node"] as Node3D).position if material != null else _random_near(a, 9.0)
    elif action == "Охотится":
        var prey = _nearest_wildlife((a["root"] as Node3D).position, "deer", PERCEPTION_RADIUS * 1.5)
        if prey != null:
            a["target_wildlife_id"] = int(prey["id"])
            a["target"] = (prey["root"] as Node3D).position
        else:
            a["target"] = _random_near(a, 12.0)
    elif action == "Следует за семьёй":
""",
)

s = s.replace(
"""    var node = a["root"] as Node3D
    var target: Vector3 = a["target"]
""",
"""    var node = a["root"] as Node3D
    var wid = int(a.get("target_wildlife_id", -1))
    if wid >= 0:
        var moving_prey = _wildlife_by_id(wid)
        if moving_prey != null:
            a["target"] = (moving_prey["root"] as Node3D).position
        else:
            a["target_wildlife_id"] = -1
    var target: Vector3 = a["target"]
""",
1,
)

s = s.replace(
"""func _try_interact(a: Dictionary) -> void:
    var rid = int(a["target_rid"])
""",
"""func _try_interact(a: Dictionary) -> void:
    var wid = int(a.get("target_wildlife_id", -1))
    if wid >= 0:
        _try_hunt(a, wid)
        return
    var rid = int(a["target_rid"])
""",
)

# Persist wildlife.
s = s.replace(
"""    var saved_agents: Array = []
""",
"""    var saved_wildlife: Array = []
    for animal in wildlife:
        var animal_pos = (animal["root"] as Node3D).position
        saved_wildlife.append({
            "id": animal["id"], "kind": animal["kind"], "pos": [animal_pos.x, animal_pos.y, animal_pos.z],
            "health": animal["health"], "hunger": animal["hunger"], "age": animal["age"],
            "lifespan": animal["lifespan"], "last_birth": animal["last_birth"]
        })

    var saved_agents: Array = []
""",
)

s = s.replace(
    '"resources": saved_resources, "agents": saved_agents, "cultures": saved_cultures',
    '"resources": saved_resources, "wildlife": saved_wildlife, "agents": saved_agents, "cultures": saved_cultures',
)

s = s.replace(
"""    for raw in data.get("cultures", []):
""",
"""    for raw in data.get("wildlife", []):
        var wp: Array = raw["pos"]
        var animal = _spawn_animal(String(raw["kind"]), Vector3(float(wp[0]), 0.0, float(wp[2])), float(raw["age"]))
        animal["id"] = int(raw["id"])
        animal["health"] = float(raw["health"])
        animal["hunger"] = float(raw["hunger"])
        animal["lifespan"] = float(raw["lifespan"])
        animal["last_birth"] = float(raw["last_birth"])
        next_wildlife_id = maxi(next_wildlife_id, int(raw["id"]) + 1)

    for raw in data.get("cultures", []):
""",
)

s = s.replace(
"""    _spawn_wildlife_decor()
    _update_structures()
""",
"""    _spawn_wildlife_decor()
    if wildlife.is_empty():
        _spawn_wildlife()
    _update_structures()
""",
)

# Surface ecology in the HUD.
s = s.replace(
"""    status_label.text = "Г%d Д%d  •  Люди %d  •  Поколение %d  •  Культуры %d  •  Поселения %d  •  Открытия %d  •  Конфликты %d  •  T %d%%" % [
        year, day, agents.size(), max_generation, active_cultures, settlements, global_discoveries.size(), conflicts, int(_world_temperature() * 100.0)
    ]
""",
"""    status_label.text = "Г%d Д%d  •  Люди %d  •  Животные %d  •  Поколение %d  •  Культуры %d  •  Поселения %d  •  Открытия %d  •  Конфликты %d  •  T %d%%" % [
        year, day, agents.size(), wildlife.size(), max_generation, active_cultures, settlements, global_discoveries.size(), conflicts, int(_world_temperature() * 100.0)
    ]
""",
)

p.write_text(s, encoding="utf-8")

project = root / "project.godot"
ps = project.read_text(encoding="utf-8").replace('config/version="1.2.1"', 'config/version="1.3.0"')
project.write_text(ps, encoding="utf-8")

preset = root / "export_presets.cfg"
es = preset.read_text(encoding="utf-8").replace("version/code=6", "version/code=7").replace('version/name="1.2.1"', 'version/name="1.3.0"')
preset.write_text(es, encoding="utf-8")
