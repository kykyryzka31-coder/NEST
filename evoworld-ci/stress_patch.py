from pathlib import Path
import sys

root = Path(sys.argv[1])
p = root / "main.gd"
s = p.read_text(encoding="utf-8")

s = s.replace(
    "var next_resource_update = 0.0\n",
    "var next_resource_update = 0.0\nvar ci_stress = false\nvar ci_stress_target = 0.0\nvar ci_save_done = false\n",
)

s = s.replace(
    "    _setup_menu()\n    _show_menu()\n",
    """    _setup_menu()
    _show_menu()
    if "--ci-stress" in OS.get_cmdline_user_args():
        ci_stress = true
        ci_stress_target = YEAR_SECONDS * 20.0
        auto_slow = false
        _start_world(12345)
        auto_slow = false
        _set_speed(100.0)
        print("CI_STRESS_START population=", agents.size(), " target_years=20")
""",
)

s = s.replace(
    "    _refresh_ui()\n\nfunc _simulate_step(dt: float) -> void:\n",
    """    _refresh_ui()
    if ci_stress and not ci_save_done and sim_time >= YEAR_SECONDS * 10.0:
        ci_save_done = true
        var before_population = agents.size()
        var before_births = births
        _save_world(true)
        _load_world()
        auto_slow = false
        _set_speed(100.0)
        print("CI_SAVELOAD population_before=", before_population, " population_after=", agents.size(), " births_before=", before_births, " births_after=", births, " year=", sim_time / YEAR_SECONDS)
        if agents.size() != before_population or births != before_births:
            push_error("CI save/load failed: world state changed")
            get_tree().quit(3)
    if ci_stress and sim_time >= ci_stress_target:
        print("CI_STRESS_RESULT years=", sim_time / YEAR_SECONDS, " population=", agents.size(), " births=", births, " deaths=", deaths, " generation=", max_generation, " discoveries=", global_discoveries.size(), " cultures=", cultures.size(), " conflicts=", conflicts)
        if agents.size() < 10 or births < 8 or max_generation < 2:
            push_error("CI stress failed: population did not sustain generations")
            get_tree().quit(2)
        else:
            get_tree().quit(0)

func _simulate_step(dt: float) -> void:
""",
)



# --- EvoWorld 1.2.0 balance/gameplay patch ---
repls = {
    "const PERCEPTION_RADIUS := 20.0": "const PERCEPTION_RADIUS := 26.0",
    "const SOCIAL_RADIUS := 8.0": "const SOCIAL_RADIUS := 10.0",
    "    for i in range(42):\n        _create_resource(\"food\", 0.0, rng.randf_range(0.46, 0.68))":
        "    for i in range(60):\n        _create_resource(\"food\", 0.0, rng.randf_range(0.46, 0.68))",
    "    for i in range(14):\n        _create_resource(\"water\", 0.0, 0.9)":
        "    for i in range(20):\n        _create_resource(\"water\", 0.0, 0.9)",
    '    a["hunger"] = clampf(float(a["hunger"]) + dt * 0.00255 * metabolism, 0.0, 1.0)\n    a["thirst"] = clampf(float(a["thirst"]) + dt * 0.00385 * metabolism, 0.0, 1.0)\n    a["fatigue"] = clampf(float(a["fatigue"]) + dt * 0.0016, 0.0, 1.0)':
        '    var age_factor = 0.72 if float(a["age"]) < 14.0 else 1.0\n    var culture_factor = 0.92 if int(a["culture_id"]) >= 0 else 1.0\n    var storage_factor = 0.88 if a["techniques"].has("storage") else 1.0\n    a["hunger"] = clampf(float(a["hunger"]) + dt * 0.00185 * metabolism * age_factor * culture_factor * storage_factor, 0.0, 1.0)\n    a["thirst"] = clampf(float(a["thirst"]) + dt * 0.00265 * metabolism * age_factor, 0.0, 1.0)\n    a["fatigue"] = clampf(float(a["fatigue"]) + dt * 0.00135, 0.0, 1.0)',
    '    if float(a["hunger"]) > 0.96:\n        a["health"] = float(a["health"]) - dt * 0.0029\n    if float(a["thirst"]) > 0.96:\n        a["health"] = float(a["health"]) - dt * 0.0055\n    if float(a["cold_stress"]) > 0.62:\n        a["health"] = float(a["health"]) - dt * 0.0017 * float(a["cold_stress"])':
        '    if float(a["hunger"]) > 0.985:\n        a["health"] = float(a["health"]) - dt * 0.0018\n    if float(a["thirst"]) > 0.985:\n        a["health"] = float(a["health"]) - dt * 0.0032\n    if float(a["cold_stress"]) > 0.78:\n        a["health"] = float(a["health"]) - dt * 0.0010 * float(a["cold_stress"])',
    '        r["respawn_at"] = sim_time + (32.0 if kind in ["food", "water"] else 110.0)':
        '        r["respawn_at"] = sim_time + (18.0 if kind == "food" else (10.0 if kind == "water" else 110.0))',
    '    if sim_time - float(a["last_birth"]) < YEAR_SECONDS * 1.8:':
        '    if sim_time - float(a["last_birth"]) < YEAR_SECONDS * 1.25:',
    '    if float(a["health"]) < 0.70 or float(a["hunger"]) > 0.68 or float(a["thirst"]) > 0.68:':
        '    if float(a["health"]) < 0.60 or float(a["hunger"]) > 0.78 or float(a["thirst"]) > 0.78:',
    '    var chance = (0.08 + fertility * 0.16 + social * 0.06) * crowd_factor':
        '    var chance = (0.14 + fertility * 0.22 + social * 0.08) * crowd_factor',
}
for old, new in repls.items():
    s = s.replace(old, new)

