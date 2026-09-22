from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
p = root / "main.gd"
s = p.read_text(encoding="utf-8")

def replace_once(old: str, new: str):
    global s
    if old not in s:
        raise RuntimeError("Ecology patch target not found: " + old[:120])
    s = s.replace(old, new, 1)

replace_once('const MAX_POPULATION := 320\n', 'const MAX_POPULATION := 320\nconst MAX_ANIMALS := 130\n')
replace_once('const SAVE_PATH := "user://evoworld_save_v4.json"', 'const SAVE_PATH := "user://evoworld_save_v5.json"')
replace_once(
    'var agents: Array = []\nvar resources: Array = []\n',
    'var agents: Array = []\nvar animals: Array = []\nvar resources: Array = []\n'
)
replace_once(
    'var next_agent_id = 1\nvar next_resource_id = 1\n',
    'var next_agent_id = 1\nvar next_animal_id = 1\nvar next_resource_id = 1\n'
)
replace_once(
    'var births = 0\nvar deaths = 0\n',
    'var births = 0\nvar deaths = 0\nvar animal_births = 0\nvar animal_deaths = 0\n'
)

replace_once('    agents.clear()\n    resources.clear()\n', '    agents.clear()\n    animals.clear()\n    resources.clear()\n')
replace_once('    next_agent_id = 1\n    next_resource_id = 1\n', '    next_agent_id = 1\n    next_animal_id = 1\n    next_resource_id = 1\n')
replace_once(
    '    births = 0\n    deaths = 0\n    conflicts = 0\n',
    '    births = 0\n    deaths = 0\n    animal_births = 0\n    animal_deaths = 0\n    conflicts = 0\n'
)

replace_once(
    '    _spawn_initial_population()\n    _spawn_wildlife_decor()\n',
    '    _spawn_initial_population()\n    _spawn_wildlife_decor()\n    _spawn_initial_animals()\n'
)
replace_once(
    '    for i in range(8):\n        _create_resource("ore", 0.0, 0.52)\n',
    '    for i in range(8):\n        _create_resource("ore", 0.0, 0.52)\n    for i in range(68):\n        _create_resource("grass", 0.0, rng.randf_range(0.28, 0.42))\n'
)

replace_once(
    '        "target_rid": -1,\n        "next_think":',
    '        "target_rid": -1,\n        "target_animal_id": -1,\n        "next_think":'
)

replace_once(
    '    var temp = _world_temperature()\n\n    for i in range(agents.size() - 1, -1, -1):',
    '    var temp = _world_temperature()\n    _simulate_animals(dt, temp)\n\n    for i in range(agents.size() - 1, -1, -1):'
)
replace_once(
    '        _move_agent(a, dt)\n        _try_interact(a)\n        agents[i] = a\n',
    '        _move_agent(a, dt)\n        _try_interact(a)\n        _try_hunt_animal(a)\n        agents[i] = a\n'
)

replace_once(
    '    a["action"] = action\n    a["target_rid"] = -1\n',
    '    a["action"] = action\n    a["target_rid"] = -1\n    a["target_animal_id"] = -1\n'
)
replace_once(
    '''    elif action == "Экспериментирует":
        var material = _nearest_material(a)
        a["target"] = (material["node"] as Node3D).position if material != null else _random_near(a, 9.0)
    else:
''',
    '''    elif action == "Экспериментирует":
        var material = _nearest_material(a)
        a["target"] = (material["node"] as Node3D).position if material != null else _random_near(a, 9.0)
    elif action == "Охотится":
        var prey = _nearest_prey(a, 28.0)
        if prey != null:
            a["target_animal_id"] = int(prey["aid"])
            a["target"] = (prey["root"] as Node3D).position
        else:
            a["target"] = _random_near(a, 14.0)
    else:
'''
)

