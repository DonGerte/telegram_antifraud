"""Utility for scheduled backups of PostgreSQL and Redis data.

Usage examples (cron/Windows Task Scheduler):

    python tools/backup.py --pg-dsn postgresql://user:pass@localhost/antifraud --redis-url redis://localhost:6379 --out /backups

It will create timestamped dumps and optionally upload to S3 if AWS creds are configured.
"""
import argparse
import datetime
import os
import subprocess
import sys

try:
    import redis
except ImportError:
    redis = None


def backup_postgres(dsn: str, out_dir: str):
    """Run pg_dump and store gzipped file."""
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = os.path.join(out_dir, f"pg_dump_{ts}.sql.gz")
    cmd = [
        "pg_dump",
        dsn,
        "-Fc",  # custom format (compressed)
        "-f",
        filename,
    ]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)
    print("Postgres backup saved to", filename)
    return filename


def backup_redis(url: str, out_dir: str):
    """Trigger Redis BGSAVE and copy dump.rdb to output dir."""
    if not redis:
        print("redis library not installed, skipping Redis backup")
        return None
    r = redis.from_url(url)
    print("Triggering Redis BGSAVE...")
    r.bgsave()
    # wait for completion
    while True:
        info = r.info()
        if info.get("rdb_bgsave_in_progress") == 0:
            break
    src = os.path.join(os.getcwd(), "dump.rdb")
    if not os.path.exists(src):
        print("warning: dump.rdb not found; ensure Redis configured to save to working dir")
        return None
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dest = os.path.join(out_dir, f"redis_dump_{ts}.rdb")
    print("Copying", src, "to", dest)
    with open(src, "rb") as fr, open(dest, "wb") as fw:
        fw.write(fr.read())
    return dest


def main():
    parser = argparse.ArgumentParser(description="Backup Postgres and Redis")
    parser.add_argument("--pg-dsn", help="Postgres DSN")
    parser.add_argument("--redis-url", help="Redis URL")
    parser.add_argument("--out", default=".", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    if args.pg_dsn:
        backup_postgres(args.pg_dsn, args.out)
    if args.redis_url:
        backup_redis(args.redis_url, args.out)


if __name__ == "__main__":
    main()
