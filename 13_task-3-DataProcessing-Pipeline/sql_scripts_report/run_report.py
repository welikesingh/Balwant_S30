"""Run every SQL script in this folder against Supabase and build the report.

    ..\\venv\\Scripts\\python run_report.py            (from sql_scripts_report)
    venv\\Scripts\\python sql_scripts_report\\run_report.py   (from supabase_db_kit)

Reads DATABASE_URL from ../.env. Scripts run in file-name order (01..15).
Each "-- @result: <name>" block in a .sql file is one result set; it is saved as
output/<name>.csv and rendered into DATA_QUALITY_REPORT.md by report_builder.py.
All result sets are also saved together in output/results.json.
"""
import csv, datetime as dt, decimal, json, os, pathlib, re, sys, time

import psycopg
from dotenv import load_dotenv

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "output"
load_dotenv(HERE.parent / ".env")

MARK = re.compile(r"^-- @result:\s*(\w+)\s*$", re.M)


def split_script(text):
    """-> (setup_sql, [(name, sql), ...])"""
    parts = MARK.split(text)
    setup, named = parts[0], []
    for i in range(1, len(parts), 2):
        named.append((parts[i], parts[i + 1]))
    return setup, named


def has_sql(s):
    body = "\n".join(l for l in s.splitlines() if not l.strip().startswith("--"))
    return bool(body.strip().strip(";").strip())


def jsonable(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat()
    if isinstance(v, (dict, list)):
        return json.dumps(v)
    return v


def main():
    OUT.mkdir(exist_ok=True)
    results, timings = {}, []
    scripts = sorted(p for p in HERE.glob("[0-9][0-9]_*.sql") if not p.name.startswith("99"))
    with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=20, autocommit=True) as conn:
        conn.execute("SET statement_timeout = 0")
        for path in scripts:
            setup, named = split_script(path.read_text(encoding="utf-8"))
            t0 = time.time()
            if has_sql(setup):
                conn.execute(setup)
            for name, sql in named:
                cur = conn.execute(sql)
                cols = [d.name for d in cur.description]
                rows = [[jsonable(v) for v in r] for r in cur.fetchall()]
                results[name] = {"script": path.name, "columns": cols, "rows": rows}
                with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as fh:
                    w = csv.writer(fh); w.writerow(cols); w.writerows(rows)
            secs = round(time.time() - t0, 1)
            timings.append({"script": path.name, "seconds": secs})
            print(f"{path.name:40s} {secs:7.1f}s  {', '.join(n for n, _ in named)}", flush=True)

    meta = {"generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "timings": timings}
    (OUT / "results.json").write_text(json.dumps({"meta": meta, "results": results}, indent=1), encoding="utf-8")

    sys.path.insert(0, str(HERE))
    import report_builder
    report_builder.build(results, meta, HERE / "DATA_QUALITY_REPORT.md")
    print("report written:", HERE / "DATA_QUALITY_REPORT.md")


if __name__ == "__main__":
    main()
