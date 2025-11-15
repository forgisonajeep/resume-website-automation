#!/usr/bin/env python3
import os
import sys
import json
import datetime
import boto3
from botocore.exceptions import ClientError


def read_first_line(path):
    """Read a single-line file such as ddb_analytics.txt."""
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"ERROR reading {path}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    # Table name from Terraform output file (already created in PR workflow)
    table_name = read_first_line("ddb_analytics.txt")

    # ATS JSON produced by build_resume_site.py
    try:
        with open("dist/ats_analysis.json", "r", encoding="utf-8") as f:
            analysis = json.load(f)
    except Exception as e:
        print(f"ERROR reading dist/ats_analysis.json: {e}", file=sys.stderr)
        sys.exit(1)

    region = os.environ.get("AWS_REGION", "us-east-1")
    ddb = boto3.resource("dynamodb", region_name=region)
    table = ddb.Table(table_name)

    item = {
        "analysis_id": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": "pr-beta-deploy",
        "commit_sha": os.environ.get("GITHUB_SHA", "local"),
        "analysis": analysis,
    }

    print(f"[debug] Writing ATS analysis item: {item}")

    try:
        resp = table.put_item(Item=item)
        print("[debug] put_item succeeded:", resp)
    except ClientError as e:
        print("ERROR during put_item:", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
