import re

KEYWORDS = [
        "artist",
        "work",
        "title",
        ]

LANGUAGE_MATCHER = re.compile(r'\b(' + r'|'.join(KEYWORDS) + r'):(?:"(.+?)"|(.+?)(?:$|\s(?=(?:' + r'|'.join(KEYWORDS) + r'):)))', re.I)

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
            }

    while True:
        split = LANGUAGE_MATCHER.split(query, maxsplit=1)
        if len(split) == 1:
            if query:
                result['remaining'].append(query)
            break

        remaining = split[0].strip()
        target = split[1].strip() + "s"
        value_exact = (split[2] or '').strip()
        value = (split[3] or '').strip()

        if remaining:
            result['remaining'].append(remaining)

        if value and not value_exact:
            result.get(target).append(value)
        elif value_exact and not value:
            result.get(target + "_exact").append(value_exact)
        else:
            raise ValueError("Inconsistency")

        query = split[4].strip()

    return result
