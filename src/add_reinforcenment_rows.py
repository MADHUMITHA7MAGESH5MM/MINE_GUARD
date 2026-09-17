import os
import pandas as pd

REINFORCEMENT_ROWS = [
    ("A crane operator swung a loaded pallet directly over two technicians working on the ground below.",
     "HIGH", "Line of Fire;Safe Mechanical Lifting",
     "Positioning a suspended load directly above personnel exposes them to a potentially fatal strike if the load or rigging fails."),

    ("Employee stood beneath an overhead crane hook while it repositioned a large steel beam across the yard.",
     "HIGH", "Line of Fire;Safe Mechanical Lifting",
     "Standing under a moving overhead load is a direct exposure to a heavy falling-object hazard."),

    ("Rigger walked underneath a raised excavator bucket to reach tools on the far side of the site.",
     "HIGH", "Line of Fire",
     "Passing beneath a raised, heavy piece of equipment exposes the worker to being crushed if it drops or swings unexpectedly."),

    ("A technician reached up to adjust a sling while a suspended engine block hung directly above his head.",
     "HIGH", "Line of Fire;Safe Mechanical Lifting",
     "Working directly beneath a suspended heavy object puts the worker in the direct path of a fatal strike if the load shifts."),

    ("Two workers paused for a break in the shade cast by a crane's suspended concrete slab overhead.",
     "HIGH", "Line of Fire;Safe Mechanical Lifting",
     "Remaining under a suspended load for any reason, including incidentally, carries the same fatal strike potential as working there."),

    ("A forklift carried a raised pallet of pipe fittings across a walkway while a pedestrian passed directly beneath the forks.",
     "HIGH", "Line of Fire",
     "A raised load passing over a pedestrian is a direct line-of-fire exposure to a falling-object strike."),

    ("Maintenance crew stood under a gantry crane's load path to guide a hanging valve assembly into position by hand.",
     "HIGH", "Line of Fire;Safe Mechanical Lifting",
     "Manually guiding a load from directly beneath it removes any margin of safety if the load drops."),

    ("A worker crossed under an active tower crane's boom line to shortcut to the site office, without checking for an ongoing lift.",
     "HIGH", "Line of Fire;Safe Mechanical Lifting",
     "Crossing beneath an active crane's load path exposes a person to being struck without warning by a load or falling rigging."),

    ("The crane's exclusion zone was clearly marked and no personnel entered the area beneath the suspended load during the entire lift.",
     "LOW", "Line of Fire",
     "Maintaining the exclusion zone meant no one was ever exposed to the suspended load overhead."),

    ("Load was lifted only after all personnel moved outside the marked barrier line surrounding the lift area.",
     "LOW", "Safe Mechanical Lifting;Line of Fire",
     "Personnel were cleared from the hazard zone before the lift began, removing any exposure to the suspended load."),

    ("A pallet was lifted two feet off the ground to check the forklift's hydraulics, with no one within ten metres of the load.",
     "LOW", "Safe Mechanical Lifting",
     "Minimal lift height and complete absence of nearby personnel meant no meaningful exposure existed."),
]

# 1. Locate the correct final_sif.csv file in the data folder
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, "..", "data", "final_sif.csv")

# 2. Create the new reinforcement rows DataFrame
new = pd.DataFrame(REINFORCEMENT_ROWS, columns=['report', 'sif', 'rules', 'reason'])

# 3. Load the existing master dataset
existing = pd.read_csv(data_path)

# 4. Combine and remove any duplicate reports
combined = pd.concat([existing, new], ignore_index=True).drop_duplicates(subset='report').reset_index(drop=True)

# 5. Save directly back to the master dataset
combined.to_csv(data_path, index=False)
print(f"Added {len(new)} rows. Dataset now has {len(combined)} unique rows.")
print(combined['sif'].value_counts())