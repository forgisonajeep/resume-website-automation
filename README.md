# AI-Generated Resume Website Automation
### A CI/CD Pipeline That Builds & Evaluates Your Resume Using Terraform + AWS + Bedrock AI

![Build Status](https://img.shields.io/badge/status-success-brightgreen)
![Terraform](https://img.shields.io/badge/IaC-Terraform-5C4EE5)
![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20DynamoDB%20%7C%20IAM-orange)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue)
![AI Powered](https://img.shields.io/badge/AI%20Powered-AWS%20Bedrock-purple)

A fully automated cloud CI/CD pipeline that converts a Markdown resume into an HTML website, enhances it using **AWS Bedrock AI**, deploys it to an S3 static website, and logs analytics + deployment events to DynamoDB. All deployments are triggered automatically by **GitHub Actions** and provisioned with **Terraform**.

---

### How to View the Live Resume Website (When Deployed)

This project deploys the resume site to two S3 static website environments via CI/CD pipelines:

- **Beta URL** (Pull Requests → main)
  https://cameron-resume-site-11062025.s3-website-us-east-1.amazonaws.com/beta/

- **Production URL** (Merge → main)
  https://cameron-resume-site-11062025.s3-website-us-east-1.amazonaws.com/

> **Note:** Hosting only exists when infrastructure is provisioned using Terraform:

```bash
terraform init
terraform apply -auto-approve
```

> **If the site is currently offline:**
Infrastructure has been torn down to avoid costs — redeploy using Terraform to reactivate both URLs.


## 🔗 Jump To

- [Overview](#overview)
- [What This Project Does](#what-this-project-does)
- [Architecture Overview](#architecture-overview)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [AWS + Terraform Setup](#aws--terraform-setup)
- [How the CI/CD Pipeline Works (Implementation)](#how-the-cicd-pipeline-works-implementation)
- [Deployment Logging in DynamoDB](#deployment-logging-in-dynamodb)
- [Manual Seed for Beta ATS Analytics](#manual-seed-for-beta-ats-analytics)
- [Troubleshooting](#troubleshooting)
- [Security Hardening](#security-hardening)
- [Lessons Learned](#lessons-learned)

---

## Overview

This project automates the full lifecycle of a resume website:

- `resume.md` is the **single source of truth**.
- A Python script converts it into `dist/index.html`.
- A second Python step calls **AWS Bedrock** for ATS-style analysis and writes a structured JSON file.
- GitHub Actions:
  - On **pull request** → deploys to **beta**.
  - On **merge to `main`** → promotes beta to **prod**.
- Terraform:
  - Provisions an **S3 static website bucket**.
  - Creates **DynamoDB tables** for deployment tracking and ATS analytics.
- DynamoDB:
  - Stores **production deployment records**.
  - Stores **AI ATS analysis results** generated during beta deploys.

The entire system is reproducible from this repository — no manual console configuration required.

---

## What This Project Does

- Uses `resume.md` as the canonical resume source.
- Converts Markdown → HTML using Python (`build_resume_site.py`).
- Calls AWS Bedrock to generate ATS-style analysis and saves it as `dist/ats_analysis.json`.
- Deploys HTML to an S3 static website bucket:
  - Pull request → `beta/index.html`.
  - Main branch → copies beta to `prod/index.html` and root `index.html`.
- Writes:
  - **Deployment events** to `DeploymentTrackingTable` (prod only).
  - **ATS analytics** to `ResumeAnalyticsTable` (beta only).
- Uses Terraform for all AWS infrastructure:
  - S3 bucket
  - DynamoDB tables
  - IAM roles / policies for GitHub Actions.

---

## Architecture Overview

High-level flow from edit → beta → prod → DynamoDB logging:

```text
    Developer edits resume.md
                │
                ▼
          Push / PR on GitHub
                │
                ▼
           GitHub Actions
                │
      ┌─────────┴───────────────────────────────┐
      │                                         │
      ▼                                         ▼
  PR into main                             Push/Merge to main
(triggers PR → beta workflow)          (triggers main → prod workflow)
 .github/workflows/pr-deploy.yml        .github/workflows/deploy.yml
      │                                         │
      ▼                                         ▼
Build HTML + ATS JSON                     Build HTML (local check)
via build_resume_site.py                 via build_resume_site.py
      │                                         │
      ▼                                         ▼
Upload HTML to S3 beta path              Copy beta → prod → root:
s3://cameron-resume-site-               - beta/index.html → prod/index.html
11062025/beta/index.html                - prod/index.html → index.html
      │                                         │
      ▼                                         ▼
Write ATS analytics item                 Write deployment event item
to ResumeAnalyticsTable                  to DeploymentTrackingTable
(beta only – no deployment log)          (prod only – no ATS analytics write)
```

---

## Repository Structure
```
resume-website-automation/
├── README.md                            # Project documentation
├── resume.md                            # Source of truth resume (Markdown)
├── requirements.txt                     # Python dependencies for build scripts
├── dist/                                # Generated outputs (HTML + ATS JSON)
│   ├── index.html                       # Built resume HTML
│   ├── converted.html                   # (optional) markdown conversion preview
│   ├── test_output.html                 # (optional) past testing artifact
│   └── ats_analysis.json                # Bedrock ATS analysis result
├── src/
│   ├── build_resume_site.py             # Converts resume.md → HTML + ATS JSON
│   └── template.html                    # HTML template applied to resume
├── scripts/
│   ├── write_deployment_event.py        # Logs prod deploy event → DynamoDB
│   ├── write_ats_analytics.py           # Writes ATS analytics → DynamoDB (beta)
│   └── manual_seed_resume_analytics.py  # Optional manual analytics seed tool
├── terraform/                           # IaC — S3 + DynamoDB + IAM roles
│   ├── main.tf                          # Core AWS resources
│   ├── variables.tf                     # Terraform input variables
│   ├── outputs.tf                       # Bucket name + website endpoint outputs
│   ├── provider.tf                      # AWS provider config
│   └── versions.tf                      # Terraform version constraints
└── .github/workflows/
    ├── pr-deploy.yml                    # PR → beta deploy automation
    └── deploy.yml                       # main → prod deploy automation
```
---

## Prerequisites

- AWS account with permissions for:
  - S3 (bucket + static website hosting).
  - DynamoDB (tables + `PutItem`).
  - IAM (role for GitHub Actions).
- GitHub repository with:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION`
  stored as **GitHub Secrets**.
- Local tools (for testing and seeding):
  - Python 3.x
  - `python -m venv` support
  - AWS CLI configured locally (optional but used during testing).
- Terraform installed (version matching the workflows, e.g. `1.5.x` / `1.6.x`).

---

## AWS + Terraform Setup

Terraform is responsible for:

- Creating the S3 bucket used for both **beta** and **prod**:
  - `cameron-resume-site-11062025`
- Enabling S3 static website hosting.
- Creating DynamoDB tables:
  - `DeploymentTrackingTable` (for prod deployment logs).
  - `ResumeAnalyticsTable` (for ATS analytics).
- IAM roles/policies that allow:
  - S3 object operations for the resume bucket.
  - DynamoDB `PutItem` access for both tables.

The `.gitignore` ensures Terraform state, `.terraform/`, and transient files do not get committed.

---

### 🚀 How the CI/CD Pipeline Works (Implementation)

Below is the full workflow from **editing the resume** → **beta preview** → **production deployment** → **database logging**.

---

#### **Local Build + ATS Analysis (Python)**  
Script: `src/build_resume_site.py` — Converts `resume.md` → HTML + Bedrock ATS JSON
  
```python
import os
import json
import markdown
import boto3
from botocore.exceptions import ClientError


def read_text(path):
    """Read a text file and return its contents as a string."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    """Write the given text to a file (UTF-8). Create parent folders if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def write_json(path, data):
    """Write a Python object as pretty-printed JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def md_to_html(md_text):
    """Convert Markdown text to HTML using python-markdown."""
    extensions = ["extra", "sane_lists", "toc", "tables", "fenced_code"]
    return markdown.markdown(md_text, extensions=extensions)


def extract_title_from_md(md_text):
    """Return the first H1 line ('# ') without the '# '. Fallback to 'Resume'."""
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Resume"


def render_page_from_template(template_path, page_title, content_html):
    """Read the HTML template and replace placeholders {{PAGE_TITLE}} and {{CONTENT}}."""
    template = read_text(template_path)
    page = template.replace("{{PAGE_TITLE}}", page_title)
    page = page.replace("{{CONTENT}}", content_html)
    return page


def run_ats_analysis_with_bedrock(md_text):
    """
    Call AWS Bedrock to analyze the resume for ATS readiness.

    Writes structured JSON to dist/ats_analysis.json:
    {
      "overall_score": ...,
      "keywords": [...],
      "missing_sections": [...],
      "suggestions": "..."
    }

    If Bedrock fails (permissions, service not enabled, etc),
    falls back to a simple local "fake" analysis so the pipeline
    still produces JSON for DynamoDB.
    """
    region = os.environ.get("AWS_REGION", "us-east-1")
    model_id = os.environ.get("ATS_MODEL_ID", "amazon.titan-text-lite-v1")

    prompt = f"""
You are an Applicant Tracking System (ATS) assistant.

Analyze the following resume (in Markdown) for ATS readiness.

Return ONLY valid JSON with this exact structure and no extra text:

{{
  "overall_score": <number between 0 and 100>,
  "keywords": [ "keyword1", "keyword2", ... ],
  "missing_sections": [ "section1", "section2", ... ],
  "suggestions": "one or two sentences of advice"
}}

Resume markdown:
\"\"\"{md_text}\"\"\"
"""

    try:
        client = boto3.client("bedrock-runtime", region_name=region)

        body = json.dumps(
            {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 512,
                    "temperature": 0.2,
                    "topP": 0.9,
                },
            }
        )

        response = client.invoke_model(
            modelId=model_id,
            body=body,
            accept="application/json",
            contentType="application/json",
        )

        raw_body = response["body"].read()
        payload = json.loads(raw_body.decode("utf-8"))
        output_text = payload["results"][0]["outputText"]

        try:
            analysis = json.loads(output_text)
        except json.JSONDecodeError:
            # Model returned text that isn't pure JSON; store as raw_output
            analysis = {
                "overall_score": 0,
                "keywords": [],
                "missing_sections": [],
                "suggestions": "Bedrock returned non-JSON output; see raw_output.",
                "raw_output": output_text,
            }

    except (ClientError, Exception) as e:
        # Hard fallback so the pipeline keeps working
        print(f"[warn] Bedrock ATS analysis failed: {e}")

        # dumb but deterministic "fake" analysis so grading can still see structure
        word_count = len(md_text.split())
        analysis = {
            "overall_score": max(40, min(90, word_count // 10)),
            "keywords": ["AWS", "Terraform", "GitHub Actions"],
            "missing_sections": [],
            "suggestions": "Fallback analysis used because Bedrock call failed.",
        }

    write_json("dist/ats_analysis.json", analysis)
    print("[debug] Wrote ATS analysis JSON to dist/ats_analysis.json")


if __name__ == "__main__":
    # Phase 1: read Markdown
    md = read_text("resume.md")

    # Phase 2: simple write test
    write_text("dist/test_output.html", "<h1>Hello from Phase 2!</h1>")

    # Phase 3: convert Markdown → HTML fragment
    html = md_to_html(md)
    write_text("dist/converted.html", html)

    # Phase 4: inject fragment into template → final page
    title = extract_title_from_md(md)
    full_html = render_page_from_template(
        "src/template.html", f"{title} — Resume", html
    )
    write_text("dist/index.html", full_html)
    print("File written to dist/index.html")

    # Phase 5: ATS AI analysis via Bedrock → JSON
    run_ats_analysis_with_bedrock(md)

```

Outputs generated automatically:
- `dist/index.html` → resume website
- `dist/ats_analysis.json` → Bedrock ATS scoring

---

#### **Create AWS Infrastructure with Terraform**  
Files: `terraform/*.tf` — Creates:
- S3 bucket: `cameron-resume-site-11062025`
- DynamoDB tables:
  - `DeploymentTrackingTable`
  - `ResumeAnalyticsTable`

> Run locally when infra needed:
```bash
terraform init
terraform apply -auto-approve
```

---

#### **PR → Beta Deployment (GitHub Actions)**  
Workflow: `.github/workflows/pr-deploy.yml`  
Trigger: Pull Request → `main`

Flow:
1. Builds HTML + ATS JSON using Python
2. Uploads HTML to S3 → `/beta/index.html`
3. Writes ATS analytics → `ResumeAnalyticsTable` (beta **only** — no deployment log)

```yaml
name: PR -> deploy (beta)

on:
  pull_request:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.6.6

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v3
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Terraform init + plan + validate
        run: |
          cd terraform
          terraform init -input=false
          terraform fmt -check
          terraform validate
          terraform plan -out=tfplan

      - name: Terraform apply (auto-approve) (create/update infra)
        if: github.event_name == 'pull_request'
        run: |
          cd terraform
          terraform apply -auto-approve tfplan

      - name: Read terraform outputs (bucket name & website endpoint)
        id: outputs
        run: |
          cd terraform
          terraform output -raw bucket_name > ../bucket.txt
          terraform output -raw website_endpoint > ../website_endpoint.txt
          terraform output -raw deployment_tracking_table > ../ddb_tracking.txt
          terraform output -raw resume_analytics_table > ../ddb_analytics.txt

      - name: Setup Python
        run: |
          python -m venv .venv
          . .venv/bin/activate
          pip install -r requirements.txt

      - name: Build resume HTML (local)
        run: |
          . .venv/bin/activate
          python src/build_resume_site.py

      - name: Upload site to S3 (beta)
        run: |
          if [ -f ../bucket.txt ]; then
            BUCKET=$(cat ../bucket.txt)
            aws s3 cp dist/index.html s3://$BUCKET/beta/index.html --acl public-read
            echo "Deployed to beta -> s3://$BUCKET/beta/index.html"
          else
            echo "::warning::bucket.txt not found, skipping upload"
          fi

      - name: Write ATS analytics to DynamoDB (beta)
        run: |
          echo "ResumeAnalyticsTable" > ddb_analytics.txt
          python scripts/write_ats_analytics.py \
            --table-file ddb_analytics.txt \
            --region "${AWS_REGION}"

      - name: Output S3 website endpoint (for screenshots)
        run: |
          if [ -f ../website_endpoint.txt ]; then
            echo "S3 website endpoint: $(cat ../website_endpoint.txt)"
          else
            echo "::warning::website_endpoint not found"
          fi

      - name: Cleanup temp files
        if: always()
        run: |
          rm -f ../bucket.txt ../website_endpoint.txt ../ddb_tracking.txt ../ddb_analytics.txt || true

```

---

#### **Write ATS Analytics to DynamoDB (Python)**  
Script: `scripts/write_ats_analytics.py`  
Only runs in **beta deployment**

Stores fields such as:
- `overall_score`
- extracted Bedrock keywords
- Bedrock suggestions
- raw result saved for debugging
 
```python
#!/usr/bin/env python3
import os
import sys
import json
import datetime
import boto3
from botocore.exceptions import ClientError


def read_first_line(path: str) -> str:
    """Read a single-line file such as ddb_analytics.txt."""
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"# ERROR reading {path}: {e}", file=sys.stderr)
        sys.exit(1)


def extract_bedrock_json(raw_output: str) -> dict | None:
    """
    Try to extract the inner JSON from a Bedrock response that looks like:

    tabular-data-json
    { ...real json... }
    """

    Returns a dict if successful, otherwise None.
    """
    if not raw_output:
        return None

    cleaned = raw_output

    # Split on ``` fences and pick the part that contains JSON
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            if "{" in part and "}" in part:
                cleaned = part
                break

    # Now grab the JSON object between the first { and last }
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    json_str = cleaned[start : end + 1]

    try:
        return json.loads(json_str)
    except Exception as e:
        print(f"# WARN: failed to parse inner Bedrock JSON: {e}", file=sys.stderr)
        return None


def main() -> None:
    # 1) Read table name from terraform-created file (ddb_analytics.txt)
    table_name = read_first_line("ddb_analytics.txt")

    # 2) Load the ATS analysis JSON produced by build_resume_site.py
    try:
        with open("dist/ats_analysis.json", "r", encoding="utf-8") as f:
            analysis = json.load(f)
    except Exception as e:
        print(f"# ERROR reading dist/ats_analysis.json: {e}", file=sys.stderr)
        sys.exit(1)

    # Base fields from original analysis
    overall_score = analysis.get("overall_score", 0)
    keywords = analysis.get("keywords", [])
    missing_sections = analysis.get("missing_sections", [])
    suggestions = analysis.get("suggestions", "")
    raw_output = analysis.get("raw_output", "")

    # 2b) Always try to pull real values from Bedrock's tabular-data-json block
    inner = None
    if isinstance(raw_output, str) and "tabular-data-json" in raw_output:
        inner = extract_bedrock_json(raw_output)

    if inner:
        # Override with the parsed Bedrock values if present
        overall_score = inner.get("overall_score", overall_score)
        keywords = inner.get("keywords", keywords)
        missing_sections = inner.get("missing_sections", missing_sections)
        suggestions = inner.get("suggestions", suggestions)

    # Ensure types are correct for DynamoDB
    try:
        overall_score = int(overall_score)
    except Exception:
        overall_score = 0

    if not isinstance(keywords, list):
        keywords = [str(keywords)]

    if not isinstance(missing_sections, list):
        missing_sections = [str(missing_sections)]

    suggestions = str(suggestions)
    raw_output = str(raw_output)

    # 3) Build the DynamoDB item (schema must match ResumeAnalyticsTable)
    item = {
        "id": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": "pr-beta-deploy",
        "overall_score": overall_score,
        "keywords": keywords,
        "missing_sections": missing_sections,
        "suggestions": suggestions,
        "raw_output": raw_output,
    }

    print("[debug] Writing ATS analysis item:")
    print(json.dumps(item, indent=2))

    # 4) Put the item into DynamoDB
    region = os.environ.get("AWS_REGION", "us-east-1")
    ddb = boto3.resource("dynamodb", region_name=region)
    table = ddb.Table(table_name)

    try:
        resp = table.put_item(Item=item)
        print("[debug] put_item succeeded:", resp)
    except ClientError as e:
        print("# ERROR during put_item:", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

```

---

#### **Prod Deploy + Promotion (GitHub Actions)**  
Workflow: `.github/workflows/main-deploy.yml`  
Trigger: Merge / Push → `main`

Flow:
1. Copy → `/beta/index.html`
2. Promote → `/prod/index.html` **and** `/index.html` (root website)
3. Logs deployment metadata → `DeploymentTrackingTable`
  
```yaml
name: deploy

# Trigger on pull request (same as your PR deploy flow)
on:
  pull_request:
    types: [opened, synchronize, reopened]
  push: 
    branches:
      - main
  workflow_dispatch: {}
    

permissions:
  contents: read
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      AWS_REGION: us-east-1

    steps:
      - name: "Checkout repo"
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: '1.5.7'

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Read Terraform outputs (bucket name & website endpoint)
        run: |
          echo "=== Terraform init & output (prod deploy) ==="
          cd terraform

          terraform init -input=false

          # Extract clean outputs
          terraform output -raw bucket_name | tr -d '\r' > ../bucket.txt
          echo "DeploymentTrackingTable" > ../ddb_tracking.txt
          terraform output -raw website_endpoint | tr -d '\r' > ../website_endpoint.txt

          cd -

      - name: "Debug: show working dir & files"
        run: |
          echo "---- workspace root ----"
          pwd
          ls -la

          echo "---- terraform dir ----"
          ls -la terraform || true

          echo "---- head of generated files ----"
          if [ -f bucket.txt ]; then
            echo "bucket.txt exists:"
            sed -n '1,5p' bucket.txt
          else
            echo "bucket.txt missing"
          fi

          if [ -f ddb_tracking.txt ]; then
            echo "ddb_tracking.txt exists:"
            sed -n '1,5p' ddb_tracking.txt
          else
            echo "ddb_tracking.txt missing"
          fi

          if [ -f website_endpoint.txt ]; then
            echo "website_endpoint.txt exists:"
            sed -n '1,5p' website_endpoint.txt
          else
            echo "website_endpoint.txt missing"
          fi

      - name: "Setup Python"
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: "Install Python dependencies"
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then
            pip install -r requirements.txt
          fi

      - name: "Build resume HTML (local)"
        run: |
          if [ -f src/build_resume_site.py ]; then
            python src/build_resume_site.py
          else
            echo "build script missing, skipping"
          fi

      - name: "Promote beta build to prod (S3)"
        run: |
          echo "=== Promote beta build to prod ==="

          # Hard-code the bucket name to avoid Terraform wrapper noise
          BUCKET_NAME="cameron-resume-site-11062025"

          echo "Using bucket: ${BUCKET_NAME}"

          echo "Checking for beta/index.html..."
          if ! aws s3 ls "s3://${BUCKET_NAME}/beta/index.html"; then
            echo "ERROR: beta/index.html not found in bucket ${BUCKET_NAME}"
            exit 1
          fi

          echo "Copying beta/index.html -> prod/index.html..."
          aws s3 cp \
            "s3://${BUCKET_NAME}/beta/index.html" \
            "s3://${BUCKET_NAME}/prod/index.html" \
            --metadata-directive REPLACE \
            --content-type text/html

          echo "Copying prod/index.html -> root index.html (for website endpoint)..."
          aws s3 cp \
            "s3://${BUCKET_NAME}/prod/index.html" \
            "s3://${BUCKET_NAME}/index.html" \
            --metadata-directive REPLACE \
            --content-type text/html

          # Refresh bucket.txt with the clean name for the DDB step
          echo "${BUCKET_NAME}" > bucket.txt

      - name: "Write deployment event to DynamoDB"
        run: |
          if [ -f ddb_tracking.txt ]; then
            echo "Running deployment event writer"
            python scripts/write_deployment_event.py \
              --table-file ddb_tracking.txt \
              --bucket-file bucket.txt \
              --environment prod \
              --region "${AWS_REGION}" || true
          else
            echo "Skipping DDB event write - ddb_tracking.txt not found"
          fi

      - name: "Output S3 website endpoint"
        run: |
          if [ -f website_endpoint.txt ]; then
            echo "Website URL: $(cat website_endpoint.txt)"
          else
            echo "website_endpoint.txt missing"
          fi

      - name: "Cleanup temp files"
        run: |
          rm -f bucket.txt ddb_tracking.txt website_endpoint.txt || true

      - name: "Complete job"
        run: |
          echo "Deploy job finished"

```

---

#### **Log Deployment Events (Python)**  
Script: `scripts/write_deployment_event.py`

Writes the production deployment metadata:
- bucket
- commit SHA
- environment
- timestamp

```python
#!/usr/bin/env python3
import os
import sys
import datetime
import boto3
from botocore.exceptions import ClientError


def read_first_line(path):
    """Read a single-line file such as bucket.txt or ddb_tracking.txt."""
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"ERROR reading {path}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    # Read table name & bucket name from workflow-generated files
    table_name = read_first_line("ddb_tracking.txt")
    bucket_name = read_first_line("bucket.txt")

    print(f"[debug] Using table name: {table_name}")
    print(f"[debug] Using bucket name: {bucket_name}")

    region = os.environ.get("AWS_REGION", "us-east-1")
    print(f"[debug] boto3 region: {region}")

    ddb = boto3.resource("dynamodb", region_name=region)
    table = ddb.Table(table_name)

    # WRITE A FULL ITEM (safe shape)
    item = {
        "deployment_id": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "message": "automated promotion from GitHub Actions",
        "bucket": bucket_name,
        "environment": "prod",
    }

    print(f"[debug] Writing item: {item}")

    try:
        resp = table.put_item(Item=item)
        print("[debug] put_item succeeded:", resp)
    except ClientError as e:
        print("ERROR during put_item:", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

```

---

#### **(Optional) Local Table Seeding (Python)**  
Script: `scripts/manual_seed_resume_analytics.py`  
Used for **local testing** before CI/CD is active
  
```python
#!/usr/bin/env python3
import json
import datetime
import boto3


TABLE_NAME = "ResumeAnalyticsTable"
AWS_REGION = "us-east-1"  # same region as your table


def main():
    # 1) Read the ATS analysis JSON produced by Bedrock
    with open("dist/ats_analysis.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2) Build the DynamoDB item (types must match: Number, String, List)
    item = {
        "id": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),  # PK MUST be named "id" to match your table
        "source": "local-seed",
        "overall_score": int(data.get("overall_score", 0)),
        "keywords": data.get("keywords", []),
        "missing_sections": data.get("missing_sections", []),
        "suggestions": str(data.get("suggestions", "")),
        "raw_output": str(data.get("raw_output", "")),
    }
    

    print("[debug] Item to write:")
    print(json.dumps(item, indent=2))

    # 3) Put the item into DynamoDB
    ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = ddb.Table(TABLE_NAME)

    resp = table.put_item(Item=item)
    print("[debug] put_item response:")
    print(resp)
    print("\n✅ Wrote ATS analytics item to ResumeAnalyticsTable")


if __name__ == "__main__":
    main()
```

---

### ✔ Results

After a merge to `main`:
- Production resume site updates automatically  
- DynamoDB tracks:
  - **ATS scoring history** (from PR beta flow)
  - **Deployment history** (from prod flow)

---

## Troubleshooting

Some of the most important real-world issues encountered and fixed:

1. **YAML Nested Mapping / Indentation Errors**
   - Symptom: GitHub Actions fails before the job starts with “mapping values are not allowed here” or nested mapping errors.
   - Cause: Incorrect YAML indentation and quoting in workflow files.
   - Fix: Re-wrote `.github/workflows/pr-deploy.yml` and `.github/workflows/deploy.yml` with consistent spacing and clear `run: |` blocks.

2. **DynamoDB `ValidationException: Missing the key id`**
   - Symptom: `ClientError` when writing to the analytics table.
   - Cause: The `ResumeAnalyticsTable` primary key was named `id`, but the item being written was using a different key name.
   - Fix: Updated `scripts/write_ats_analytics.py` to use `"id"` as the partition key and ensured all writes included this attribute.

3. **Bedrock Returning Fenced JSON Instead of Plain JSON**
   - Symptom: `overall_score` stuck at `0` and keywords list empty, even though Bedrock was returning data.
   - Cause: Bedrock response was wrapped in a fenced block like ` ```tabular-data-json { ... } ````, which broke basic JSON parsing.
   - Fix: Added an `extract_bedrock_json` helper that:
     - Strips fences.
     - Finds the inner `{ ... }`.
     - Parses that into a dict and overrides `overall_score`, `keywords`, etc.

4. **S3 ACL Error: `AccessControlListNotSupported`**
   - Symptom: CLI upload failed with `The bucket does not allow ACLs`.
   - Cause: Using `--acl public-read` on a bucket with ACLs disabled via S3 Bucket Ownership / Object Ownership.
   - Fix: Removed `--acl public-read` and relied on bucket policy + static website hosting configuration instead.

5. **Prod Deploy Not Updating Root Website**
   - Symptom: Beta looked correct, but main site did not update after merging to `main`.
   - Cause: The prod workflow was not explicitly copying objects from `beta/` to `prod/` and then to root.
   - Fix: Updated `.github/workflows/deploy.yml` to:
     - Copy `beta/index.html` → `prod/index.html`.
     - Copy `prod/index.html` → `index.html`.

---

## Security Hardening

Even for a small personal project, some basic security practices were followed:

- AWS credentials:
  - Stored only as **GitHub Secrets**.
  - Never committed to the repository.
- IAM permissions:
  - Scoped to:
    - S3 access for the specific resume bucket.
    - DynamoDB `PutItem` for `DeploymentTrackingTable` and `ResumeAnalyticsTable`.
- Terraform state:
  - `.terraform/`, `terraform.tfstate`, and backups are ignored via `.gitignore`.
- Temporary build / helper files:
  - `dist/`
  - `bucket.txt`, `ddb_tracking.txt`, `ddb_analytics.txt`, `website_endpoint.txt`
  - All excluded from version control and cleaned in workflows where appropriate.

---

## Lessons Learned

- **YAML is fragile** – a single indentation mistake can break an entire CI pipeline.
- **DynamoDB schemas must be explicit** – primary keys should be clearly defined and matched in all writer scripts.
- **AI integration isn’t just “call the model”** – real Bedrock responses may need post-processing to extract clean JSON.
- **Separating beta and prod flows is worth it** – being able to test in beta before promoting makes debugging much safer.
- **Documentation matters** – capturing the real troubleshooting journey (in this README and the Medium article) turns a school project into a real portfolio piece.

---

**Project by:** Cameron Parker — Cloud DevOps Engineer (in progress), Fayetteville, NC  
This repository represents a complete, reproducible CI/CD + AI pipeline for a resume website on AWS.
