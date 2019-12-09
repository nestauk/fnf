import requests
from retrying import retry

ENDPOINT = "https://api.labs.cognitive.microsoft.com/academic/v1.0/evaluate"

def build_composite_expr(query_values, entity_name, year):
  query_prefix_format = "expr=OR({})"
  and_queries = [''.join([f"And(Composite({entity_name}='{query_value}'), Y>={year})"]) for query_value in query_values]
  return query_prefix_format.format(", ".join(and_queries))

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
    query = f"{expr}&count={query_count}&offset={offset}&attributes={','.join(fields)}"

    r = requests.post(ENDPOINT, data=query.encode("utf-8"), headers=headers)
    r.raise_for_status()

    return r.json()