animal_funcs = r'''
func _spawn_initial_animals() -> void:
    var herd_centers = [Vector3(-24.0, 0.0, -20.0), Vector3(23.0, 0.0, -18.0), Vector3(-20.0, 0.0, 23.0), Vector3(22.0, 0.0, 22.0)]
    for herd in herd_centers:
        for i in range(11):
            _spawn_animal("grazer", _clamp_world(herd + Vector3(rng.randf_range(-6.0, 6.0), 0.0, rng.randf_range(-6.0, 6.0))))
    var pack_centers = [Vector3(-5.0, 0.0, -28.0), Vector3(7.0, 0.0, 28.0)]
    for pack in pack_centers:
        for i in range(2):
            _spawn_animal("predator", _clamp_world(pack + Vector3(rng.randf_range(-4.0, 4.0), 0.0, rng.randf_range(-4.0, 4.0))))

func _spawn_animal(species: String, pos: Vector3, starting_age: float = -1.0, sex_override: String = "") -> Dictionary:
    var root = Node3D.new()
    root.position = _clamp_world(pos)
    world_root.add_child(root)

    var body = MeshInstance3D.new()
    var body_mesh = CapsuleMesh.new()
    body_mesh.radius = 0.30 if species == "grazer" else 0.34
    body_mesh.height = 0.78 if species == "grazer" else 0.72
    body.mesh = body_mesh
    body.rotation_degrees.z = 90.0
    body.position.y = 0.42
    root.add_child(body)

    var head = MeshInstance3D.new()
    var head_mesh = SphereMesh.new()
    head_mesh.radius = 0.22 if species == "grazer" else 0.25
    head_mesh.height = head_mesh.radius * 2.0
    head.mesh = head_mesh
    head.position = Vector3(0.48, 0.48, 0.0)
    root.add_child(head)

    var mat = StandardMaterial3D.new()
    mat.albedo_color = Color(0.55, 0.42, 0.20) if species == "grazer" else Color(0.34, 0.35, 0.39)
    body.material_override = mat
    var head_mat = StandardMaterial3D.new()
    head_mat.albedo_color = mat.albedo_color.lightened(0.08)
    head.material_override = head_mat

    var sex = sex_override if sex_override != "" else ("F" if rng.randf() < 0.5 else "M")
    var age = starting_age if starting_age >= 0.0 else rng.randf_range(0.5, 4.5)
    var animal = {
        "aid": next_animal_id,
        "species": species,
        "root": root,
        "health": 1.0,
        "hunger": rng.randf_range(0.0, 0.42),
        "age": age,
        "lifespan": rng.randf_range(14.0, 21.0) if species == "grazer" else rng.randf_range(16.0, 24.0),
        "sex": sex,
        "fertility": rng.randf_range(0.35, 0.95),
        "speed": rng.randf_range(1.8, 2.5) if species == "grazer" else rng.randf_range(2.1, 2.9),
        "target": root.position,
        "target_rid": -1,
        "target_aid": -1,
        "next_think": sim_time + rng.randf_range(0.0, 5.0),
        "next_attack": sim_time,
        "last_birth": -999999.0
    }
    next_animal_id += 1
    animals.append(animal)
    return animal

func _simulate_animals(dt: float, temperature: float) -> void:
    for i in range(animals.size() - 1, -1, -1):
        var animal: Dictionary = animals[i]
        animal["age"] = float(animal["age"]) + dt / YEAR_SECONDS
        var hunger_rate = 0.00105 if String(animal["species"]) == "grazer" else 0.00085
        animal["hunger"] = clampf(float(animal["hunger"]) + dt * hunger_rate, 0.0, 1.0)
        if float(animal["hunger"]) > 0.97:
            animal["health"] = float(animal["health"]) - dt * 0.0030
        elif float(animal["hunger"]) < 0.55:
            animal["health"] = minf(1.0, float(animal["health"]) + dt * 0.00032)
        if temperature < 0.10:
            animal["health"] = float(animal["health"]) - dt * 0.00045
        if float(animal["health"]) <= 0.0 or float(animal["age"]) > float(animal["lifespan"]):
            _kill_animal(i, animal)
            continue

        if sim_time >= float(animal["next_think"]):
            _animal_think(animal)
            var min_delay = 4.0 if speed < 40.0 else 8.0
            var max_delay = 8.0 if speed < 40.0 else 15.0
            animal["next_think"] = sim_time + rng.randf_range(min_delay, max_delay)
            _animal_try_reproduce(animal)

        _move_animal(animal, dt)
        _animal_interact(animal)
        animals[i] = animal

func _animal_think(animal: Dictionary) -> void:
    animal["target_rid"] = -1
    animal["target_aid"] = -1
    var species = String(animal["species"])
    if species == "grazer" and float(animal["hunger"]) > 0.28:
        var food = _nearest_resource_to_position((animal["root"] as Node3D).position, "grass", 28.0)
        if food != null:
            animal["target_rid"] = int(food["rid"])
            animal["target"] = (food["node"] as Node3D).position
            return
    elif species == "predator" and float(animal["hunger"]) > 0.52:
        var prey = _nearest_grazer_to_position((animal["root"] as Node3D).position, 30.0)
        if prey != null:
            animal["target_aid"] = int(prey["aid"])
            animal["target"] = (prey["root"] as Node3D).position
            return
    animal["target"] = _clamp_world((animal["root"] as Node3D).position + Vector3(rng.randf_range(-11.0, 11.0), 0.0, rng.randf_range(-11.0, 11.0)))

func _move_animal(animal: Dictionary, dt: float) -> void:
    var root = animal["root"] as Node3D
    if int(animal["target_aid"]) >= 0:
        var prey = _animal_by_id(int(animal["target_aid"]))
        if prey != null and float(prey["health"]) > 0.0:
            animal["target"] = (prey["root"] as Node3D).position
    var target: Vector3 = animal["target"]
    var delta = target - root.position
    delta.y = 0.0
    if delta.length_squared() < 0.04:
        return
    var amount = minf(delta.length(), float(animal["speed"]) * dt)
    var dir = delta.normalized()
    root.position = _clamp_world(root.position + dir * amount)
    root.rotation.y = atan2(dir.x, dir.z)

func _animal_interact(animal: Dictionary) -> void:
    var root = animal["root"] as Node3D
    if String(animal["species"]) == "grazer" and int(animal["target_rid"]) >= 0:
        var idx = _resource_index_by_id(int(animal["target_rid"]))
        if idx >= 0:
            var r: Dictionary = resources[idx]
            if String(r["kind"]) == "grass" and float(r["amount"]) > 0.05 and root.position.distance_to((r["node"] as Node3D).position) <= 1.05:
                var taken = minf(0.11, float(r["amount"]))
                r["amount"] = float(r["amount"]) - taken
                animal["hunger"] = maxf(0.0, float(animal["hunger"]) - taken * 1.6)
                if float(r["amount"]) <= 0.05:
                    r["amount"] = 0.0
                    r["respawn_at"] = sim_time + 17.0
                    (r["node"] as Node3D).visible = false
                resources[idx] = r
                animal["target_rid"] = -1
                animal["next_think"] = sim_time
    elif String(animal["species"]) == "predator" and int(animal["target_aid"]) >= 0 and sim_time >= float(animal["next_attack"]):
        var prey = _animal_by_id(int(animal["target_aid"]))
        if prey != null and float(prey["health"]) > 0.0 and root.position.distance_to((prey["root"] as Node3D).position) <= 1.25:
            prey["health"] = float(prey["health"]) - rng.randf_range(0.34, 0.58)
            animal["next_attack"] = sim_time + 2.0
            if float(prey["health"]) <= 0.0:
                animal["hunger"] = maxf(0.0, float(animal["hunger"]) - 0.82)
                animal["target_aid"] = -1
                animal["next_think"] = sim_time

func _animal_try_reproduce(animal: Dictionary) -> void:
    if animals.size() >= MAX_ANIMALS or String(animal["sex"]) != "F":
        return
    var species = String(animal["species"])
    var adult_age = 1.8 if species == "grazer" else 2.6
    if float(animal["age"]) < adult_age or float(animal["health"]) < 0.72 or float(animal["hunger"]) > 0.66:
        return
    var cooldown = YEAR_SECONDS * (0.55 if species == "grazer" else 1.10)
    if sim_time - float(animal["last_birth"]) < cooldown:
        return
    var root = animal["root"] as Node3D
    var mate_found = false
    for other in animals:
        if int(other["aid"]) == int(animal["aid"]) or String(other["species"]) != species or String(other["sex"]) != "M":
            continue
        if float(other["age"]) < adult_age or float(other["health"]) < 0.65:
            continue
        if root.position.distance_to((other["root"] as Node3D).position) <= 12.0:
            mate_found = true
            break
    if not mate_found:
        return
    var density_factor = clampf(1.0 - float(animals.size()) / float(MAX_ANIMALS), 0.08, 1.0)
    if species == "predator":
        var grazers = _animal_species_count("grazer")
        var predators = _animal_species_count("predator")
        if predators * 6 >= maxi(grazers, 1):
            return
    var chance = (0.12 + float(animal["fertility"]) * 0.16) * density_factor
    if rng.randf() > chance:
        return
    animal["last_birth"] = sim_time
    animal_births += 1
    _spawn_animal(species, _clamp_world(root.position + Vector3(rng.randf_range(-1.0, 1.0), 0.0, rng.randf_range(-1.0, 1.0))), 0.0)

func _kill_animal(index: int, animal: Dictionary) -> void:
    if is_instance_valid(animal["root"]):
        (animal["root"] as Node).queue_free()
    animals.remove_at(index)
    animal_deaths += 1

func _animal_species_count(species: String) -> int:
    var count = 0
    for animal in animals:
        if String(animal["species"]) == species and float(animal["health"]) > 0.0:
            count += 1
    return count

func _animal_by_id(aid: int) -> Variant:
    for animal in animals:
        if int(animal["aid"]) == aid:
            return animal
    return null

func _nearest_grazer_to_position(pos: Vector3, radius: float) -> Variant:
    var best: Variant = null
    var best_dist = radius
    for animal in animals:
        if String(animal["species"]) != "grazer" or float(animal["health"]) <= 0.0:
            continue
        var dist = pos.distance_to((animal["root"] as Node3D).position)
        if dist < best_dist:
            best_dist = dist
            best = animal
    return best

func _nearest_resource_to_position(pos: Vector3, kind: String, radius: float) -> Variant:
    var best: Variant = null
    var best_dist = radius
    for r in resources:
        if String(r["kind"]) != kind or float(r["amount"]) <= 0.05:
            continue
        var dist = pos.distance_to((r["node"] as Node3D).position)
        if dist < best_dist:
            best_dist = dist
            best = r
    return best

func _nearest_prey(a: Dictionary, radius: float) -> Variant:
    return _nearest_grazer_to_position((a["root"] as Node3D).position, radius)

func _try_hunt_animal(a: Dictionary) -> void:
    if String(a["action"]) != "Охотится":
        return
    var aid = int(a["target_animal_id"])
    if aid < 0:
        return
    var prey = _animal_by_id(aid)
    if prey == null or float(prey["health"]) <= 0.0:
        a["target_animal_id"] = -1
        a["next_think"] = sim_time
        return
    var apos = (a["root"] as Node3D).position
    var ppos = (prey["root"] as Node3D).position
    if apos.distance_to(ppos) > 1.55:
        return
    var weapon = 0.45
    if a["techniques"].has("spear"):
        weapon += 0.24
    if a["techniques"].has("bow"):
        weapon += 0.31
    if a["techniques"].has("metal_tools"):
        weapon += 0.12
    var skill = float(a["skills"].get("combat", 0.0))
    var chance = clampf(weapon + skill * 0.28 + float(a["strength"]) * 0.16 - float(a["caution"]) * 0.05, 0.15, 0.97)
    if rng.randf() < chance:
        var damage = 0.58 + float(a["strength"]) * 0.26 + skill * 0.18
        prey["health"] = float(prey["health"]) - damage
        a["skills"]["combat"] = clampf(skill + 0.018, 0.0, 1.0)
        if float(prey["health"]) <= 0.0:
            var nutrition = 0.72
            if a["techniques"].has("cooking") and a["techniques"].has("fire_control"):
                nutrition = 0.88
            a["hunger"] = maxf(0.0, float(a["hunger"]) - nutrition)
            if not global_discoveries.has("successful_hunt"):
                global_discoveries["successful_hunt"] = sim_time
                _add_history("%s совершил(а) первую успешную охоту на животное." % String(a["name"]), true)
    else:
        if rng.randf() < 0.18:
            a["health"] = maxf(0.0, float(a["health"]) - rng.randf_range(0.02, 0.08))
    a["target_animal_id"] = -1
    a["next_think"] = sim_time + 1.0
'''

