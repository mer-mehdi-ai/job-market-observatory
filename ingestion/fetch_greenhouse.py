import requests 
from datetime import datetime, timezone, timedelta
import time
import os
import json
from pathlib import Path


def read_companies(path):
    with open(path, encoding="utf-8") as f :
        companies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    if not companies:
            raise ValueError("No companies found")
    return companies

#-------------------------------------------------------------------

def utc_now():
    return datetime.now(timezone.utc)

#-------------------------------------------------------------------

def fetch_jobs(company):
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    response = requests.get(url, params={"content":"true"}, timeout=30)
    response.raise_for_status()
    return response.json(), response.status_code

#-------------------------------------------------------------------

def build_path(company, date, timestamp):
    return (Path("data") / "raw" / "greenhouse" / f"dt={date}" / f"company={company}" / f"{timestamp}.json")
#-------------------------------------------------------------------

def ensure_folder(path):
    folder = os.path.dirname(path)
    if folder :
        os.makedirs(folder,exist_ok=True)

#-------------------------------------------------------------------

def save_json(data,path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

#-------------------------------------------------------------------
if __name__ == "__main__":

    companies = read_companies("config/companies.txt")

    now = utc_now()
    date = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")

    succeeded=[]
    failed=[]
    total_jobs = 0

    for company in companies:
        try:
            data, status = fetch_jobs(company)
            path = build_path(company, date, timestamp)
            ensure_folder(path)
 
            informations= {
                "source": "greenhouse",
                "company": company,
                "fetched_at": timestamp,
                "status_code": status,
                "payload": data
                }
            save_json(informations, path)
            total_jobs += len(data["jobs"])
            succeeded.append(company)
        except Exception as e:
            print(f"{company} failed: {e}")
            failed.append(company)
        time.sleep(0.5)
        
    if not succeeded :
        raise RuntimeError(f"All {len(failed)} companies failed : {failed}")

    print(f"{len(succeeded)} companies succeeded: {succeeded}")
    print(f"{len(failed)} companies failed: {failed}")
    print(f"there is {total_jobs} jobs in total")
