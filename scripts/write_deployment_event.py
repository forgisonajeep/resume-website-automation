#!/usr/bin/env python3
"""
scripts/write_deployment_event.py

Usage (from repo root):
  python scripts/write_deployment_event.py --table-file ddb_tracking.txt --bucket-file bucket.txt --environment prod --region us-east-1
"""

import argparse
import boto3
import datetime
import json
import os
import sys
import traceback

def read_one_line(filename):
    try:
        with open(filename, "r") as f:
            # take last non-empty line
            lines = [ln.rstrip("\n\r") for ln in f if ln.strip() != ""]
            if not lines:
                return ""
            return lines[-1].strip()
    except Exception:
        return ""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table-file", required=True, help="File containing DynamoDB table name")
    parser.add_argument("--bucket-file", required=False, default="bucket.txt", help="File containing bucket name")
    parser.add_argument("--environment", required=False, default="prod", help="env label (prod/beta)")
    parser.add_argument("--region", required=False, default=None, help="AWS region (optional). If not set boto3 default will be used)")
    args = parser.parse_args()

    table_name = read_one_line(args.table_file)
    bucket_name = read_one_line(args.bucket_file) if args.bucket_file else ""
    env = args.environment

    if not table_name:
        print("ERROR: table name is empty; ensure the GitHub Action wrote the file.")
        sys.exit(1)

    print("boto3 default session region:", boto3.Session().region_name)
    if args.region:
        print("Using explicit region:", args.region)
        ddb = boto3.resource("dynamodb", region_name=args.region)
    else:
        ddb = boto3.resource("dynamodb")

    try:
        # Validate table visible
        try:
            client = boto3.client("dynamodb", region_name=(args.region or boto3.Session().region_name))
            names = client.list_tables().get("TableNames", [])
            print("DynamoDB tables visible to this session (sample):", names[:30])
        except Exception as e:
            print("Warning: could not list tables (may be a permissions issue):", e)

        table = ddb.Table(table_name)
        print("Using table object:", getattr(table, "table_name", table_name))

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        item = {
            "deployment_id": timestamp,
            "environment": env,
            "bucket": bucket_name,
            "message": "automated pipeline deployment",
            "metadata": {
                "written_by": "github-actions",
                "raw_timestamp": timestamp
            }
        }

        print("Attempting put_item with item keys:", list(item.keys()))
        resp = table.put_item(Item=item)
        print("\u2705 Successfully wrote item!")
        print(json.dumps(resp.get("ResponseMetadata", {}), indent=2))
        return 0

    except Exception as e:
        print("ERROR during put_item:", type(e).__name__, str(e))
        traceback.print_exc()
        # On ResourceNotFoundException it usually means table name mismatch or wrong region
        if hasattr(e, 'response') and 'Error' in getattr(e, 'response'):
            print("dynamodb error response:", e.response['Error'])
        return 2

if __name__ == "__main__":
    sys.exit(main())
