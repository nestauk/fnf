import requests
from retrying import retry
import logging

ENDPOINT = "https://api.labs.cognitive.microsoft.com/academic/v1.0/evaluate"


# def build_composite_expr(query_values, entity_name, year):
#     """Builds a composite expression with ANDs in OR to be used as MAG query.

#     Args:
#         query_values (:obj:`list` of str): Phrases to query MAG with. 
#         entity_name (str): MAG attribute that will be used in query.
#         year (int): We collect data in the [year, now] timeframe.
#     Returns:
#         (str) MAG expression.
    
#     """
#     query_prefix_format = "expr=OR({})"
#     and_queries = [
#         "".join([f"And(Composite({entity_name}='{query_value}'), Y>={year})"])
#         for query_value in query_values
#     ]
#     return query_prefix_format.format(", ".join(and_queries))


def build_composite_expr(query_items, entity_name, year, max_length=16000):
    """Builds and yields a composite expression with ANDs in OR to be used 
    as MAG query from a list of items. Strings and integer items are formatted 
    quoted and unquoted respectively, as per the MAG query specification.
    The maximum accepted query length for the api appears to be around 16,000 characters.
    The same module (without the composite) is in the nesta repo. 

    Args:
        query_items (list): all items to be queried
        entity_name (str): the mag entity to be queried ie 'Ti' or 'Id'
        max_length (int): length of the expression which should not be exceeded. Yields
            occur at or below this expression length
        year (int): We collect data in the [year, now] timeframe.

    Returns:
        (str): expression in the format expr=OR(entity_name=item1, entity_name=item2...)

    """
    expr = []
    length = 0
    query_prefix_format = "expr=OR({})"
    for item in query_items:
        if type(item) == str:
            formatted_item = f"And(Composite({entity_name}='{item}'), Y>={year})"
        elif type(item) == int:
            formatted_item = f"And(Composite({entity_name}={item}), Y >={year})"
        length = sum(len(e) + 1 for e in expr) + len(formatted_item) + len(query_prefix_format)
        if length >= max_length:
            yield query_prefix_format.format(','.join(expr))
            expr.clear()
        expr.append(formatted_item)

    # pick up any remainder below max_length
    if len(expr) > 0:
        yield query_prefix_format.format(','.join(expr))

@retry(stop_max_attempt_number=1)
def query_mag_api(expr, fields, subscription_key, query_count=1000, offset=0):
    """Posts a query to the Microsoft Academic Graph Evaluate API.

    Args:
        expr (:obj:`str`): Expression as built by build_expr.
        fields: (:obj:`list` of `str`): Codes of fields to return, as per mag documentation.
        query_count: (:obj:`int`): Number of items to return.
        offset (:obj:`int`): Offset in the results if paging through them.

    Returns:
        (:obj:`dict`): JSON response from the api containing 'expr' (the original expression)
                and 'entities' (the results) keys.
                If there are no results 'entities' is an empty list.

    """
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    query = f"{expr}&count={query_count}&offset={offset}&model=latest&attributes={','.join(fields)}"

    r = requests.post(ENDPOINT, data=query.encode("utf-8"), headers=headers)
    r.raise_for_status()

    return r.json()
