"""
Synthetic data generator for the STAR Regional Intelligence System.
Produces realistic teacher, school, training, and NAT score records
based on Philippine DepEd regional structure.
"""

import pandas as pd
import numpy as np
import random
import json
from pathlib import Path

random.seed(42)
np.random.seed(42)

# ---------------------------------------------------------------------------
# Reference data — Philippine regions and divisions
# ---------------------------------------------------------------------------

REGIONS = {
    "Region I": ["Ilocos Norte", "Ilocos Sur", "La Union", "Pangasinan"],
    "Region II": ["Batanes", "Cagayan", "Isabela", "Nueva Vizcaya", "Quirino"],
    "Region III": ["Aurora", "Bataan", "Bulacan", "Nueva Ecija", "Pampanga", "Tarlac", "Zambales"],
    "Region IV-A": ["Batangas", "Cavite", "Laguna", "Quezon", "Rizal"],
    "Region IV-B": ["Marinduque", "Occidental Mindoro", "Oriental Mindoro", "Palawan", "Romblon"],
    "Region V": ["Albay", "Camarines Norte", "Camarines Sur", "Catanduanes", "Masbate", "Sorsogon"],
    "Region VI": ["Aklan", "Antique", "Capiz", "Guimaras", "Iloilo", "Negros Occidental"],
    "Region VII": ["Bohol", "Cebu", "Negros Oriental", "Siquijor"],
    "Region VIII": ["Biliran", "Eastern Samar", "Leyte", "Northern Samar", "Samar", "Southern Leyte"],
    "Region IX": ["Zamboanga del Norte", "Zamboanga del Sur", "Zamboanga Sibugay"],
    "Region X": ["Bukidnon", "Camiguin", "Lanao del Norte", "Misamis Occidental", "Misamis Oriental"],
    "Region XI": ["Davao de Oro", "Davao del Norte", "Davao del Sur", "Davao Occidental", "Davao Oriental"],
    "Region XII": ["Cotabato", "Sarangani", "South Cotabato", "Sultan Kudarat"],
    "Region XIII": ["Agusan del Norte", "Agusan del Sur", "Dinagat Islands", "Surigao del Norte", "Surigao del Sur"],
    "NCR": ["Manila", "Quezon City", "Caloocan", "Pasig", "Taguig"],
    "CAR": ["Abra", "Apayao", "Benguet", "Ifugao", "Kalinga", "Mountain Province"],
    "BARMM": ["Basilan", "Lanao del Sur", "Maguindanao", "Sulu", "Tawi-Tawi"],
}

# Geographic disadvantage: remote/island/conflict-affected areas
GEOGRAPHIC_DISADVANTAGE = {
    "Batanes": 0.9, "Palawan": 0.8, "Camiguin": 0.7, "Dinagat Islands": 0.85,
    "Tawi-Tawi": 0.95, "Sulu": 0.95, "Basilan": 0.9, "Maguindanao": 0.85,
    "Lanao del Sur": 0.85, "Eastern Samar": 0.75, "Northern Samar": 0.75,
    "Samar": 0.7, "Quirino": 0.7, "Apayao": 0.8, "Ifugao": 0.75,
    "Mountain Province": 0.7, "Kalinga": 0.65, "Agusan del Sur": 0.65,
    "Surigao del Sur": 0.6, "Romblon": 0.65, "Marinduque": 0.6,
    "Masbate": 0.7, "Catanduanes": 0.65, "Occidental Mindoro": 0.6,
    "Oriental Mindoro": 0.55,
}

SUBJECTS = ["Biology", "Chemistry", "Physics", "Earth Science", "General Science", "Mathematics", "Statistics"]

SPECIALIZATIONS = [
    "Biology", "Chemistry", "Physics", "Earth Science", "General Science",
    "Mathematics", "Statistics", "Agriculture", "Education", "English",
    "Filipino", "Social Studies", "Physical Education", "Technology"
]

# Subject-to-valid-specialization mapping
SUBJECT_VALID_SPECIALIZATIONS = {
    "Biology": ["Biology", "General Science"],
    "Chemistry": ["Chemistry", "General Science"],
    "Physics": ["Physics", "General Science"],
    "Earth Science": ["Earth Science", "General Science"],
    "General Science": ["Biology", "Chemistry", "Physics", "Earth Science", "General Science"],
    "Mathematics": ["Mathematics", "Statistics"],
    "Statistics": ["Mathematics", "Statistics"],
}

