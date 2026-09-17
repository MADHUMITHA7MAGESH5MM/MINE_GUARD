import os
import random
import pandas as pd
from sentence_transformers import SentenceTransformer, util


def locate_file(filename: str) -> str:
    """Searches common project locations for the target file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()

    search_paths = [
        os.path.join(cwd, filename),
        os.path.join(script_dir, filename),
        os.path.abspath(os.path.join(script_dir, "..", filename)),
        os.path.abspath(os.path.join(cwd, "..", filename)),
        os.path.abspath(os.path.join(script_dir, "..", "data", filename)),
        os.path.abspath(os.path.join(cwd, "data", filename)),
    ]

    for path in search_paths:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        f"Could not locate '{filename}'. Checked locations:\n"
        + "\n".join(f" - {p}" for p in search_paths)
    )


def alphabetize_rules(rule_str: str) -> str:
    """Sorts semicolon-delimited rule tags alphabetically."""
    if not rule_str or pd.isna(rule_str):
        return ""
    tags = [t.strip() for t in str(rule_str).split(";") if t.strip()]
    return "; ".join(sorted(tags))


def generate_gritty_dataset():
    # 1. Locate and load the existing baseline dataset
    input_csv_path = locate_file("final_sif.csv")
    print(f"Found base file at: {input_csv_path}")
    df_existing = pd.read_csv(input_csv_path)

    # Ensure existing rules follow alphabetical sorting
    if "rules" in df_existing.columns:
        df_existing["rules"] = df_existing["rules"].apply(alphabetize_rules)

    existing_reports = df_existing["report"].astype(str).tolist()
    initial_count = len(df_existing)
    target_total = 1000
    needed_rows = target_total - initial_count

    print(f"Loaded {initial_count} baseline reports. Generating {needed_rows} new records...")

    # 2. Initialize Critic Agent (NLP Embedding Model)
    print("Initializing Critic Agent (Sentence-Transformers)...")
    critic_model = SentenceTransformer("all-MiniLM-L6-v2")
    active_embeddings = critic_model.encode(existing_reports, convert_to_tensor=True)

    # 3. Domain Entity Perturbation Banks
    actors = [
        "exhausted night-shift mechanic",
        "derrickman",
        "instrumentation tech",
        "third-party rigger",
        "roustabout",
        "contract welder",
        "mud logger",
        "crane operator",
        "scaffolding lead",
        "pipeline technician",
    ]

    environments = [
        "mud logging unit",
        "offshore flare deck",
        "pig launcher shed",
        "high-voltage substation",
        "mud pits",
        "nitrogen purge header",
        "shaker deck",
        "BOP stack",
        "compressor manifold",
        "pipe rack staging area",
    ]

    # Format: (raw_failure_text, SIF_rating, rules_string, mechanism_of_harm)
    failures = [
        (
            "a hydraulic fluid pinhole leak ignited on the pump skid",
            "HIGH",
            "Hot Work; Bypassing Safety Controls",
            "Ignition of pressurized hydrocarbon fluid creates immediate severe fire hazard.",
        ),
        (
            "a tensioned 3/4-inch tag line snapped and whipped across the deck",
            "HIGH",
            "Line of Fire; Safe Mechanical Lifting",
            "Whipping tensioned wire rope releases fatal kinetic energy.",
        ),
        (
            "a 480V motor control center cubicle was found open and energized with temporary jumpers bypassing the interlock",
            "HIGH",
            "Bypassing Safety Controls; Energy Isolation",
            "Bypassed electrical interlocks expose personnel to fatal arc flash.",
        ),
        (
            "sparks from a handheld grinder fell through grating onto oil-soaked rags on the lower level",
            "HIGH",
            "Hot Work",
            "Uncontained ignition source directly above combustible fluids risks major facility fire.",
        ),
        (
            "a contract welder struck an arc on a live 6-inch gas flowline misidentified on the permit as decommissioned",
            "HIGH",
            "Energy Isolation; Work Authorization",
            "Penetration or heat input on live pressurized gas line risks catastrophic explosion.",
        ),
        (
            "the pedestal crane slew motor blew a high-pressure seal, causing the suspended load to drift uncontrolled",
            "HIGH",
            "Line of Fire; Safe Mechanical Lifting",
            "Uncontrolled movement of heavy suspended load risks fatal impact or crush.",
        ),
        (
            "an uncalibrated fixed sensor failed to alarm during an H2S spike",
            "HIGH",
            "Bypassing Safety Controls",
            "Failure of fixed toxic gas detection leads directly to rapid asphyxiation.",
        ),
        (
            "unsecured scaffolding planks slipped off ledger supports while carrying load",
            "HIGH",
            "Working at Height",
            "Structural displacement of working platform causes fatal fall from height.",
        ),
        (
            "a water bowser driver brushed a traffic cone while reversing at low parking speed",
            "LOW",
            "Driving",
            "Minimal kinetic energy and contact with flexible stationary marker.",
        ),
        (
            "a localized static discharge was felt after confirming complete lockout/tagout verification",
            "LOW",
            "Energy Isolation",
            "Hazardous energy isolated; minor static potential carries no systemic harm.",
        ),
        (
            "a hand tool was dropped from waist height and struck a steel grate without contacting personnel",
            "LOW",
            "Line of Fire",
            "Low elevation and mass resulted in minimal gravitational energy transfer.",
        ),
        (
            "a minor surface cut on the forearm occurred while adjusting a certified full-body harness strap",
            "LOW",
            "Working at Height",
            "Surface contact injury unrelated to mechanical failure of primary fall arrest system.",
        ),
    ]

    contexts = [
        "during a frantic end-of-shift handover.",
        "compounded by severe night-shift fatigue.",
        "amidst conflicting simultaneous operations (SIMOPS).",
        "while heavy monsoon rain obscured visibility.",
        "in freezing temperatures that stiffened hydraulic controls.",
        "under substandard auxiliary lighting.",
        "while rushing to meet a drilling schedule deadline.",
    ]

    # Non-repetitive grammatical templates
    templates = [
        "{failure_cap} near the {environment} while the {actor} was working {context}",
        "Midway through operations at the {environment}, {failure}, narrowly missing the {actor} {context}",
        "At 03:00 hours, the {actor} discovered that {failure} near the {environment} {context}",
        "Adjacent to the {environment}, {failure} in close proximity to the {actor} {context}",
        "While inspecting the {environment}, the {actor} logged that {failure} {context}",
    ]

    new_rows = []

    while len(new_rows) < needed_rows:
        actor = random.choice(actors)
        env = random.choice(environments)
        fail_text, sif, rule_tag, reason = random.choice(failures)
        context = random.choice(contexts)
        template = random.choice(templates)

        fail_cap = fail_text[0].upper() + fail_text[1:]
        report_text = template.format(
            failure=fail_text,
            failure_cap=fail_cap,
            environment=env,
            actor=actor,
            context=context,
        )

        # 4. Critic Agent Validation Loop
        candidate_embedding = critic_model.encode(report_text, convert_to_tensor=True)
        similarity = util.cos_sim(candidate_embedding, active_embeddings)

        # Retain candidate if structurally distinct (similarity < 0.92)
        if similarity.max().item() < 0.92:
            new_rows.append({
                "report": report_text,
                "sif": sif,
                "rules": alphabetize_rules(rule_tag),
                "reason": reason,
            })

            # Update critic embeddings every 50 accepted samples
            if len(new_rows) % 50 == 0:
                print(f"Validated {len(new_rows)} / {needed_rows} generated samples...")
                combined_texts = existing_reports + [r["report"] for r in new_rows]
                active_embeddings = critic_model.encode(combined_texts, convert_to_tensor=True)

    # 5. Export Combined Dataset
    df_new = pd.DataFrame(new_rows)
    df_final = pd.concat([df_existing, df_new], ignore_index=True)

    output_dir = os.path.dirname(input_csv_path)
    output_path = os.path.join(output_dir, "final_sif_1000.csv")
    df_final.to_csv(output_path, index=False)

    print("\nGeneration Complete:")
    print(f" - Baseline rows: {initial_count}")
    print(f" - Added rows:    {len(new_rows)}")
    print(f" - Total rows:    {len(df_final)}")
    print(f" - Saved to:      {output_path}")


if __name__ == "__main__":
    generate_gritty_dataset()