import re
from library.models import WorkType

KEYWORDS = [
        "artist",
        "work",
        "title",
        ]

KEYWORDS_WORK_TYPE = [work_type.query_name for work_type in WorkType.objects.all()]
if KEYWORDS_WORK_TYPE:
    KEYS_WORK_TYPE, KEYS_WORK_TYPE_EXACT = zip(*[(
        work_type_query_name + 's',
        work_type_query_name + 's_exact',
        ) for work_type_query_name in KEYWORDS_WORK_TYPE])
else:
    KEYS_WORK_TYPE = []
    KEYS_WORK_TYPE_EXACT = []

KEYWORDS.extend(KEYWORDS_WORK_TYPE)
LANGUAGE_MATCHER = re.compile(r'\b(' + r'|'.join(KEYWORDS) + r'):\s?(?:""(.+?)""|"(.+?)"|((?:\\\s|\S)+))', re.I)


def split_remaining(string):
    result = []
    current_expression = ""
    in_quotes = False
    previous_char = ""
    for char in string:
        if char == '"':
            if in_quotes:
                if current_expression:
                    result.append(current_expression)
                in_quotes = False 
                current_expression = ""
            else:
                current_expression = current_expression.strip()
                if current_expression:
                    result.append(current_expression)
                in_quotes = True
                current_expression = ""
        elif char == " " and not in_quotes and previous_char != "\\":
            current_expression = current_expression.strip()
            if current_expression:
                result.append(current_expression)
            current_expression = ""
        elif char != "\\":
            current_expression += char
        
        previous_char = char

    current_expression = current_expression.strip()
    if current_expression:
        result.append(current_expression)

    return result
            
def parse(query):
    """ Function that parses query mini language
        Returns a dictionnary with the folowing entries:

        artists: list of artists names to match partially
        artists_exact: list of artists names to match exactly
        works: list of works names to match partially
        works_exact: list of works names to match exactly
        titles: titles to match partially
        titles_exact: titles to match exactly
        remaining: unparsed text
    """

    result = {
            "artists": [],
            "artists_exact": [],
            "works": [],
            "works_exact": [],
            "titles": [],
            "titles_exact": [],
            "remaining": [],
            "tags": [],
            }
    # add current work types to the list
    for key_work_type, key_work_type_exact in zip(KEYS_WORK_TYPE, KEYS_WORK_TYPE_EXACT):
        result[key_work_type] = []
        result[key_work_type_exact] = []

    while True:
        split = LANGUAGE_MATCHER.split(query, maxsplit=1)
        if len(split) == 1:
            if query:
                result['remaining'].extend(split_remaining(query))
            break

        remaining = split[0].strip()
        target = split[1].strip() + "s"
        target = target.lower()
        value_exact = (split[2] or '').strip()
        value = (split[3] or split[4] or '').replace("\\", "").strip()

        if remaining:
            result['remaining'].extend(split_remaining(remaining))

        if value and not value_exact:
            result.get(target).append(value)
        elif value_exact and not value:
            result.get(target + "_exact").append(value_exact)
        else:
            raise ValueError("Inconsistency")

        query = split[5].strip()

    # deal with tags
    for item in result["remaining"][:]:
        if item[0] == "#":
            result["remaining"].remove(item)
            item_clean = item[1:]
            if item_clean:
                result["tags"].append(item_clean.upper())

    return result
