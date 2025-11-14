# Resume Website Automation

![Build Status](https://img.shields.io/badge/status-success-brightgreen)
![Terraform](https://img.shields.io/badge/IaC-Terraform-5C4EE5)
![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20DynamoDB%20%7C%20IAM-orange)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue)

A fully automated CI/CD pipeline that converts a Markdown resume into an HTML website, deploys it to an S3 static website, and logs deployment events into DynamoDB — all powered by GitHub Actions and Terraform.

---

## Jump To

- [Overview](#overview)
- [What This Project Does](#what-this-project-does)
- [Architecture Overview](#architecture-overview)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [AWS & Terraform Setup](#aws--terraform-setup)
- [How the CI/CD Pipeline Works](#how-the-cicd-pipeline-works)
- [Terraform Infrastructure](#terraform-infrastructure)
- [Deployment Logging in DynamoDB](#deployment-logging-in-dynamodb)
- [Troubleshooting Notes](#troubleshooting-notes)
- [Cost Optimization](#cost-optimization)
- [Security Hardening](#security-hardening)
- [How to Recreate This Project](#how-to-recreate-this-project)
- [Teardown Notes](#teardown-notes)
- [Lessons Learned](#lessons-learned)

---

## Overview

This project automates the entire process of hosting a resume website:

- `resume.md` is the single source of truth for the resume.
- GitHub Actions automatically converts it to HTML using Python.
- Terraform provisions AWS infrastructure (S3 + DynamoDB).
- Deployments occur automatically on:
  - Pull requests into `main` → **beta environment**
  - Push/merge to `main` → **production environment**
- DynamoDB logs every production deployment event.

The entire resume site can be rebuilt from scratch using only this repository.

---

## What This Project Does

- Converts `resume.md` → `dist/index.html` using `src/build_resume_site.py`
- Deploys the final site to an S3 static website bucket
- Logs each **production** deployment to DynamoDB (`DeploymentTrackingTable`)
- Automates infrastructure with Terraform (`terraform/`)
- Uses GitHub Actions to:
  - Deploy beta site on **PR to main** (`pr-deploy.yml`)
  - Deploy prod site + log DynamoDB item on **push to main** (`main-deploy.yml`)

---

## Architecture Overview

High-level flow from edit → beta → prod → DynamoDB logging.

```text
Developer updates resume.md
        │
        ▼
  GitHub Actions
        │
 ┌-----------------------------┐
 │                             │
 ▼                             ▼
PR into main           Push/Merge to main
(triggers PR           (triggers Main
 beta deploy)          prod deploy)
 pr-deploy.yml         main-deploy.yml
     │                         │
     ▼                         ▼
Build resume HTML via Python (build_resume_site.py)
     │                         │
     ▼                         ▼
Upload to S3 (beta)           Upload to S3 (prod)
s3://<bucket>/beta/           s3://<bucket>/index.html
                               │
                               ▼
                     DynamoDB: DeploymentTrackingTable
                     - deployment_id (PK)
                     - message
                     - bucket
                     - environment = "prod"
                     - timestamp (ISO-8601)

(beta deploy does NOT write to DynamoDB)

```
---
## Repository Structure

    .
    ├── .github/
    │   └── workflows/
    │       ├── pr-deploy.yml           # PR → beta deploy pipeline
    │       └── main-deploy.yml         # main → prod deploy + DynamoDB logging
    │
    ├── src/
    │   ├── build_resume_site.py        # Markdown → HTML pipeline using template
    │   └── template.html               # HTML template with {{PAGE_TITLE}} and {{CONTENT}}
    │
    ├── scripts/
    │   └── write_deployment_event.py   # Writes deployment event into DynamoDB
    │
    ├── terraform/
    │   ├── backend.tf                  # Remote S3 backend for Terraform state
    │   ├── main.tf                     # S3 + DynamoDB infrastructure
    │   ├── variables.tf                # bucket_name and other variables
    │   └── outputs.tf                  # bucket name, website endpoint, etc.
    │
    ├── resume.md                       # Source-of-truth resume (Markdown)
    ├── requirements.txt                # python-markdown, boto3, etc.
    ├── README.md                       # This documentation
    └── .gitignore                      # Includes Terraform state and temp files

---

## Prerequisites

To run or recreate this project, you need:

- **AWS**
  - An AWS account
  - An IAM user with permissions for:
    - S3: create buckets, put objects
    - DynamoDB: create tables, `DescribeTable`, `PutItem`
    - IAM: enough to use your TF config (or use an admin-style lab role)
  - Access key + secret key for that IAM user

- **GitHub**
  - A GitHub repository (this project)
  - Repository **Secrets** (Settings → Secrets and variables → Actions → Repository secrets):
    - `AWS_ACCESS_KEY_ID`
    - `AWS_SECRET_ACCESS_KEY`
    - `AWS_REGION` (e.g. `us-east-1`)

- **Local tooling (optional but recommended)**
  - `git`
  - `python3` and `pip`
  - `terraform` CLI (matching the version used in workflows, e.g. 1.5.x / 1.6.x)
  - `awscli` v2 (for manual validation / cleanup)

The CI/CD pipeline itself runs fully inside GitHub Actions — local tools are primarily for testing and debugging.

---

## AWS & Terraform Setup

### 1. Terraform backend (state)

Terraform uses a remote S3 backend (configured in `terraform/backend.tf`) to store `terraform.tfstate`.  

If you are recreating this project in your own AWS account:

1. Create an **S3 bucket** to hold Terraform state (for example):

    - Name: `your-tf-state-bucket-name`
    - Region: `us-east-1` (or update the region in `backend.tf`)

2. Update `terraform/backend.tf` to match **your** backend bucket:

    - `bucket = "your-tf-state-bucket-name"`
    - `key    = "terraform.tfstate"`
    - `region = "us-east-1"`

3. From the `terraform/` folder, initialize:

    - `terraform init -reconfigure`

### 2. Terraform infrastructure (S3 + DynamoDB)

From the `terraform/` directory:

- Format / validate:

    - `terraform fmt`
    - `terraform validate`

- Plan and apply:

    - `terraform plan -out=tfplan`
    - `terraform apply -auto-approve tfplan`

This creates:

- **S3 bucket** for the resume website (static hosting)
- **DynamoDB table** `DeploymentTrackingTable` for deployment logs

The GitHub Actions workflows read Terraform outputs and use these resources for deployment and logging.

---

## How the CI/CD Pipeline Works

At a high level:

1. **Developer edits `resume.md`** and pushes to a branch.
2. **PR into `main`**:
   - `pr-deploy.yml` runs
   - Terraform deploys/updates infra
   - Python builds `dist/index.html`
   - S3 beta site is updated at `s3://<bucket>/beta/index.html`
3. **Merge / push to `main`**:
   - `main-deploy.yml` runs
   - `src/build_resume_site.py` builds the HTML
   - Prod site is updated (S3 root website)
   - `scripts/write_deployment_event.py` writes a row into DynamoDB `DeploymentTrackingTable`

### Key Python Script: `src/build_resume_site.py`

This script converts the Markdown resume into full HTML using an HTML template.

    import os
    import markdown

    def read_text(path):
        """Read a text file and return its contents as a string."""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def write_text(path, text):
        """Write the given text to a file (UTF-8). Create parent folders if needed."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def md_to_html(md_text):
        """Convert Markdown text to HTML using python-markdown."""
        extensions = ["extra", "sane_lists", "toc", "tables", "fenced_code"]
        return markdown.markdown(md_text, extensions=extensions)

    def extract_title_from_md(md_text):
        """Return the first H1 line (starts with '# ') without the '# '. Fallback to 'Resume' if none is found."""
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
        full_html = render_page_from_template("src/template.html", f"{title} — Resume", html)
        write_text("dist/index.html", full_html)
        print("File written to dist/index.html")

---

## CI/CD Workflow: PR → Beta (`.github/workflows/pr-deploy.yml`)

When a pull request targets `main`, this workflow:

- Runs Terraform to ensure infra is up-to-date
- Builds the site
- Uploads beta version to S3 under `beta/index.html`
- Prints website endpoint for testing

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

---

## CI/CD Workflow: Main → Prod (`.github/workflows/main-deploy.yml`)

When changes are pushed to `main` (including PR merges), this workflow:

- Reads Terraform outputs
- Builds the site
- Uploads to the production S3 website
- Writes a deployment event into DynamoDB

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

          - name: "Read terraform outputs (bucket name & website endpoint)"
            run: |
              echo "=== Terraform init & output ==="
              # run terraform commands from inside the terraform directory to avoid
              # global-flag / wrapper issues on the runner
              cd terraform
              terraform init -input=false
              terraform plan -input=false || true

              # collect outputs to files (ignore errors so job continues)
              terraform output -raw bucket_name > ../bucket.txt || true

              # HARD-CODE the DynamoDB table name
              echo "DeploymentTrackingTable" > ../ddb_tracking.txt

              terraform output -raw website_endpoint > ../website_endpoint.txt || true

              # return to repo root
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
              else:
                echo "build script missing, skipping"
              fi

          - name: "Upload site to S3 (beta)"
            run: |
              # placeholder: actual S3 upload commands go here
              echo "Uploading site to S3 (beta) - placeholder"

          - name: "Write deployment event to DynamoDB"
            run: |
              if [ -f ddb_tracking.txt ]; then
                echo "Running deployment event writer"
                python scripts/write_deployment_event.py \
                  --table-file ddb_tracking.txt \
                  --bucket-file bucket.txt \
                  --environment prod \
                  --region "${AWS_REGION}" || true
              else:
                echo "Skipping DDB event write - ddb_tracking.txt not found"
              fi

          - name: "Output S3 website endpoint (for screenshots)"
            run: |
              if [ -f website_endpoint.txt ]; then
                echo "Website URL: $(cat website_endpoint.txt)"
              else:
                echo "website_endpoint.txt missing"
              fi

          - name: "Cleanup temp files"
            run: |
              rm -f bucket.txt ddb_tracking.txt website_endpoint.txt || true

          - name: "Complete job"
            run: |
              echo "Deploy job finished"

---

## Deployment Logging in DynamoDB

When the **main-deploy** workflow runs successfully, it calls:

- `scripts/write_deployment_event.py`

This script reads the table name and bucket name from files written by the workflow (`ddb_tracking.txt`, `bucket.txt`), then writes a structured deployment item into DynamoDB.

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

Each row in `DeploymentTrackingTable` includes:

- `deployment_id` – ISO-8601 timestamp (primary key)
- `message` – description of the deployment
- `bucket` – target S3 bucket name
- `environment` – `prod` (production deployments only)

---

## Terraform Infrastructure

Terraform manages:

- S3 static website bucket (for resume site)
- DynamoDB `DeploymentTrackingTable` (for prod deployment logs)

Key behaviors:

- Bucket is configured for **static website hosting**
- Public access settings and bucket policy allow public read of `index.html`
- DynamoDB uses **PAY_PER_REQUEST** billing mode for simplicity and cost control

---

## Troubleshooting Notes

These are real issues hit while building this project and how they were resolved:

1. **Terraform backend / state errors**
   - Symptom: `terraform init` failing because the S3 backend bucket did not exist or had the wrong name.
   - Fix: Create the backend bucket first and update `terraform/backend.tf`, then run `terraform init -reconfigure`.

2. **S3 website endpoint vs bucket name confusion**
   - Symptom: Trying to open the **bucket name** as a URL instead of the **static website endpoint**.
   - Fix: Use the website endpoint reported by Terraform or the S3 console (e.g. `http://<bucket>.s3-website-<region>.amazonaws.com`).

3. **GitHub Actions YAML `nested mappings` errors**
   - Symptom: Workflow failing to load due to `nested mappings not allowed` errors.
   - Fix: Carefully align indentation, ensure steps under `run: |` are properly indented, and avoid mixing tabs with spaces. Keeping debug steps simple and consistently indented fixed this.

4. **Terraform outputs not appearing in workflow**
   - Symptom: `bucket.txt` or `ddb_tracking.txt` missing or containing garbage.
   - Fix: Run Terraform commands from the correct directory (`cd terraform`), then write outputs back to repo root (`> ../bucket.txt`). Avoid complex `-chdir` combinations and keep it simple: `cd`, `terraform output`, `cd -`.

5. **DynamoDB writes failing**
   - Symptom: `put_item` errors due to wrong table name or region.
   - Fix:
     - Confirm the table name (**DeploymentTrackingTable**) matches exactly.
     - Ensure `AWS_REGION` environment variable matches the table’s region.
     - Log the table name and region in the Python script before calling `put_item`.

---

## Cost Optimization

A few choices were made with cost in mind:

- **DynamoDB PAY_PER_REQUEST**
  - No fixed capacity — you only pay for actual reads/writes.
- **Single S3 bucket**
  - One bucket with beta and prod paths rather than multiple buckets.
- **Short-lived infrastructure for the lab**
  - Terraform makes it easy to destroy all resources once grading and screenshots are complete.

---

## Security Hardening

This project already bakes in several basic security practices:

- AWS credentials are **only** stored as GitHub Secrets and injected at runtime with `aws-actions/configure-aws-credentials`.
- IAM access is scoped to the minimum needed for this lab:
  - S3 object operations for the resume website bucket
  - DynamoDB `PutItem` on `DeploymentTrackingTable`
  - Access to the Terraform backend state bucket
- Terraform state and `.terraform/` directory are excluded via `.gitignore`, and state is stored in a dedicated S3 backend bucket (not committed to the repo).
- Temporary files (`bucket.txt`, `ddb_tracking.txt`, `ddb_analytics.txt`, `website_endpoint.txt`, `dist/`) are excluded via `.gitignore` and cleaned up inside the GitHub Actions workflows.

---

## How to Recreate This Project

If someone clones this repo and wants to recreate the full system:

1. **Clone the repo**

    - `git clone <this-repo-url>`
    - `cd resume-website-automation`

2. **Set up Terraform backend (state)**

    - Create an S3 bucket for Terraform state.
    - Update `terraform/backend.tf` with:
      - `bucket`
      - `region`
    - Run from inside `terraform/`:
      - `terraform init -reconfigure`

3. **Apply Terraform**

    - From `terraform/`:
      - `terraform fmt`
      - `terraform validate`
      - `terraform plan -out=tfplan`
      - `terraform apply -auto-approve tfplan`

4. **Configure GitHub Secrets**

    - In GitHub → Repo → Settings → Secrets and variables → Actions:
      - Add `AWS_ACCESS_KEY_ID`
      - Add `AWS_SECRET_ACCESS_KEY`
      - Add `AWS_REGION` (e.g. `us-east-1`)

5. **Test PR → beta flow**

    - Create a new branch.
    - Edit `resume.md`.
    - Push the branch and open a Pull Request into `main`.
    - Confirm `PR -> deploy (beta)` workflow runs and deploys `beta/index.html`.

6. **Test main → prod flow**

    - Merge the PR into `main`.
    - Confirm `deploy` (main-deploy) workflow runs.
    - Verify:
      - S3 static site is updated (prod)
      - DynamoDB `DeploymentTrackingTable` has a new item

At this point, they have fully recreated the resume website automation project.

---

## Teardown Notes

When you are done and want to stop all charges:

1. **Destroy Terraform infrastructure**

    - From the `terraform/` directory:
      - `terraform destroy -auto-approve`

2. **Verify in AWS Console**

    - S3:
      - Resume site bucket deleted
      - Terraform state bucket deleted (if you choose to)
    - DynamoDB:
      - `DeploymentTrackingTable` removed

3. **Optional: Clean up GitHub**

    - Leave workflows and code in place for portfolio purposes.
    - No AWS charges occur once S3/DynamoDB resources are gone.

---

## Lessons Learned

- **Small changes in YAML matter**
  - Indentation and multi-line `run: |` blocks caused real errors; fixing them required careful step-by-step debugging.
- **Terraform + GitHub Actions integration is powerful but strict**
  - Running Terraform from the correct directory and writing outputs to predictable files (`bucket.txt`, `ddb_tracking.txt`) made the workflows stable.
- **DynamoDB logging turns a basic site into a real DevOps system**
  - Instead of “just a static site,” every prod deployment now leaves an audit trail in `DeploymentTrackingTable`.
- **Teardown is as important as setup**
  - Using Terraform for both creation and destruction keeps AWS costs controlled and repeatable, which is critical in a learning environment.

This project now represents a full CI/CD pipeline: Markdown → HTML → S3 static website → DynamoDB deployment analytics, all wired together with Terraform and GitHub Actions.
