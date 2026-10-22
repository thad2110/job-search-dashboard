# User Profiles Directory

This directory contains text files for candidate profiles. Each `.txt` file represents a user whose skills and preferences determine which jobs from the scraped pool are matched and displayed on the dashboard.

## File Format

Create a new file named `<username>.txt` (for example, `priya.txt` or `alex.txt`):

```txt
Name: Full Name
Email: candidate@example.com
Phone: +91 98765 43210
Role: Target Title (e.g. Senior Machine Learning Engineer)
Experience: 5+ Years
Target Locations: India, UK, Australia

Summary:
Short summary of candidate background and domain expertise.

Primary Skills:
- Recommendation Systems (RecSys)
- Search & Ranking
- Large Language Models (LLM)
- PyTorch
- Python

Exclusions:
- Intern, Junior, Director, Principal
```

## How It Works

1. **Scraped Pool**: Raw jobs are stored in `data/scraped_jobs.json`.
2. **Refinement Pipeline**: Running `python scripts/refine_jobs.py` (or `python build_site.py`) reads every `.txt` file in `users/`.
3. **Skill Matching**: The refiner scores and categorizes jobs against each user's skills and generates `data/refined_jobs.json` and `data/jobs.json`.
4. **Interactive Dashboard**: The web dashboard reads the user list and jobs directly from the JSON. When a user switches candidates via the dropdown, the KPI stats, charts, and table immediately update.

