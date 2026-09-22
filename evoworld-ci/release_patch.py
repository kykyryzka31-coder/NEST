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