SCHOOL_TYPES = ["Elementary", "Junior High", "Senior High", "Integrated"]
TRAINING_TYPES = [
    "STAR Basic Science Training",
    "STAR Advanced Science Seminar",
    "STAR Math Enhancement Program",
    "STAR Regional Science Camp",
    "STAR Leadership for Science Teachers",
    "STAR Physics Upskilling Workshop",
    "STAR Biology Specialization Course",
    "STAR Chemistry Lab Techniques",
    "STAR STEM Integration Workshop",
    "STAR Regional Coaching Program",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def geo_weight(division: str) -> float:
    return GEOGRAPHIC_DISADVANTAGE.get(division, random.uniform(0.1, 0.45))


def biased_specialization(subject: str, mismatch_prob: float) -> str:
    valid = SUBJECT_VALID_SPECIALIZATIONS[subject]
    if random.random() < mismatch_prob:
        invalid = [s for s in SPECIALIZATIONS if s not in valid]
        return random.choice(invalid)
    return random.choice(valid)


def generate_schools(n_per_division: int = 8) -> pd.DataFrame:
    rows = []
    school_id = 1
    for region, divisions in REGIONS.items():
        for division in divisions:
            geo = geo_weight(division)
            n = max(4, int(n_per_division * (1 + geo * 0.5)))
            for _ in range(n):
                ltr = int(np.random.normal(40, 15))
                ltr = max(10, min(80, ltr))
                if geo > 0.7:
                    ltr = max(ltr, 35)
                rows.append({
                    "school_id": f"SCH{school_id:04d}",
                    "school_name": f"{division} {random.choice(SCHOOL_TYPES)} School {school_id}",
                    "school_type": random.choice(SCHOOL_TYPES),
                    "division": division,
                    "region": region,
                    "learner_teacher_ratio": ltr,
                    "is_geographically_isolated": 1 if geo > 0.65 else 0,
                    "geographic_disadvantage_score": round(geo, 3),
                })
                school_id += 1
    return pd.DataFrame(rows)


def generate_teachers(schools_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    teacher_id = 1
    for _, school in schools_df.iterrows():
        region = school["region"]
        division = school["division"]
        geo = school["geographic_disadvantage_score"]

        # More teachers in remote areas to reflect larger deployment challenges
        n_teachers = random.randint(3, 10)
        # Mismatch probability is higher in underserved areas
        mismatch_prob = min(0.7, 0.15 + geo * 0.6)

        for _ in range(n_teachers):
            subject = random.choice(SUBJECTS)
            specialization = biased_specialization(subject, mismatch_prob)
            experience = int(np.random.exponential(8))
            experience = max(1, min(35, experience))
            training_count = int(np.random.poisson(2 - geo * 1.5))
            training_count = max(0, training_count)
            rows.append({
                "teacher_id": f"TCH{teacher_id:05d}",
                "school_id": school["school_id"],
                "division": division,
                "region": region,
                "subject_taught": subject,
                "specialization": specialization,
                "years_experience": experience,
                "training_count": training_count,
                "employment_status": random.choices(
                    ["Permanent", "Provisional", "Contractual"],
                    weights=[0.65, 0.2, 0.15]
                )[0],
            })
            teacher_id += 1
    return pd.DataFrame(rows)


def generate_training_logs(teachers_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    log_id = 1
    for _, teacher in teachers_df.iterrows():
        for _ in range(int(teacher["training_count"])):
            year = random.randint(2019, 2024)
            rows.append({
                "log_id": f"LOG{log_id:06d}",
                "teacher_id": teacher["teacher_id"],
                "division": teacher["division"],
                "region": teacher["region"],
                "training_name": random.choice(TRAINING_TYPES),
                "year": year,
                "modality": random.choices(
                    ["Face-to-face", "Online", "Blended"],
                    weights=[0.5, 0.3, 0.2]
                )[0],
            })
            log_id += 1
    return pd.DataFrame(rows)


def generate_nat_scores() -> pd.DataFrame:
    rows = []
    for region, divisions in REGIONS.items():
        for division in divisions:
            geo = geo_weight(division)
            # NAT scores inversely correlated with geographic disadvantage
            base_science = max(30, min(80, int(np.random.normal(55 - geo * 25, 5))))
            base_math = max(30, min(80, int(np.random.normal(53 - geo * 22, 5))))
            rows.append({
                "division": division,
                "region": region,
                "nat_science_mps": base_science,
                "nat_math_mps": base_math,
                "year": 2023,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    out = Path(__file__).parent
    out.mkdir(parents=True, exist_ok=True)

    print("Generating schools...")
    schools = generate_schools()
    schools.to_csv(out / "schools.csv", index=False)
    print(f"  {len(schools)} schools across {schools['division'].nunique()} divisions")

    print("Generating teachers...")
    teachers = generate_teachers(schools)
    teachers.to_csv(out / "teachers.csv", index=False)
    print(f"  {len(teachers)} teacher records")

    print("Generating training logs...")
    logs = generate_training_logs(teachers)
    logs.to_csv(out / "training_logs.csv", index=False)
    print(f"  {len(logs)} training log entries")

    print("Generating NAT scores...")
    nat = generate_nat_scores()
    nat.to_csv(out / "nat_scores.csv", index=False)
    print(f"  {len(nat)} division NAT records")

    print("\nDone. Files written to:", out)
    print("  schools.csv, teachers.csv, training_logs.csv, nat_scores.csv")


if __name__ == "__main__":
    main()