replace_once(
    'func _spawn_agent(pos: Vector3, inherited: Dictionary = {}, generation: int = 0, starting_age: float = -1.0, sex_override: String = "", mother_id: int = -1, father_id: int = -1) -> Dictionary:\n',
    animal_funcs + '\nfunc _spawn_agent(pos: Vector3, inherited: Dictionary = {}, generation: int = 0, starting_age: float = -1.0, sex_override: String = "", mother_id: int = -1, father_id: int = -1) -> Dictionary:\n'
)

replace_once(
    'status_label.text = "Г%d Д%d  •  Люди %d  •  Поколение %d',
    'status_label.text = "Г%d Д%d  •  Люди %d  •  Животные %d  •  Поколение %d'
)
replace_once(
    'year, day, agents.size(), max_generation, active_cultures, settlements, global_discoveries.size(), conflicts, int(_world_temperature() * 100.0)',
    'year, day, agents.size(), animals.size(), max_generation, active_cultures, settlements, global_discoveries.size(), conflicts, int(_world_temperature() * 100.0)'
)

replace_once(
    '    var saved_agents: Array = []\n',
    '''    var saved_animals: Array = []
    for animal in animals:
        var apos = (animal["root"] as Node3D).position
        saved_animals.append({
            "aid": animal["aid"], "species": animal["species"], "pos": [apos.x, apos.y, apos.z],
            "health": animal["health"], "hunger": animal["hunger"], "age": animal["age"],
            "lifespan": animal["lifespan"], "sex": animal["sex"], "fertility": animal["fertility"],
            "speed": animal["speed"], "last_birth": animal["last_birth"]
        })

    var saved_agents: Array = []
'''
)
replace_once(
    '"births": births, "deaths": deaths, "max_generation": max_generation, "conflicts": conflicts,',
    '"births": births, "deaths": deaths, "animal_births": animal_births, "animal_deaths": animal_deaths, "max_generation": max_generation, "conflicts": conflicts,'
)
replace_once(
    '"resources": saved_resources, "agents": saved_agents, "cultures": saved_cultures',
    '"resources": saved_resources, "animals": saved_animals, "agents": saved_agents, "cultures": saved_cultures'
)
replace_once('"version": 4,', '"version": 5,')