# Child family cohesion + culture-centered wandering.
s = s.replace(
    '    var hunt_score = 0.0\n    if a["techniques"].has("spear") or a["techniques"].has("bow"):\n        hunt_score = float(a["hunger"]) * 0.58 + float(a["aggression"]) * 0.16\n',
    '    var hunt_score = 0.0\n    if a["techniques"].has("spear") or a["techniques"].has("bow"):\n        hunt_score = float(a["hunger"]) * 0.58 + float(a["aggression"]) * 0.16\n    var family_score = 0.0\n    if float(a["age"]) < 12.0 and float(a["hunger"]) < 0.72 and float(a["thirst"]) < 0.72:\n        family_score = 0.70 + float(a["sociability"]) * 0.18\n'
)
s = s.replace(
    '    if hunt_score > best:\n        action = "Охотится"\n',
    '    if hunt_score > best:\n        best = hunt_score\n        action = "Охотится"\n    if family_score > best:\n        action = "Следует за семьёй"\n'
)
s = s.replace(
    '    elif action == "Экспериментирует":\n        var material = _nearest_material(a)\n        a["target"] = (material["node"] as Node3D).position if material != null else _random_near(a, 9.0)\n    else:\n        a["target"] = _random_near(a, 12.0)\n',
    '    elif action == "Экспериментирует":\n        var material = _nearest_material(a)\n        a["target"] = (material["node"] as Node3D).position if material != null else _random_near(a, 9.0)\n    elif action == "Следует за семьёй":\n        var parent: Variant = _agent_by_id(int(a["mother_id"]))\n        if parent == null:\n            parent = _agent_by_id(int(a["father_id"]))\n        a["target"] = (parent["root"] as Node3D).position if parent != null else _random_near(a, 7.0)\n    else:\n        var culture: Variant = _culture_by_id(int(a["culture_id"]))\n        if culture != null and rng.randf() < 0.62:\n            var center: Vector3 = culture["center"]\n            a["target"] = _clamp_world(center + Vector3(rng.randf_range(-9.0, 9.0), 0.0, rng.randf_range(-9.0, 9.0)))\n        else:\n            a["target"] = _random_near(a, 12.0)\n'
)

# Settlement food support once farming is culturally established.
s = s.replace(
    '        var farming_count = 0\n        var masonry_count = 0',
    '        var farming_count = 0\n        var irrigation_count = 0\n        var masonry_count = 0'
)
s = s.replace(
    '            if a["techniques"].has("farming"):\n                farming_count += 1\n            if a["techniques"].has("masonry"):',
    '            if a["techniques"].has("farming"):\n                farming_count += 1\n            if a["techniques"].has("irrigation"):\n                irrigation_count += 1\n            if a["techniques"].has("masonry"):'
)
s = s.replace(
    '                _upgrade_settlement(settlement, culture, farming_count, masonry_count)\n\nfunc _create_settlement',
    '''                _upgrade_settlement(settlement, culture, farming_count, masonry_count)
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

func _create_settlement'''
)

p.write_text(s, encoding="utf-8")


# EvoWorld 1.2 balance and survival patch.
s = s.replace("const PERCEPTION_RADIUS := 20.0", "const PERCEPTION_RADIUS := 26.0")
s = s.replace("const SOCIAL_RADIUS := 8.0", "const SOCIAL_RADIUS := 10.0")
s = s.replace("for i in range(42):\n        _create_resource(\"food\", 0.0", "for i in range(60):\n        _create_resource(\"food\", 0.0")
s = s.replace("for i in range(14):\n        _create_resource(\"water\", 0.0, 0.9)", "for i in range(20):\n        _create_resource(\"water\", 0.0, 0.9)")

s = s.replace(
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
"""
)
s = s.replace(
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
"""
)
s = s.replace('r["respawn_at"] = sim_time + (32.0 if kind in ["food", "water"] else 110.0)',
              'r["respawn_at"] = sim_time + (18.0 if kind == "food" else (10.0 if kind == "water" else 110.0))')
s = s.replace('YEAR_SECONDS * 1.8', 'YEAR_SECONDS * 1.25')
s = s.replace('float(a["health"]) < 0.70 or float(a["hunger"]) > 0.68 or float(a["thirst"]) > 0.68',
              'float(a["health"]) < 0.60 or float(a["hunger"]) > 0.78 or float(a["thirst"]) > 0.78')
s = s.replace('(0.08 + fertility * 0.16 + social * 0.06)', '(0.14 + fertility * 0.22 + social * 0.08)')

# Children stay close to family; cultures stop randomly dispersing.
s = s.replace(
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
"""
)
s = s.replace(
"""    if hunt_score > best:
        action = "Охотится"
""",
"""    if hunt_score > best:
        best = hunt_score
        action = "Охотится"
    if family_score > best:
        action = "Следует за семьёй"
"""
)
s = s.replace(
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
"""
)

# Farming has a real simulation effect: settlements maintain local food sources.
s = s.replace("        var farming_count = 0\n        var masonry_count = 0",
              "        var farming_count = 0\n        var irrigation_count = 0\n        var masonry_count = 0")
s = s.replace('            if a["techniques"].has("masonry"):\n                masonry_count += 1',
              '            if a["techniques"].has("irrigation"):\n                irrigation_count += 1\n            if a["techniques"].has("masonry"):\n                masonry_count += 1')
s = s.replace(
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
"""
)

# Final release identity.
ps = ps.replace('config/version="1.2.0"', 'config/version="1.2.0"')
es = es.replace("version/code=5", "version/code=5").replace('version/name="1.2.0"', 'version/name="1.2.0"')
