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
        var before_wildlife = wildlife.size()
        _save_world(true)
        _load_world()
        auto_slow = false
        _set_speed(100.0)
        print("CI_SAVELOAD population_before=", before_population, " population_after=", agents.size(), " wildlife_before=", before_wildlife, " wildlife_after=", wildlife.size(), " births_before=", before_births, " births_after=", births, " year=", sim_time / YEAR_SECONDS)
        if agents.size() != before_population or wildlife.size() != before_wildlife or births != before_births:
            push_error("CI save/load failed: world state changed")
            get_tree().quit(3)
    if ci_stress and sim_time >= ci_stress_target:
        print("CI_STRESS_RESULT years=", sim_time / YEAR_SECONDS, " population=", agents.size(), " wildlife=", wildlife.size(), " deer=", _count_wildlife("deer"), " wolves=", _count_wildlife("wolf"), " births=", births, " deaths=", deaths, " generation=", max_generation, " discoveries=", global_discoveries.size(), " cultures=", cultures.size(), " conflicts=", conflicts)
        if agents.size() < 10 or wildlife.size() < 3 or births < 8 or max_generation < 2:
            push_error("CI stress failed: population did not sustain generations")
            get_tree().quit(2)
        else:
            get_tree().quit(0)

func _simulate_step(dt: float) -> void:
""",
)

p.write_text(s, encoding="utf-8")
