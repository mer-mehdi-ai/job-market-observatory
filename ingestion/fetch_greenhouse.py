import time
import os
import json
from datetime import datetime, timezone
from pathlib import Path

import requests 

#-------------------------------------------------------------------

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"
SOURCE = "greenhouse"
CONFIG_PATH = "config/companies_test.txt"
DELAY_SECONDS = 0.5

#-------------------------------------------------------------------

def read_companies(path):
    with open(path, encoding="utf-8") as f :
        companies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    if not companies:
            raise ValueError("No companies found")
    return companies

                            #____________________________________________________________________#


def utc_now():
    return datetime.now(timezone.utc)

                            #____________________________________________________________________#


def build_path(company, date, timestamp):
    return (Path("data") / "raw" / "greenhouse" / f"dt={date}" / f"company={company}" / f"{timestamp}.json")

                            #____________________________________________________________________#


def ensure_folder(path):
    folder = os.path.dirname(path)
    if folder :
        os.makedirs(folder,exist_ok=True)


                            #____________________________________________________________________#

def save_json(data,path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

                            #____________________________________________________________________#


def fetch_jobs(company):
    url = f"{BASE_URL}/{company}/jobs"
    response = requests.get(url, params={"content":"true"}, timeout=30)
    response.raise_for_status()
    return response.json(), response.status_code

                            #____________________________________________________________________#

def wrap_payload(company,payload,status_code,fetched_at):
    return {
        "source": SOURCE,
        "company": company,
        "fetched_at": fetched_at,
        "status_code": status_code,
        "payload": payload
    }

#-------------------------------------------------------------------

def run(companies_path):

    companies = read_companies(companies_path)

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
    
            informations= wrap_payload(company,data,status,timestamp)
            save_json(informations, path)
            total_jobs += len(data["jobs"])
            succeeded.append(company)
        except Exception as e:
            print(f"{company} failed: {e}")
            failed.append(company)
        time.sleep(DELAY_SECONDS)
            
    if not succeeded :
        raise RuntimeError(f"All {len(failed)} companies failed : {failed}")
    print(f"Companies: {len(companies)} | Succeeded: {len(succeeded)} | Failed: {len(failed)} | Jobs: {total_jobs} ")

    """print(f"{len(succeeded)} companies succeeded: {succeeded}")
    print(f"{len(failed)} companies failed: {failed}")
    print(f"there is {total_jobs} jobs in total")"""

if __name__ == "__main__":

    run(CONFIG_PATH)
