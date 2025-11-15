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
