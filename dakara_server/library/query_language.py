import re


class QueryLanguageParser:
    """Parser for search query mini language.

    Args:
        keywords (list of str): List of keywords to use
        for parsing.
    """

    def __init__(self, keywords):
        self.keywords = keywords

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
            dict: Query terms parsed according to the
            provided keywords. Each item is a dict
            containing two lists:
                `contains`: List of partial matches.
                `exact`: List of exact matches.
            In addition, two extra items are present in
            the dict:
                `tag`: List of tags to match in uppercase.
                `remaining`: Unparsed text.
        """
        # create results structure
        # work_type will be filled only if necessary
        result = {kw: {"contains": [], "exact": []} for kw in self.keywords}
        result.update(
            {
                "remaining": [],
                "tag": [],
            }
        )

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

            if value_contains and not value_exact:
                result[target]["contains"].append(value_contains)

            elif value_exact and not value_contains:
                result[target]["exact"].append(value_exact)

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


def regroup(res, key, keys):
    """Regroup non empty keys in a specific key.

    Args:
        res (dict): Dictionary where to regroup keys.
        key (str): Key where to regroup `keys`.
        keys (list of str): Keys to regroup in `key`.
            Any key with no items in `exact` and
            `contains` will just be removed.
    """
    res_copy = res.copy()
    res_copy[key] = {}
    for k in keys:
        val = res_copy.pop(k)
        if len(val["exact"]) or len(val["contains"]):
            res_copy[key][k] = val

    return res_copy
