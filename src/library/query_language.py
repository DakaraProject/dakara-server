import re

from library.models import WorkType

KEYWORDS = ["artist", "work", "title"]


class QueryLanguageParser:
    """Parser for search query mini language used to search song."""

    def __init__(self):
        self.keywords_work_type = [
            work_type.query_name for work_type in WorkType.objects.all()
        ]

        self.keywords = KEYWORDS + self.keywords_work_type

        regex = r"""
        \b(?P<keyword>{keywords_regex}) # keyword
        :                               # separator
        \s?
        (?:
            ""(?P<exact>.+?)""          # exact value between double double
                                        # quote
            |
            "(?P<contains>.+?)"         # contains value between double
                                        # quote
            |
            (?P<contains2>(?:\\\s|\S)+) # contains with no quotes
        )
        """.format(
            keywords_regex=r"|".join(self.keywords)
        )

        self.language_matcher = re.compile(regex, re.I | re.X)

    @staticmethod
    def split_remaining(string):
        """Process the splitting of remaining parts of the query.

        Split string by whitespace character not escaped with backslash and
        preserve double quoted strings.

        Args:
            string (str): Words or expressions separated with spaces.

        Returns:
            list: List of splitted words or expressions.
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
        """Parse query mini language.

        Args:
            query (str): Words or commands of the query language separated
                with spaces.

        Returns:
            dict: Query terms arranged among the following keys:
                `artist`:
                    `contains`: List of list of artists names to match
                        partially.
                    `exact`: List of list of artists names to match exactly.
                `work`:
                    `contains`: List of works names to match partially.
                    `exact`: List of works names to match exactly.
                `title:
                    `contains`: Titles to match partially
                    `exact`: Titles to match exactly.
                `tag`: List of tags to match in uppercase.
                `work_type`: Dict with queryname as key and a dict as value
                    with the keys `contains` and `exact`.

                `remaining`: Unparsed text.
        """
        # create results structure
        # work_type will be filled only if necessary
        result = {
            "artist": {"contains": [], "exact": []},
            "work": {"contains": [], "exact": []},
            "title": {"contains": [], "exact": []},
            "work_type": {},
            "remaining": [],
            "tag": [],
        }

        for match in self.language_matcher.finditer(query):
            group_index = match.groupdict()

            # extract values
            target = group_index["keyword"].strip().lower()
            value_exact = (group_index["exact"] or "").strip()
            value_contains = (
                (group_index["contains"] or group_index["contains2"] or "")
                .replace("\\", "")
                .strip()
            )

            if target in self.keywords_work_type:
                # create worktype if not exists
                if target not in result["work_type"]:
                    result["work_type"][target] = {"contains": [], "exact": []}

                result_target = result["work_type"][target]

            else:
                result_target = result[target]

            if value_contains and not value_exact:
                result_target["contains"].append(value_contains)

            elif value_exact and not value_contains:
                result_target["exact"].append(value_exact)

            else:
                raise ValueError("Inconsistency")

        # deal with remaining
        remaining = self.language_matcher.sub("", query)
        result["remaining"] = self.split_remaining(remaining)

        # deal with tags
        for item in result["remaining"][:]:
            if item[0] == "#":
                result["remaining"].remove(item)
                item_clean = item[1:]
                if item_clean:
                    result["tag"].append(item_clean.upper())

        return result
