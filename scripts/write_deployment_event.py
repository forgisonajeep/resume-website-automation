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
