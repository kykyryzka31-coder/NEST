from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")

s = s.replace(
    "var next_resource_update = 0.0\n",
    "var next_resource_update = 0.0\nvar ci_stress = false\nvar ci_stress_target = 0.0\n",
)

s = s.replace(
    "    _setup_menu()\n    _show_menu()\n",
    """    _setup_menu()
    _show_menu()
    if "--ci-stress" in OS.get_cmdline_user_args():
        ci_stress = true
        ci_stress_target = YEAR_SECONDS * 40.0
        _start_world(12345)
        _set_speed(100.0)
        print("CI_STRESS_START population=", agents.size(), " target_years=40")
""",
)

s = s.replace(
    "    _refresh_ui()\n\nfunc _simulate_step(dt: float) -> void:\n",
    """    _refresh_ui()
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

p.write_text(s, encoding="utf-8")
