"""
Job Refinement and User Skills Categorization Engine
====================================================
Reads:
1. User profile text files in `users/*.txt`
2. Raw scraped jobs in `data/scraped_jobs.json`

Matches and categorizes jobs for each user based on their specific skills.
Produces:
1. `data/refined_jobs.json` (categorized jobs per user + user metadata + stats)
2. `data/jobs.json` (synced for dashboard and consumer compatibility)

Run with:
    python scripts/refine_jobs.py
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone

PROJECT_DIR = Path(__file__).parent.parent
USERS_DIR   = PROJECT_DIR / "users"
DATA_DIR    = PROJECT_DIR / "data"
SCRAPED_PATH = DATA_DIR / "scraped_jobs.json"
REFINED_PATH = DATA_DIR / "refined_jobs.json"
JOBS_PATH    = DATA_DIR / "jobs.json"

DATA_DIR.mkdir(exist_ok=True)
USERS_DIR.mkdir(exist_ok=True)


def parse_user_profile(txt_path: Path) -> dict:
    """Parse a user profile .txt file into a structured dictionary."""
    content = txt_path.read_text(encoding="utf-8")
    user_id = txt_path.stem.lower()
    
    profile = {
        "id": user_id,
        "name": user_id.replace("_", " ").title(),
        "email": f"{user_id}@example.com",
        "phone": "[Phone Number]",
        "role": "Senior Machine Learning Engineer",
        "experience": "5+ Years",
        "target_locations": "India, UK, Australia",
        "summary": "",
        "skills": [],
        "exclusions": ["intern", "graduate", "junior", "principal", "staff"]
    }

    current_section = None
    summary_lines = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Check for header key: value
        if ":" in line and not line.startswith(("-", "*")):
            k, v = line.split(":", 1)
            k = k.strip().lower()
            v = v.strip()

            if "name" in k:
                profile["name"] = v or profile["name"]
                current_section = None
            elif "email" in k:
                profile["email"] = v or profile["email"]
                current_section = None
            elif "phone" in k:
                profile["phone"] = v or profile["phone"]
                current_section = None
            elif "role" in k or "title" in k:
                profile["role"] = v or profile["role"]
                current_section = None
            elif "experience" in k:
                profile["experience"] = v or profile["experience"]
                current_section = None
            elif "location" in k:
                profile["target_locations"] = v or profile["target_locations"]
                current_section = None
            elif "summary" in k or "bio" in k:
                current_section = "summary"
                if v:
                    summary_lines.append(v)
            elif "skill" in k:
                current_section = "skills"
                if v:
                    profile["skills"].append(v)
            elif "exclusion" in k or "exclude" in k:
                current_section = "exclusions"
                if v:
                    profile["exclusions"] = [x.strip().lower() for x in v.split(",") if x.strip()]
            else:
                current_section = None
        elif line.startswith(("-", "*")):
            item = line.lstrip("-* ").strip()
            if current_section == "skills":
                profile["skills"].append(item)
            elif current_section == "exclusions":
                profile["exclusions"].append(item.lower())
        else:
            if current_section == "summary":
                summary_lines.append(line)

    if summary_lines:
        profile["summary"] = " ".join(summary_lines)

    # Derive short skills summary
    if profile["skills"]:
        profile["skills_summary"] = ", ".join(profile["skills"][:5])
    else:
        profile["skills_summary"] = profile["role"]

    return profile


def extract_keywords_from_skill(skill_str: str) -> list[str]:
    """Generate search keywords and acronyms from a skill description."""
    keywords = set()
    cleaned = re.sub(r"[^\w\s-]", " ", skill_str).lower()
    
    # Split by conjunctions & slashes
    for token in re.split(r"[/&,]|\\band\\b", cleaned):
        t = token.strip()
        if len(t) >= 3:
            keywords.add(t)

    # Look for capitalized acronyms (RecSys, LLM, CTR, NLP, MLOps, RAG, SQL)
    for acr in re.findall(r"\b[A-Za-z0-9]{2,6}\b", skill_str):
        keywords.add(acr.lower())

    # Common domain keyword expansions
    skill_lower = skill_str.lower()
    if "recsys" in skill_lower or "recommendation" in skill_lower:
        keywords.update(["recsys", "recommendation", "recommendations", "recommender", "collaborative filtering"])
    if "ranking" in skill_lower:
        keywords.update(["ranking", "reranking", "re-ranking", "ranker", "candidate generation"])
    if "search" in skill_lower or "retrieval" in skill_lower:
        keywords.update(["search", "retrieval", "semantic search", "information retrieval", "query"])
    if "two-tower" in skill_lower or "two tower" in skill_lower:
        keywords.update(["two-tower", "two tower", "dual tower", "embeddings", "vector search"])
    if "ctr" in skill_lower or "click" in skill_lower:
        keywords.update(["ctr", "click", "click-through", "conversion", "ads ranking"])
    if "personalization" in skill_lower:
        keywords.update(["personalization", "personalisation", "user modeling", "sequence modeling"])
    if "llm" in skill_lower or "generative" in skill_lower or "genai" in skill_lower:
        keywords.update(["llm", "llms", "genai", "generative ai", "generative", "agentic", "agents", "rag", "foundation model"])
    if "nlp" in skill_lower:
        keywords.update(["nlp", "natural language", "transformers", "bert", "huggingface"])
    if "pytorch" in skill_lower:
        keywords.update(["pytorch", "torch"])
    if "mlops" in skill_lower or "serving" in skill_lower or "inference" in skill_lower:
        keywords.update(["mlops", "serving", "inference", "model deployment", "triton", "latency"])
    if "experimentation" in skill_lower or "a/b" in skill_lower:
        keywords.update(["experimentation", "a/b", "ab test", "causal", "bandits", "multi-armed"])

    return [k for k in keywords if len(k) >= 2]


def match_job_for_user(job: dict, user: dict, skill_keywords_map: dict) -> tuple[bool, int, list[str], str, str]:
    """
    Evaluates whether a job matches a user's skills.
    Returns: (is_match, score, matched_skills, fit_category, fit_reason)
    """
    title = job.get("title", "")
    title_lower = title.lower()

    # Check exclusions
    for exc in user.get("exclusions", []):
        if exc and exc in title_lower:
            return False, 0, [], "Excluded", f"Excluded role title matching '{exc}'"

    tech = job.get("tech", "")
    why_fits = job.get("why_fits", "")
    company = job.get("company", "")
    exp_cat_raw = job.get("expCat", "Good")

    full_text = f"{title} {tech} {why_fits}".lower()

    matched_skills = []
    score = 0

    for skill_name, kws in skill_keywords_map.items():
        skill_hit = False
        for kw in kws:
            pattern = r"(?:\b|_)" + re.escape(kw) + r"(?:\b|_)"
            
            # Check in title (highest value)
            if re.search(pattern, title_lower):
                score += 25
                skill_hit = True
                break
            # Check in tech
            elif re.search(pattern, tech.lower()):
                score += 15
                skill_hit = True
                break
            # Check in why_fits
            elif re.search(pattern, why_fits.lower()):
                score += 10
                skill_hit = True
                break

        if skill_hit:
            matched_skills.append(skill_name)

    # General domain baseline points
    if any(term in full_text for term in ["machine learning", "data science", "ai", "mle", "applied scientist"]):
        score += 15

    # If at least one specific skill matches or high domain score
    if matched_skills or score >= 35:
        # Normalize score to 40 - 98 range
        normalized_score = min(98, max(45, score))

        if normalized_score >= 70 or len(matched_skills) >= 3:
            fit_cat = "Strong"
        elif normalized_score >= 50 or len(matched_skills) >= 2:
            fit_cat = "Good"
        else:
            fit_cat = "Stretch" if exp_cat_raw == "Stretch" else "Good"

        if matched_skills:
            fit_reason = f"Matches {len(matched_skills)} of your skills: {', '.join(matched_skills[:3])}."
        else:
            fit_reason = f"General domain match for {user['role']}."

        return True, normalized_score, matched_skills, fit_cat, fit_reason

    return False, score, [], "No Match", "Role does not match user's target skills"


def refine_jobs():
    """Main function to refine scraped jobs against all user profiles."""
    # Ensure scraped jobs exist
    if not SCRAPED_PATH.exists():
        if JOBS_PATH.exists():
            print(f"[refine] Initializing {SCRAPED_PATH} from {JOBS_PATH}...")
            with open(JOBS_PATH, encoding="utf-8") as f:
                existing_data = json.load(f)
            # If existing data is list of jobs
            if isinstance(existing_data, list):
                raw_jobs = existing_data
            elif isinstance(existing_data, dict):
                raw_jobs = existing_data.get("all_jobs") or existing_data.get("jobs", [])
            else:
                raw_jobs = []
            with open(SCRAPED_PATH, "w", encoding="utf-8") as f:
                json.dump(raw_jobs, f, indent=2, ensure_ascii=False)
        else:
            print(f"[refine] Error: Neither {SCRAPED_PATH} nor {JOBS_PATH} found!")
            return None

    with open(SCRAPED_PATH, encoding="utf-8") as f:
        scraped_data = json.load(f)

    if isinstance(scraped_data, dict):
        raw_jobs = scraped_data.get("all_jobs") or scraped_data.get("jobs", [])
    elif isinstance(scraped_data, list):
        raw_jobs = scraped_data
    else:
        raw_jobs = []

    print(f"[refine] Loaded {len(raw_jobs)} scraped jobs from {SCRAPED_PATH}")

    # Find all user text files
    user_files = sorted(list(USERS_DIR.glob("*.txt")))
    if not user_files:
        print(f"[refine] Warning: No user .txt files found in {USERS_DIR}. Creating default chandan.txt...")
        chandan_file = USERS_DIR / "chandan.txt"
        chandan_file.write_text(
            "Name: Chandan Malla\n"
            "Email: chandanmalla@gmail.com\n"
            "Phone: +91 98765 43210\n"
            "Role: Senior Machine Learning Engineer & Applied Scientist\n"
            "Experience: 6+ Years\n"
            "Primary Skills:\n"
            "- Recommendation Systems (RecSys)\n"
            "- Search & Ranking Algorithms\n"
            "- Two-Tower Embeddings & Candidate Generation\n"
            "- CTR Prediction & Click Modeling\n"
            "- Personalization & User Modeling\n"
            "- Large Language Models (LLMs) & Generative AI\n"
            "- PyTorch & Python\n"
            "- MLOps & Low-Latency Inference\n"
            "- Experimentation, A/B Testing & Causal Inference\n",
            encoding="utf-8"
        )
        user_files = [chandan_file]

    users_dict = {}
    now_ist = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M IST")

    for ufile in user_files:
        user = parse_user_profile(ufile)
        uid = user["id"]
        print(f"[refine] Processing profile for '{user['name']}' ({uid}) with {len(user['skills'])} skills...")

        # Build skill keywords map
        skill_kw_map = {s: extract_keywords_from_skill(s) for s in user["skills"]}

        user_matched_jobs = []
        for j in raw_jobs:
            is_match, score, matched_skills, fit_cat, fit_reason = match_job_for_user(j, user, skill_kw_map)
            if is_match:
                # Create a refined job entry
                rj = dict(j)
                rj["matched_skills"] = matched_skills
                rj["match_score"] = score
                rj["user_fit_reason"] = fit_reason
                # Update expCat if refined fit is stronger
                if fit_cat in ["Strong", "Good", "Stretch"]:
                    rj["expCat"] = fit_cat
                    rj["exp"] = f"{fit_cat} fit ({fit_reason})"
                user_matched_jobs.append(rj)

        # Sort jobs by match_score descending, then id
        user_matched_jobs.sort(key=lambda x: (x.get("match_score", 0), x.get("expCat") == "Strong"), reverse=True)

        # Compute stats for this user
        unique_companies = len(set(x.get("company") for x in user_matched_jobs if x.get("company")))
        india_roles = sum(1 for x in user_matched_jobs if x.get("country") == "India")
        intl_roles = sum(1 for x in user_matched_jobs if x.get("country") in ["UK", "Australia"] or (x.get("country") != "India" and x.get("country")))
        visa_roles = sum(1 for x in user_matched_jobs if "confirmed" in str(x.get("visaCat", "")).lower() or "plausible" in str(x.get("visaCat", "")).lower())

        user_stats = {
            "total": len(user_matched_jobs),
            "applied": 0,
            "india": india_roles,
            "intl": intl_roles,
            "visa": visa_roles,
            "companies": unique_companies
        }

        user["stats"] = user_stats
        user["jobs"] = user_matched_jobs
        users_dict[uid] = user
        print(f"[refine] User '{uid}': {len(user_matched_jobs)} matched roles, {unique_companies} target companies.")

    active_user_keys = list(users_dict.keys())
    default_user = "chandan" if "chandan" in users_dict else active_user_keys[0]

    refined_output = {
        "generated_at": now_ist,
        "default_user": default_user,
        "active_users": active_user_keys,
        "total_scraped_jobs": len(raw_jobs),
        "users": users_dict
    }

    # Save to data/refined_jobs.json
    with open(REFINED_PATH, "w", encoding="utf-8") as f:
        json.dump(refined_output, f, indent=2, ensure_ascii=False)
    print(f"[refine] Saved refined jobs to {REFINED_PATH}")

    # Also save to data/jobs.json
    with open(JOBS_PATH, "w", encoding="utf-8") as f:
        json.dump(refined_output, f, indent=2, ensure_ascii=False)
    print(f"[refine] Synced to {JOBS_PATH}")

    return refined_output


if __name__ == "__main__":
    refine_jobs()

