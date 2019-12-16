import logging
import pickle
import glob
import os
import fnf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv, find_dotenv
from fnf.utils.utils import unique_dicts, unique_dicts_by_value, flatten_lists
from fnf.data.parse_mag_data import (
    parse_affiliations,
    parse_authors,
    parse_fos,
    parse_journal,
    parse_papers,
)
from fnf.data.mag_orm import (
    Paper,
    PaperAuthor,
    Journal,
    Author,
    Affiliation,
    AuthorAffiliation,
    FieldOfStudy,
    PaperFieldsOfStudy,
)

if __name__ == "__main__":

    load_dotenv(find_dotenv())

    external_data = fnf.config["data"]["external"]["path"]

    # Connect to postgresql
    engine = create_engine(os.getenv("postgresdb"))
    Session = sessionmaker(bind=engine)
    s = Session()

    data = []
    for filename in glob.iglob("".join([external_data, "*.pickle"])):
        # print(filename)
        with open(filename, "rb") as h:
            data.extend(pickle.load(h))
    # print(len(data))

    data = [d for d in unique_dicts_by_value(data, "Id")]
    logging.info(f"Number of unique  papers: {len(data)}")

    papers = [parse_papers(response) for response in data]
    # logging.info(f'Completed parsing papers: {len(papers)}')

    journals = [
        parse_journal(response, response["Id"])
        for response in data
        if "J" in response.keys()
    ]

    # Parse author information
    items = [parse_authors(response, response["Id"]) for response in data]
    authors = [
        d
        for d in unique_dicts_by_value(flatten_lists([item[0] for item in items]), "id")
    ]
    paper_with_authors = unique_dicts(flatten_lists([item[1] for item in items]))

    # Parse Fields of Study
    items = [
        parse_fos(response, response["Id"])
        for response in data
        if "F" in response.keys()
    ]
    paper_with_fos = unique_dicts(flatten_lists([item[0] for item in items]))
    fields_of_study = [
        d for d in unique_dicts(flatten_lists([item[1] for item in items]))
    ]

    # Parse affiliations
    items = [parse_affiliations(response) for response in data]
    affiliations = [d for d in unique_dicts(flatten_lists([item[0] for item in items]))]
    author_with_aff = [
        d for d in unique_dicts(flatten_lists([item[1] for item in items]))
    ]
    logging.info(f"Parsing completed!")

    # Insert dicts into postgresql
    s.bulk_insert_mappings(Paper, papers)
    s.bulk_insert_mappings(Journal, journals)
    s.bulk_insert_mappings(Author, authors)
    s.bulk_insert_mappings(PaperAuthor, paper_with_authors)
    s.bulk_insert_mappings(FieldOfStudy, fields_of_study)
    s.bulk_insert_mappings(PaperFieldsOfStudy, paper_with_fos)
    s.bulk_insert_mappings(Affiliation, affiliations)
    s.bulk_insert_mappings(AuthorAffiliation, author_with_aff)

    s.commit()
    logging.info("Committed to DB")
