import os
import logging
import pickle
from dotenv import load_dotenv, find_dotenv
import fnf
from fnf.data.query_mag_composite import build_composite_expr, query_mag_api

logging.basicConfig(level=logging.INFO)
load_dotenv(find_dotenv())

key = os.getenv("mag_key")
metadata = fnf.config["data"]["mag"]["metadata"]
fos = fnf.config["data"]["mag"]["fos"]
entity_name = fnf.config["data"]["mag"]["entity_name"]
year = fnf.config["data"]["mag"]["year"]
offset = fnf.config["data"]["mag"]["offset"]
query_count = fnf.config["data"]["mag"]["query_count"]
store_path = fnf.config["data"]["mag"]["store_path"]

expression = build_composite_expr(fos, entity_name, year)
logging.info(f"{expression}")

has_content = True
i = 1

while has_content:
    logging.info(f"Query {i} - Offset {offset}...")

    data = query_mag_api(
        expression, metadata, key, query_count=query_count, offset=offset
    )
    results = [ents for ents in data["entities"]]

    with open("_".join([store_path, f"{i}.pickle"]), "wb") as h:
        pickle.dump(results, h)
    logging.info(f"Number of stored results from query {i}: {len(results)}")

    i += 1
    offset += query_count

    if len(results) == 0:
        has_content = False
