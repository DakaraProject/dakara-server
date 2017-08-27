import re
from library.models import WorkType

KEYWORDS = [
        "artist",
        "work",
        "title",
        ]

class QueryLanguageParser:
    """
    Parser for search query mini language
    used to search song
    """

    def __init__(self):
        self.keywords_work_type = [work_type.query_name
                for work_type in WorkType.objects.all()]

        self.keywords = KEYWORDS
        self.keywords.extend(self.keywords_work_type)
        self.language_matcher = re.compile(r"""
            \b(?P<keyword>{keywords_regex}) #keyword
            :
            \s?
            (?:
                ""(?P<exact>.+?)""          #exact value between double double quote
                |
                "(?P<contains>.+?)"         #contains value between double quote
                |
                (?P<contains2>(?:\\\s|\S)+) #contains with no quotes
            )
            """.format(keywords_regex=r'|'.join(self.keywords)),
            re.I | re.X
        )

    def split_remaining(self, string):
        """ Split string by whitespace character not escaped with backslash
            and preserve double quoted strings
        """
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

    def parse(self, query):
        """ Function that parses query mini language
            Returns a dictionnary with the folowing entries:

            artist:
                contains: list of list of artists names to match partially.
                exact: list of list of artists names to match exactly.
            work:
                contains: list of works names to match partially
                exact: list of works names to match exactly
            title:
                contains: titles to match partially
                exact: titles to match exactly
            tag: list of tags to match in uppercase
            work_type: dict with queryname as key and
                a dict as value with contains and exact

            remaining: unparsed text
        """

        result = {
                "artist": {
                    "contains": [],
                    "exact": []
                    },
                "work": {
                    "contains": [],
                    "exact": []
                    },
                "title": {
                    "contains": [],
                    "exact": []
                    },
                "work_type": {},
                "remaining": [],
                "tag": [],
                }

        for match in self.language_matcher.finditer(query):

            group_index = match.groupdict()

            target = group_index['keyword'].strip().lower()
            value_exact = (group_index['exact'] or '').strip()
            value_contains = (group_index['contains'] or group_index['contains2'] or '').replace("\\", "").strip()


            if target in self.keywords_work_type:
                # create worktype if not exists
                if target not in result['work_type']:
                    result['work_type'][target] = {
                        "contains": [],
                        "exact": []
                        }

                result_target = result['work_type'][target]

            else:
                result_target = result[target]

            if value_contains and not value_exact:
                result_target['contains'].append(value_contains)

            elif value_exact and not value_contains:
                result_target['exact'].append(value_exact)

            else:
                raise ValueError("Inconsistency")

        remaining = self.language_matcher.sub("", query)

        result['remaining'] = self.split_remaining(remaining)

        # deal with tags
        for item in result["remaining"][:]:
            if item[0] == "#":
                result["remaining"].remove(item)
                item_clean = item[1:]
                if item_clean:
                    result["tag"].append(item_clean.upper())

        return result
