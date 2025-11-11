#!/usr/bin/env python3
# scripts/write_deployment_event.py
import os
import sys
import datetime
import boto3
from botocore.exceptions import ClientError

# read table name produced by the workflow
def read_table_name(path="ddb_tracking.txt"):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"ERROR: cannot open {path}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    table_name = read_table_name()
    print("Using table_name from file:", repr(table_name))

    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
    print("boto3 default session region:", region)

    ddb = boto3.resource("dynamodb", region_name=region)
    table = ddb.Table(table_name)
    print("Using table object:", table.table_name)

    item = {
        # use timezone-aware UTC datetime ISO string
        "deployment_id": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "message": "automated promotion from GitHub Actions"
    }

    try:
        resp = table.put_item(Item=item)
        print("✅ Successfully wrote item!")
        print(resp)
    except ClientError as e:
        # show helpful error message for common problems
        code = e.response.get("Error", {}).get("Code", "")
        print("ERROR during put_item:", e, file=sys.stderr)
        if code == "ValidationException":
            print(" -> ValidationException: likely missing required key or wrong attribute name/type.", file=sys.stderr)
        if code == "ResourceNotFoundException":
            print(" -> ResourceNotFoundException: check table name and region.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
