import os
import logging
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine
from sqlalchemy.sql import exists
from sqlalchemy.orm import sessionmaker
from fnf.data.mag_orm import Affiliation, AffiliationLocation
from fnf.data.geocode import place_by_id, place_by_name, parse_response

if __name__== '__main__':
    logging.basicConfig(level=logging.INFO)
    load_dotenv(find_dotenv())

    # config = fnf.config["data"][""]
    db_config = os.getenv("postgresdb")
    key = os.getenv("google_key")
    
    engine = create_engine(db_config)
    Session = sessionmaker(engine)
    s = Session()

    # Fetch affiliations that have not been geocoded yet.
    queries = s.query(Affiliation.id, Affiliation.affiliation).filter(
        ~exists().where(Affiliation.id == AffiliationLocation.affiliation_id)
    )
    logging.info(f"Number of queries: {queries.count()}")

    for id, name in queries:
        logging.info(name)
        try:
            r = place_by_name(name, key)
        except IndexError as e:
            logging.info(e)
            continue
        response = place_by_id(r, key)
        place_details = parse_response(response)
        place_details.update({"affiliation_id": id})
        s.add(AffiliationLocation(**place_details))
        s.commit()
