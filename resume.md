# Cameron Antoine Parker

Fayetteville, North Carolina  
Email: [parker_c_18@yahoo.com](mailto:parker_c_18@yahoo.com)  
Phone: 910-910-1057  
LinkedIn: [linkedin.com/in/cameronaparker](https://www.linkedin.com/in/cameronaparker/) *(LinkedIn may require sign-in to view profile)*  
GitHub: [github.com/forgisonajeep](https://github.com/forgisonajeep)  

---

## SUMMARY  
Entry-level DevOps Engineer transitioning from culinary and DFAC operations with a passion for automation, cloud technologies, and system reliability. Skilled in scripting, cloud fundamentals, and deploying infrastructure using modern DevOps tools. Currently building hands-on projects and pursuing AWS certifications to accelerate a career in cloud engineering. Strong communicator and self-learner with a desire to contribute to high-performing technical teams.  

---

## SKILLS  
**Languages:** Bash, PowerShell, Python (boto3 primarily)  
**DevOps & Cloud:** AWS (EC2, S3, IAM, Lambda, Terraform, CloudWatch), GitHub Actions, Docker (basic), AWS CLI, EventBridge  
**CI/CD & Automation:** GitHub Actions, Git, GitHub, CodePipeline (familiar), YAML  
**Monitoring & Logging:** AWS CloudWatch, EC2 Logs  

---

## PROJECTS  

**Prompt Deployment Pipeline | Amazon Bedrock + S3 + GitHub Actions**  
*Use Case:* Automate AI-powered content creation and publishing for static sites.  
- Created a GitHub-based CI/CD workflow to process prompt templates and config files  
- Built a Python script (`process_prompt.py`) that:  
  - Loads and renders prompt templates using variables from config files  
  - Sends structured prompts to Amazon Bedrock for content generation  
  - Saves outputs as `.html` or `.md` files and uploads to S3 for static website hosting  
- Used environment-specific prefixes (`beta/`, `prod/`) to separate test and live content  
- Managed workflow triggers using PRs and merges, with secrets securely handled in GitHub Actions  

**Multilingual Audio Pipeline | Amazon Transcribe + Translate + Polly + S3 + GitHub Actions**  
*Use Case:* Automate voice-to-voice translation for `.mp3` content.  
- Developed a Python script (`process_audio.py`) to:  
  - Upload input `.mp3` files to S3  
  - Transcribe English audio using Amazon Transcribe  
  - Translate text into other languages with Amazon Translate  
  - Generate multilingual speech using Amazon Polly  
  - Save outputs to structured S3 paths for `transcripts/`, `translations/`, and `audio_outputs/`  
- Automated processing via GitHub Actions workflows for both PR (beta) and main (prod) branches  
- Used GitHub Secrets to securely manage AWS credentials and environment variables  

**Two-Tier Web Architecture on AWS | EC2 + RDS + VPC**  
*Use Case:* Deploy a secure and scalable content management website.  
- Launched a custom VPC with public and private subnets, configured routing tables and Internet Gateway  
- Deployed CMS on an Ubuntu EC2 instance (web tier), with MySQL database hosted on Amazon RDS (database tier)  
- Hardened networking using security groups and subnet isolation (EC2 in public, RDS in private)  
- Verified application connectivity and documented the benefits of two-tier architecture  

**EC2 Shutdown Automation | AWS Lambda + GitHub Actions + CloudFormation**  
*Use Case:* Reduce unnecessary EC2 runtime costs for non-production environments.  
- Built a Python Lambda function using boto3 to identify and stop EC2 instances based on state and tags  
- Scheduled shutdowns via Amazon EventBridge  
- Created an S3-hosted deployment package and used CloudFormation templates to deploy the Lambda with IAM roles  
- Automated deployment using separate GitHub Actions workflows for beta and prod environments  
- Managed environment-specific parameters and AWS credentials using GitHub Secrets  

---

## EXPERIENCE  

**Sous Chef / DFAC Operations Coordinator**  
*KBR – Al Asad Air Base, Iraq | June 2016 – December 2020*  
- Supported dining facility operations and logistics across secure base zones, coordinating food-service and supply data using digital inventory and reporting systems.  
- Assisted with system access requests, workstation troubleshooting, and internal data tracking for DFAC performance and metrics.  
- Collaborated with IT and logistics teams to improve efficiency through spreadsheet automation, barcode tracking, and process documentation.  
- Conducted daily inspections and maintained compliance logs for mission-critical equipment and material handling.  

---

## EDUCATION  

**High School Diploma**  
Seventy-First High School, Fayetteville, NC — 2007  

---

## CERTIFICATIONS  
- CompTIA Security+ (CE) — Completed (status: OK in CompTIA portal)  
- CompTIA Server+ — Completed (status: OK in CompTIA portal)
- AWS Certified Cloud Practitioner – In Progress  
- AWS Certified Developer – Associate – In Progress  
- Certified AI Practitioner  – In Progress  
- HashiCorp Certified: Terraform Associate – In Progress  
 
- Test AI deployment 🚀
