"""
Queries Microsoft Academic Knowledge API with author IDs and stores the responses locally.
The pickle file is a list of JSONs where every JSON object is the API response corresponding to a paper. Every 
pickle contains a maximum of 1,000 objects (that's the maximum number of papers we can retrieve from MAG with a
query).

Note that we collect only papers with a DOI.

Example API response:
{'logprob': -24.006,
 'prob': 3.75255e-11,
 'Id': 2904236373,
 'Ti': 'conspiracy ideation and fake science news',
 'Pt': '0',
 'Y': 2018,
 'D': '2018-01-18',
 'CC': 0,
 'RId': [2067319876, 2130121899],
 'PB': 'OSF',
 'BT': 'a',
 'AA': [{'DAuN': 'Asheley R. Landrum',
   'AuId': 2226866834,
   'AfId': None,
   'S': 1},
  {'DAuN': 'Alex Olshansky', 'AuId': 2883323127, 'AfId': None, 'S': 2}],
 'F': [{'DFN': 'Science communication',
   'FN': 'science communication',
   'FId': 472806},
  {'DFN': 'Public relations', 'FN': 'public relations', 'FId': 39549134},
  {'DFN': 'Public awareness of science',
   'FN': 'public awareness of science',
   'FId': 176049440},
  {'DFN': 'Political science', 'FN': 'political science', 'FId': 17744445},
  {'DFN': 'Misinformation', 'FN': 'misinformation', 'FId': 2776990098},
  {'DFN': 'Ideation', 'FN': 'ideation', 'FId': 170477896},
  {'DFN': 'Fake news', 'FN': 'fake news', 'FId': 2779756789}]}
"""
import os
import logging
import pickle
from dotenv import load_dotenv, find_dotenv
import fnf
from fnf.data.query_mag_composite import build_composite_expr, query_mag_api
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fnf.data.mag_orm import Author

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv(find_dotenv())

    config = fnf.config["data"]["mag"]
    # API params
    key = os.getenv("mag_key")
    metadata = config["metadata_short"]
    entity_name = config["entity_name"][1]
    year = config["year"]
    query_count = config["query_count"]
    # Path to external data with file prefix
    store_path = f'{fnf.project_dir}/{config["store_path"][1]}'

    # Fetch author IDs from DB
    db_config = os.getenv("postgresdb")
    engine = create_engine(db_config)
    Session = sessionmaker(engine)
    s = Session()
    authors = [id_[0] for id_ in s.query(Author.id)]

    # Build an expandable query for MAG API
    expressions = build_composite_expr(authors, entity_name, year)

    i = 1
    COLLECTED_DOIs = set()
    for num, expression in enumerate(expressions):
        has_content = True
        offset = 0
        # Request the API as long as we receive non-empty responses
        while has_content:

            data = query_mag_api(
                expression, metadata, key, query_count=query_count, offset=offset
            )
            results = [ents for ents in data["entities"] if 'DOI' in ents.keys()]
            COLLECTED_DOIs.update([result['DOI'] for result in results])

            with open("_".join([store_path, f"{i}.pickle"]), "wb") as h:
                pickle.dump(results, h)
            logging.info(f"expr {num} - query {i} - offset {offset}: {len(results)}")

            i += 1
            offset += query_count

            if len(results) < query_count:
                has_content = False
