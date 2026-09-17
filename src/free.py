from entity_extractor import build_enriched_text

report = "Worker climbed on top of a tank without fall protection."

print(build_enriched_text(report))
print(build_enriched_text(
    "Crane operator lifted a suspended load without an exclusion zone."
))
print(build_enriched_text(
    "Technician opened a live electrical panel for maintenance."
))