replace_once(
    '    births = int(data.get("births", 0))\n    deaths = int(data.get("deaths", 0))\n',
    '    births = int(data.get("births", 0))\n    deaths = int(data.get("deaths", 0))\n    animal_births = int(data.get("animal_births", 0))\n    animal_deaths = int(data.get("animal_deaths", 0))\n'
)
replace_once(
    '    for raw in data.get("cultures", []):\n',
    '''    for raw in data.get("animals", []):
        var ap: Array = raw["pos"]
        var animal = _spawn_animal(String(raw["species"]), Vector3(float(ap[0]), 0.0, float(ap[2])), float(raw["age"]), String(raw["sex"]))
        animal["aid"] = int(raw["aid"])
        next_animal_id = maxi(next_animal_id, int(raw["aid"]) + 1)
        animal["health"] = float(raw["health"])
        animal["hunger"] = float(raw["hunger"])
        animal["lifespan"] = float(raw["lifespan"])
        animal["fertility"] = float(raw["fertility"])
        animal["speed"] = float(raw["speed"])
        animal["last_birth"] = float(raw["last_birth"])

    for raw in data.get("cultures", []):
'''
)


# Extend CI assertions to cover the ecosystem too (only active in --ci-stress).
s = s.replace(
    "        var before_save_population = agents.size()\n        _save_world(true)\n        _load_world()\n        print(\"CI_SAVELOAD population_before=\", before_save_population, \" population_after=\", agents.size(), \" year=\", sim_time / YEAR_SECONDS)",
    "        var before_save_population = agents.size()\n        var before_save_animals = animals.size()\n        _save_world(true)\n        _load_world()\n        print(\"CI_SAVELOAD population_before=\", before_save_population, \" population_after=\", agents.size(), \" animals_before=\", before_save_animals, \" animals_after=\", animals.size(), \" year=\", sim_time / YEAR_SECONDS)"
)
s = s.replace(
    '        if agents.is_empty():\n            push_error("CI save/load failed: population vanished")',
    '        if agents.is_empty() or animals.is_empty():\n            push_error("CI save/load failed: population or wildlife vanished")'
)
s = s.replace(
    'print("CI_STRESS_RESULT years=", sim_time / YEAR_SECONDS, " population=", agents.size(), " births=", births, " deaths=", deaths, " generation=", max_generation, " discoveries=", global_discoveries.size(), " cultures=", cultures.size(), " conflicts=", conflicts, " climate_events=3")',
    'print("CI_STRESS_RESULT years=", sim_time / YEAR_SECONDS, " population=", agents.size(), " births=", births, " deaths=", deaths, " generation=", max_generation, " discoveries=", global_discoveries.size(), " cultures=", cultures.size(), " conflicts=", conflicts, " animals=", animals.size(), " grazers=", _animal_species_count("grazer"), " predators=", _animal_species_count("predator"), " animal_births=", animal_births, " animal_deaths=", animal_deaths, " climate_events=3")'
)
s = s.replace(
    '        if agents.size() < 8 or births < 6 or max_generation < 2:',
    '        if agents.size() < 8 or births < 6 or max_generation < 2 or animals.size() < 10 or _animal_species_count("grazer") < 8 or animal_births < 4:'
)

p.write_text(s, encoding="utf-8")

project = root / "project.godot"
ps = project.read_text(encoding="utf-8")
ps = re.sub(r'config/version="[^"]+"', 'config/version="1.2.0"', ps)
project.write_text(ps, encoding="utf-8")

preset = root / "export_presets.cfg"
es = preset.read_text(encoding="utf-8")
es = re.sub(r'version/code=\d+', 'version/code=6', es)
es = re.sub(r'version/name="[^"]+"', 'version/name="1.2.0"', es)
preset.write_text(es, encoding="utf-8")
