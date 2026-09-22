from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
p = root / "main.gd"
s = p.read_text(encoding="utf-8")

def replace_once(old: str, new: str):
    global s
    if old not in s:
        raise RuntimeError("Polish patch target not found: " + old[:140])
    s = s.replace(old, new, 1)

# Stable predator founders: each pack starts with a breeding pair.
replace_once(
    '''    var pack_centers = [Vector3(-5.0, 0.0, -28.0), Vector3(7.0, 0.0, 28.0)]
    for pack in pack_centers:
        for i in range(2):
            _spawn_animal("predator", _clamp_world(pack + Vector3(rng.randf_range(-4.0, 4.0), 0.0, rng.randf_range(-4.0, 4.0))))
''',
    '''    var pack_centers = [Vector3(-18.0, 0.0, -22.0), Vector3(18.0, 0.0, 20.0)]
    for pack in pack_centers:
        _spawn_animal("predator", _clamp_world(pack + Vector3(-1.2, 0.0, 0.5)), 2.8, "F")
        _spawn_animal("predator", _clamp_world(pack + Vector3(1.2, 0.0, -0.5)), 3.1, "M")
'''
)
s = s.replace(
    '"speed": rng.randf_range(1.8, 2.5) if species == "grazer" else rng.randf_range(2.1, 2.9),',
    '"speed": rng.randf_range(1.8, 2.45) if species == "grazer" else rng.randf_range(2.85, 3.45),',
    1
)
s = s.replace(
    'var prey = _nearest_grazer_to_position((animal["root"] as Node3D).position, 30.0)',
    'var prey = _nearest_grazer_to_position((animal["root"] as Node3D).position, 44.0)',
    1
)
s = s.replace(
    'if predators * 6 >= maxi(grazers, 1):',
    'if predators * 5 >= maxi(grazers, 1):',
    1
)
s = s.replace(
    'var cooldown = YEAR_SECONDS * (0.55 if species == "grazer" else 1.10)',
    'var cooldown = YEAR_SECONDS * (0.55 if species == "grazer" else 0.90)',
    1
)
s = s.replace(
    'var chance = (0.12 + float(animal["fertility"]) * 0.16) * density_factor',
    'var chance = (0.12 + float(animal["fertility"]) * (0.16 if species == "grazer" else 0.22)) * density_factor',
    1
)

# Culture continuity: require a meaningful social cluster and preserve the identity
# already held by a substantial part of that cluster.
s = s.replace(
    '        if component.size() >= 4:\n            components.append(component)\n',
    '        if component.size() >= 6:\n            components.append(component)\n',
    1
)
replace_once(
    '''        var culture = _best_matching_culture(centroid, dialect)
        if culture == null:
            culture = _create_culture(centroid, dialect)
''',
    '''        var culture = _dominant_existing_culture(component)
        if culture == null:
            culture = _best_matching_culture(centroid, dialect)
        if culture == null:
            culture = _create_culture(centroid, dialect)
'''
)

culture_helper = r'''
func _dominant_existing_culture(members: Array) -> Variant:
    var counts: Dictionary = {}
    for member in members:
        var cid = int(member["culture_id"])
        if cid < 0:
            continue
        counts[cid] = int(counts.get(cid, 0)) + 1
    var best_id = -1
    var best_count = 0
    for cid in counts.keys():
        var count = int(counts[cid])
        if count > best_count:
            best_count = count
            best_id = int(cid)
    if best_id >= 0 and best_count >= maxi(2, int(ceil(float(members.size()) * 0.35))):
        return _culture_by_id(best_id)
    return null

'''
replace_once(
    'func _best_matching_culture(center: Vector3, dialect: float) -> Variant:\n',
    culture_helper + 'func _best_matching_culture(center: Vector3, dialect: float) -> Variant:\n'
)
s = s.replace(
    '        if int(culture["population"]) <= 0:\n            continue\n',
    '',
    1
)
s = s.replace('var score = distance + dialect_diff * 30.0', 'var score = distance + dialect_diff * 24.0', 1)
s = s.replace(
    'if distance < 20.0 and dialect_diff < 0.25 and score < best_score:',
    'if distance < 27.0 and dialect_diff < 0.30 and score < best_score:',
    1
)

# Cross-cultural meetings are a little easier to register, while actual fighting
# still depends on aggression, scarcity, cooperation and relations.
s = s.replace('var nearby = _nearby_agents(a, 4.0)', 'var nearby = _nearby_agents(a, 6.0)', 1)

# WorldBox-like recovery tool: player can repopulate wildlife after a catastrophe.
replace_once(
    '    _add_hud_button(god_row, "Еда", _god_food_burst)\n',
    '    _add_hud_button(god_row, "Еда", _god_food_burst)\n    _add_hud_button(god_row, "Животные", _god_add_animals)\n'
)
god_animals = r'''
func _god_add_animals() -> void:
    if animals.size() >= MAX_ANIMALS - 10:
        _add_history("В мире уже слишком много животных.", false)
        return
    var center = Vector3(camera.position.x, 0.0, clampf(camera.position.z - 18.0, -WORLD_HALF, WORLD_HALF))
    for i in range(8):
        _spawn_animal("grazer", _clamp_world(center + Vector3(rng.randf_range(-5.0, 5.0), 0.0, rng.randf_range(-5.0, 5.0))))
    _spawn_animal("predator", _clamp_world(center + Vector3(-3.0, 0.0, 3.0)), 3.0, "F")
    _spawn_animal("predator", _clamp_world(center + Vector3(3.0, 0.0, -3.0)), 3.0, "M")
    _add_history("Игрок выпустил в мир стадо и пару хищников.", false)

'''
replace_once('func _god_lightning() -> void:\n', god_animals + 'func _god_lightning() -> void:\n')

# Show ecosystem split in the statistics panel.
replace_once(
    '    stats_label.text = "Средние гены:',
    '    var grazer_count = _animal_species_count("grazer")\n    var predator_count = _animal_species_count("predator")\n    stats_label.text = "Средние гены:'
)
replace_once(
    '        avg_age / n, females, males, children, births, deaths\n    ]',
    '        avg_age / n, females, males, children, births, deaths\n    ] + "    |    Фауна: травоядные %d • хищники %d • родилось %d • погибло %d" % [grazer_count, predator_count, animal_births, animal_deaths]'
)

# CI reports active cultures, not merely every culture ever observed.
active_helper = r'''
func _active_culture_count() -> int:
    var count = 0
    for culture in cultures:
        if int(culture["population"]) > 0:
            count += 1
    return count

'''
replace_once('func _best_matching_culture(center: Vector3, dialect: float) -> Variant:\n',
             active_helper + 'func _best_matching_culture(center: Vector3, dialect: float) -> Variant:\n')

s = s.replace(
    '" cultures=", cultures.size(), " conflicts=", conflicts, " animals=",',
    '" cultures=", cultures.size(), " active_cultures=", _active_culture_count(), " conflicts=", conflicts, " animals=",',
    1
)

p.write_text(s, encoding="utf-8")

project = root / "project.godot"
ps = project.read_text(encoding="utf-8")
ps = re.sub(r'config/version="[^"]+"', 'config/version="1.2.1"', ps)
project.write_text(ps, encoding="utf-8")

preset = root / "export_presets.cfg"
es = preset.read_text(encoding="utf-8")
es = re.sub(r'version/code=\d+', 'version/code=7', es)
es = re.sub(r'version/name="[^"]+"', 'version/name="1.2.1"', es)
preset.write_text(es, encoding="utf-8")
