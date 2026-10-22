# 🎯 Machine Learning & Data Science Job Tracker Dashboard

An automated tracker and interactive web dashboard for senior Machine Learning, Applied Science, and Data Science roles across India, the UK, and Australia, featuring candidate skill-matching, multi-user filtering, and per-user application tracking.

## 🚀 Key Features

- **Multi-User Candidate Filtering**: Select candidates dynamically from the dashboard. Switching candidates immediately recalculates job stats, updates visual charts, and re-renders matching roles.
- **Skill-Based Job Categorization**: Categorizes jobs from a raw scraped pool into refined candidate-specific recommendations based on profile text files in `users/`.
- **Candidate Skill Matching Tags**: Displays matched skills, match scores, and personalized fit explanations on each role.
- **Interactive Dashboard (`index.html`)**: Filter by Candidate, Location, Company, Fit level, and Visa sponsorship status.
- **Direct Application Links & Referral Notes**: Direct links to official ATS requisitions (Greenhouse, Lever, Ashby, Workday, Microsoft Careers) and one-click personalized LinkedIn referral message generator.
- **Per-User Application Tracking**: Track `/applied` and `/skipped` status per candidate in `localStorage`, with export and Telegram sync options.
- **Zero-Dependency GitHub Pages Deployment**: Fully static and self-contained. Deployed automatically via GitHub Actions (`.github/workflows/deploy.yml`).

## 📁 Project Structure

```
job-search-dashboard/
├── .github/workflows/deploy.yml   # Auto-deploys to GitHub Pages
├── index.html                     # Live responsive multi-user dashboard
├── build_site.py                  # Builds refined jobs & generates index.html
├── users/                         # Candidate profiles directory
│   ├── chandan.txt                # Chandan Malla profile & skills
│   └── README.md                  # Guide on creating new candidate profiles
├── data/
│   ├── scraped_jobs.json          # Master pool of scraped jobs
│   ├── refined_jobs.json          # Categorized jobs per candidate + metadata
│   └── jobs.json                  # Synced dataset for dashboard and APIs
├── scripts/
│   ├── refine_jobs.py             # Skill matching & categorization engine
│   ├── sweep_crawler.py           # Alternating 3-hourly ATS scraper
│   ├── cron_runner.py             # Master cron orchestrator
│   └── bot_listener.py            # Telegram tracking bot listener
└── README.md
```

## 👤 Adding a New User / Candidate

To add a new candidate:

1. Create a text file in `users/` named `<username>.txt` (e.g. `users/priya.txt`):
   ```txt
   Name: Priya Sharma
   Email: priya@example.com
   Phone: +91 91234 56789
   Role: Senior NLP & GenAI Engineer
   Experience: 5+ Years
   Target Locations: India, UK

   Primary Skills:
   - Natural Language Processing (NLP)
   - Large Language Models (LLM) & Generative AI
   - Agentic Systems & Autonomous Agents
   - PyTorch & Python
   - RAG & Vector Search
   ```

2. Re-run the build generator:
   ```bash
   python build_site.py
   ```
   Or run the refiner standalone:
   ```bash
   python scripts/refine_jobs.py
   ```

3. Open `index.html` (or push to GitHub). The dashboard dropdown will automatically populate with the new candidate, calculate their specific stats, and show their matched jobs!

## 🌐 Deploy to GitHub Pages

1. Push this repository to GitHub:
   ```bash
   git add .
   git commit -m "Add multi-user filtering and skill-based job refinement"
   git push origin main
   ```
2. In your GitHub repository settings:
   - Navigate to **Settings** > **Pages**.
   - Under **Build and deployment** > **Source**, select **GitHub Actions**.
3. Your dashboard will be live at `https://<YOUR_USERNAME>.github.io/<YOUR_REPO>/`!
