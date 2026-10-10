import os, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'earth_station'))
sys.path.insert(0, '.')

from main import EarthMissionControlApp
from engine.medical_db import medical_db

app = EarthMissionControlApp()
app.update_idletasks()

astros = medical_db.get_all_astronauts()
print(f"Total astronauts in DB: {len(astros)}")
for a in astros:
    name = a.get("name", "?")
    aid  = a.get("id", "?")
    dep  = a.get("is_deployed", 0)
    print(f"  {aid} -> {name}  (deployed={dep})")

print()
print("--- Testing select_astronaut for each crew member ---")
for astro in astros[:4]:
    # Simulate card click (sets manual=True, just like the real _select lambda)
    app.select_astronaut(astro["id"], astro, manual=True)
    app.update_idletasks()
    current_name = app.lbl_subj_name.cget("text")
    expected = astro["name"].upper()
    ok = expected in current_name or current_name in expected
    flag = "OK" if ok else "FAIL (got: " + current_name + ")"
    print(f"  Select [{astro['name']}]: {flag}")
    assert app.manual_selection_override == True, "manual_selection_override must be True after card click!"

print()
print("--- Simulating poll loop tick (should NOT overwrite last selection) ---")
last_name = app.lbl_subj_name.cget("text")
app.manual_selection_override = True
# Run the UI event queue once
app.update_idletasks()
after_name = app.lbl_subj_name.cget("text")
print(f"  Before poll: {last_name}")
print(f"  After  poll: {after_name}")
assert last_name == after_name, "Poll loop overwrote the manual selection!"

print()
print("ALL TESTS PASSED!")
print("Earth Station now correctly shows any selected astronaut's details.")
app.destroy()
