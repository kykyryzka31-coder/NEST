from pathlib import Path
import sys

root = Path(sys.argv[1])
p = root / "main.gd"
s = p.read_text(encoding="utf-8")

# CI-only state.
s = s.replace(
    "var next_resource_update = 0.0\n",
    "var next_resource_update = 0.0\nvar ci_stress = false\nvar ci_stress_target = 0.0\nvar ci_save_done = false\nvar ci_cold_done = false\nvar ci_heat_done = false\nvar ci_lightning_done = false\n",
)

# Start a deterministic 100x world when CI asks for it.
s = s.replace(
    "    _setup_menu()\n    _show_menu()\n",
    """    _setup_menu()
    _show_menu()
    if "--ci-stress" in OS.get_cmdline_user_args():
        ci_stress = true
        ci_stress_target = YEAR_SECONDS * 25.0
        _start_world(12345)
        auto_slow = false
        _set_speed(100.0)
        print("CI_STRESS_START population=", agents.size(), " target_years=25")
""",
)

# Keep 100x practical without changing event rules: use larger safe integration chunks.
s = s.replace(
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
        if speed >= 75.0:
            max_step = 0.85
        elif speed >= 40.0:
            max_step = 0.55
        elif speed >= 15.0:
            max_step = 0.32
        elif speed >= 5.0:
            max_step = 0.22
        while remaining > 0.00001:
            var step: float = minf(max_step, remaining)
            sim_time += step
            _simulate_step(step)
            remaining -= step
""",
)

# Stress persistence in the middle of the run, then continue the same world.
s = s.replace(
    "    _refresh_ui()\n\nfunc _simulate_step(dt: float) -> void:\n",
    """    _refresh_ui()
    if ci_stress and not ci_cold_done and sim_time >= YEAR_SECONDS * 5.0:
        ci_cold_done = true
        _god_cold_snap()
        print("CI_EVENT cold_snap year=", sim_time / YEAR_SECONDS, " population=", agents.size())
    if ci_stress and not ci_heat_done and sim_time >= YEAR_SECONDS * 9.0:
        ci_heat_done = true
        _god_heat_wave()
        print("CI_EVENT heat_wave year=", sim_time / YEAR_SECONDS, " population=", agents.size())
    if ci_stress and not ci_save_done and sim_time >= YEAR_SECONDS * 12.5:
        ci_save_done = true
        var before_save_population = agents.size()
        _save_world(true)
        _load_world()
        print("CI_SAVELOAD population_before=", before_save_population, " population_after=", agents.size(), " year=", sim_time / YEAR_SECONDS)
        if agents.is_empty():
            push_error("CI save/load failed: population vanished")
            get_tree().quit(3)
    if ci_stress and not ci_lightning_done and sim_time >= YEAR_SECONDS * 16.0:
        ci_lightning_done = true
        _god_lightning()
        print("CI_EVENT lightning year=", sim_time / YEAR_SECONDS, " population=", agents.size())
    if ci_stress and sim_time >= ci_stress_target:
        print("CI_STRESS_RESULT years=", sim_time / YEAR_SECONDS, " population=", agents.size(), " births=", births, " deaths=", deaths, " generation=", max_generation, " discoveries=", global_discoveries.size(), " cultures=", cultures.size(), " conflicts=", conflicts, " climate_events=3")
        if agents.size() < 8 or births < 6 or max_generation < 2:
            push_error("CI stress failed: population did not sustain and reproduce")
            get_tree().quit(2)
        else:
            get_tree().quit(0)

func _simulate_step(dt: float) -> void:
""",
)

# JSON turns integer Dictionary keys into strings. Normalize social trust IDs on load.
memory_block = """func _deserialize_memory(raw: Dictionary) -> Dictionary:
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
    s = s.replace(
        memory_block,
        memory_block + """
func _deserialize_trust(raw: Dictionary) -> Dictionary:
    var out = {}
    for key in raw.keys():
        out[int(key)] = float(raw[key])
    return out
""",
    )
s = s.replace('agent["trust"] = raw.get("trust", {})', 'agent["trust"] = _deserialize_trust(raw.get("trust", {}))')

# Persist lightning/fire-learning state too.
s = s.replace(
    '        "cold_snap_until": cold_snap_until, "heat_wave_until": heat_wave_until,\n        "global_discoveries": global_discoveries, "relations": relations, "history": history,',
    '        "cold_snap_until": cold_snap_until, "heat_wave_until": heat_wave_until,\n        "lightning_bonus_until": lightning_bonus_until, "lightning_position": [lightning_position.x, lightning_position.y, lightning_position.z],\n        "global_discoveries": global_discoveries, "relations": relations, "history": history,',
)
s = s.replace(
    '    cold_snap_until = float(data.get("cold_snap_until", -1.0))\n    heat_wave_until = float(data.get("heat_wave_until", -1.0))\n    global_discoveries = data.get("global_discoveries", {})',
    '    cold_snap_until = float(data.get("cold_snap_until", -1.0))\n    heat_wave_until = float(data.get("heat_wave_until", -1.0))\n    lightning_bonus_until = float(data.get("lightning_bonus_until", -1.0))\n    var lightning_raw: Array = data.get("lightning_position", [0.0, 0.0, 0.0])\n    lightning_position = Vector3(float(lightning_raw[0]), float(lightning_raw[1]), float(lightning_raw[2]))\n    global_discoveries = data.get("global_discoveries", {})',
)


# Godot 4.7 strict inference: nullable Dictionary helpers must return Variant.
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


# Production gameplay balancing and mobile 100x LOD. These changes are included in the APK.
s = s.replace('const SOCIAL_RADIUS := 8.0', 'const SOCIAL_RADIUS := 10.0')
s = s.replace('const SAVE_PATH := "user://evoworld_save_v3.json"', 'const SAVE_PATH := "user://evoworld_save_v4.json"')

s = s.replace(
    """func _spawn_initial_population() -> void:
    for i in range(START_POPULATION):
        _spawn_agent(Vector3(rng.randf_range(-18.0, 18.0), 0.75, rng.randf_range(-18.0, 18.0)))
""",
    """func _spawn_initial_population() -> void:
    var camps := [
        Vector3(-16.0, 0.0, -12.0),
        Vector3(15.0, 0.0, -10.0),
        Vector3(-10.0, 0.0, 15.0),
        Vector3(14.0, 0.0, 14.0)
    ]
    for camp in camps:
        _create_resource("water", 0.0, 1.05, camp + Vector3(2.5, 0.0, 0.0))
        for j in range(5):
            _create_resource("food", 0.0, rng.randf_range(0.50, 0.68), camp + Vector3(rng.randf_range(-5.0, 5.0), 0.0, rng.randf_range(-5.0, 5.0)))
    for i in range(START_POPULATION):
        var camp: Vector3 = camps[i % camps.size()]
        _spawn_agent(_clamp_world(camp + Vector3(rng.randf_range(-5.5, 5.5), 0.0, rng.randf_range(-5.5, 5.5))))
"""
)

s = s.replace(
    '"hunger": rng.randf_range(0.02, 0.34),\n        "thirst": rng.randf_range(0.02, 0.34),',
    '"hunger": rng.randf_range(0.01, 0.22),\n        "thirst": rng.randf_range(0.01, 0.22),'
)

s = s.replace(
    """    a["hunger"] = clampf(float(a["hunger"]) + dt * 0.00255 * metabolism, 0.0, 1.0)
    a["thirst"] = clampf(float(a["thirst"]) + dt * 0.00385 * metabolism, 0.0, 1.0)
    a["fatigue"] = clampf(float(a["fatigue"]) + dt * 0.0016, 0.0, 1.0)
""",
    """    a["hunger"] = clampf(float(a["hunger"]) + dt * 0.00220 * metabolism, 0.0, 1.0)
    a["thirst"] = clampf(float(a["thirst"]) + dt * 0.00315 * metabolism, 0.0, 1.0)
    a["fatigue"] = clampf(float(a["fatigue"]) + dt * 0.0015, 0.0, 1.0)
"""
)

s = s.replace(
    """    if float(a["hunger"]) > 0.96:
        a["health"] = float(a["health"]) - dt * 0.0029
    if float(a["thirst"]) > 0.96:
        a["health"] = float(a["health"]) - dt * 0.0055
    if float(a["cold_stress"]) > 0.62:
        a["health"] = float(a["health"]) - dt * 0.0017 * float(a["cold_stress"])
    if float(a["age"]) > float(a["lifespan"]):
        a["health"] = float(a["health"]) - dt * 0.0027
""",
    """    if float(a["hunger"]) > 0.97:
        a["health"] = float(a["health"]) - dt * 0.0024
    if float(a["thirst"]) > 0.97:
        a["health"] = float(a["health"]) - dt * 0.0042
    if float(a["cold_stress"]) > 0.68:
        a["health"] = float(a["health"]) - dt * 0.00125 * float(a["cold_stress"])
    if float(a["age"]) > float(a["lifespan"]):
        a["health"] = float(a["health"]) - dt * 0.0027
    if float(a["hunger"]) < 0.55 and float(a["thirst"]) < 0.50 and float(a["cold_stress"]) < 0.35 and float(a["fatigue"]) < 0.72:
        a["health"] = clampf(float(a["health"]) + dt * 0.00042, 0.0, 1.0)
"""
)

s = s.replace(
    """        if sim_time >= float(a["next_perception"]):
            _perceive(a)
            a["next_perception"] = sim_time + 1.8
        if sim_time >= float(a["next_social"]):
            _social_tick(a)
            a["next_social"] = sim_time + rng.randf_range(9.0, 20.0)
            _update_agent_visual(a)
""",
    """        if sim_time >= float(a["next_perception"]):
            _perceive(a)
            var perception_interval := 1.8
            if speed >= 75.0:
                perception_interval = 5.0
            elif speed >= 40.0:
                perception_interval = 3.4
            elif speed >= 15.0:
                perception_interval = 2.4
            a["next_perception"] = sim_time + perception_interval
        if sim_time >= float(a["next_social"]):
            _social_tick(a)
            var social_min := 9.0
            var social_max := 20.0
            if speed >= 75.0:
                social_min = 14.0
                social_max = 28.0
            a["next_social"] = sim_time + rng.randf_range(social_min, social_max)
            _update_agent_visual(a)
"""
)

s = s.replace('if String(a["sex"]) != "F" or float(a["age"]) < 18.0 or float(a["age"]) > 43.0:',
              'if String(a["sex"]) != "F" or float(a["age"]) < 17.0 or float(a["age"]) > 45.0:')
s = s.replace('if sim_time - float(a["last_birth"]) < YEAR_SECONDS * 1.8:',
              'if sim_time - float(a["last_birth"]) < YEAR_SECONDS * 1.35:')
s = s.replace('if float(a["health"]) < 0.70 or float(a["hunger"]) > 0.68 or float(a["thirst"]) > 0.68:',
              'if float(a["health"]) < 0.58 or float(a["hunger"]) > 0.80 or float(a["thirst"]) > 0.78:')
s = s.replace('var chance = (0.08 + fertility * 0.16 + social * 0.06) * crowd_factor',
              'var chance = (0.12 + fertility * 0.20 + social * 0.08) * crowd_factor')

s = s.replace(
    """    a["dialect"] = clampf(lerpf(float(a["dialect"]), mean_dialect, 0.04) + rng.randf_range(-0.002, 0.002), 0.0, 1.0)
    _try_reproduce(a, nearby)
""",
    """    a["dialect"] = clampf(lerpf(float(a["dialect"]), mean_dialect, 0.04) + rng.randf_range(-0.002, 0.002), 0.0, 1.0)
    _care_for_children(a, nearby)
    _try_reproduce(a, nearby)
"""
)

if "func _care_for_children" not in s:
    s = s.replace(
        "func _copy_resource_knowledge(a: Dictionary, rid, source: Dictionary) -> void:\n",
        """func _care_for_children(a: Dictionary, nearby: Array) -> void:
    if float(a["age"]) < 16.0 or float(a["health"]) < 0.45:
        return
    if float(a["hunger"]) > 0.82 or float(a["thirst"]) > 0.82:
        return
    for child in nearby:
        if float(child["age"]) >= 9.0:
            continue
        var is_parent := int(child["mother_id"]) == int(a["id"]) or int(child["father_id"]) == int(a["id"])
        if not is_parent and float(a["cooperation"]) < 0.72:
            continue
        if float(child["hunger"]) > 0.42:
            var food_help := minf(0.16, float(child["hunger"]))
            child["hunger"] = maxf(0.0, float(child["hunger"]) - food_help)
            a["hunger"] = minf(1.0, float(a["hunger"]) + food_help * 0.42)
        if float(child["thirst"]) > 0.38:
            var water_help := minf(0.18, float(child["thirst"]))
            child["thirst"] = maxf(0.0, float(child["thirst"]) - water_help)
            a["thirst"] = minf(1.0, float(a["thirst"]) + water_help * 0.38)
        if float(child["health"]) < 0.82 and float(a["cooperation"]) > 0.55:
            child["health"] = minf(1.0, float(child["health"]) + 0.025)

func _copy_resource_knowledge(a: Dictionary, rid, source: Dictionary) -> void:
"""
    )

s = s.replace('r["respawn_at"] = sim_time + (32.0 if kind in ["food", "water"] else 110.0)',
              'r["respawn_at"] = sim_time + (24.0 if kind in ["food", "water"] else 110.0)')
s = s.replace('next_auto_save = YEAR_SECONDS * 5.0', 'next_auto_save = YEAR_SECONDS * 8.0')
s = s.replace('next_auto_save = sim_time + YEAR_SECONDS * 5.0', 'next_auto_save = sim_time + YEAR_SECONDS * 8.0')
s = s.replace('"version": 3,', '"version": 4,')

p.write_text(s, encoding="utf-8")

# Final Android build version.
project = root / "project.godot"
ps = project.read_text(encoding="utf-8").replace('config/version="1.1.0"', 'config/version="1.1.2"')
if 'config/icon=' not in ps:
    ps = ps.replace('config/version="1.1.2"\n', 'config/version="1.1.1"\nconfig/icon="res://icon.svg"\n')
project.write_text(ps, encoding="utf-8")

(root / "icon.svg").write_text("""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<rect width="512" height="512" rx="104" fill="#0b1518"/>
<circle cx="256" cy="262" r="174" fill="#255d46"/>
<path d="M120 292C170 184 232 142 292 160c40 12 76 48 100 99-44-18-83-14-116 11 49 4 85 27 112 69-55-24-107-29-153-13-43 15-82 3-115-34z" fill="#8fd3a9"/>
<path d="M231 297l35-87 35 87-35 61z" fill="#f19b4b"/>
<circle cx="266" cy="200" r="18" fill="#ffd166"/>
</svg>
""", encoding="utf-8")

preset = root / "export_presets.cfg"
es = preset.read_text(encoding="utf-8").replace("version/code=3", "version/code=5").replace('version/name="1.1.0"', 'version/name="1.1.2"')
preset.write_text(es, encoding="utf-8")
