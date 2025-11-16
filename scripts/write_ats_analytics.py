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

    ```tabular-data-json
    { ...real json... }
    ```

    Returns a dict if successful, otherwise None.
    """
    if not raw_output:
        return None

    # Strip code-fence markers if present
    cleaned = raw_output

    # Remove leading ```... lines
    if "```" in cleaned:
        parts = cleaned.split("```")
        # usually: ['', 'tabular-data-json\n{...}', '']
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
    # 1) Read table name from terraform-created file
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

    # 2b) If overall_score is 0 but Bedrock actually returned
    # a tabular-data-json block, try to pull the real numbers
    if overall_score == 0 and isinstance(raw_output, str) and "tabular-data-json" in raw_output:
        inner = extract_bedrock_json(raw_output)
        if inner:
            # Override with the parsed Bedrock values
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
