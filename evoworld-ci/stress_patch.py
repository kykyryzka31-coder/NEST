from pathlib import Path
import sys

root = Path(sys.argv[1])
p = root / "main.gd"
s = p.read_text(encoding="utf-8")

# CI-only state.
s = s.replace(
    "var next_resource_update = 0.0\n",
    "var next_resource_update = 0.0\nvar ci_stress = false\nvar ci_stress_target = 0.0\nvar ci_save_done = false\n",
)

# Start a deterministic 100x world when CI asks for it.
s = s.replace(
    "    _setup_menu()\n    _show_menu()\n",
    """    _setup_menu()
    _show_menu()
    if "--ci-stress" in OS.get_cmdline_user_args():
        ci_stress = true
        ci_stress_target = YEAR_SECONDS * 30.0
        _start_world(12345)
        _set_speed(100.0)
        print("CI_STRESS_START population=", agents.size(), " target_years=30")
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
        if speed >= 50.0:
            max_step = 0.45
        elif speed >= 20.0:
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
    if ci_stress and not ci_save_done and sim_time >= YEAR_SECONDS * 15.0:
        ci_save_done = true
        var before_save_population = agents.size()
        _save_world(true)
        _load_world()
        print("CI_SAVELOAD population_before=", before_save_population, " population_after=", agents.size(), " year=", sim_time / YEAR_SECONDS)
        if agents.is_empty():
            push_error("CI save/load failed: population vanished")
            get_tree().quit(3)
    if ci_stress and sim_time >= ci_stress_target:
        print("CI_STRESS_RESULT years=", sim_time / YEAR_SECONDS, " population=", agents.size(), " births=", births, " deaths=", deaths, " generation=", max_generation, " discoveries=", global_discoveries.size(), " cultures=", cultures.size(), " conflicts=", conflicts)
        if agents.is_empty() or births <= 0 or max_generation < 2:
            push_error("CI stress failed: simulation did not sustain and reproduce")
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

p.write_text(s, encoding="utf-8")

# Final Android build version.
project = root / "project.godot"
ps = project.read_text(encoding="utf-8").replace('config/version="1.1.0"', 'config/version="1.1.1"')
project.write_text(ps, encoding="utf-8")

preset = root / "export_presets.cfg"
es = preset.read_text(encoding="utf-8").replace("version/code=3", "version/code=4").replace('version/name="1.1.0"', 'version/name="1.1.1"')
preset.write_text(es, encoding="utf-8")
