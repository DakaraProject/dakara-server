from django.test import TestCase

from .query_language import QueryLanguageParser
from .models import WorkType


class QueryLanguageParserTestCase(TestCase):
    def setUp(self):
        # Create work types
        self.wt1 = WorkType(name="WorkType1", query_name="wt1")
        self.wt1.save()
        self.wt2 = WorkType(name="WorkType2", query_name="wt2")
        self.wt2.save()

        # Create parser instance
        self.parser = QueryLanguageParser()

    def test_parse_multiple(self):
        """Test complex query parse
        """
        res = self.parser.parse(
            """hey  artist: me work:you wt1:workName title: test\ Test """
            """remain stuff #tagg wt3:test artist:"my artist" work:""exact """
            """Work"" i   """
        )
        self.assertCountEqual(
            res["remaining"], ["remain", "stuff", "hey", "i", "wt3:test"]
        )
        self.assertCountEqual(res["tag"], ["TAGG"])
        self.assertCountEqual(res["title"]["contains"], ["test Test"])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], ["me", "my artist"])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], ["you"])
        self.assertCountEqual(res["work"]["exact"], ["exact Work"])
        self.assertCountEqual(res["work_type"].keys(), ["wt1"])
        self.assertCountEqual(res["work_type"]["wt1"]["contains"], ["workName"])
        self.assertCountEqual(res["work_type"]["wt1"]["exact"], [])

    def test_parse_only_remaining(self):
        """Test simple query parse
        """
        res = self.parser.parse("This is just text with: nothing specific")
        self.assertCountEqual(
            res["remaining"],
            ["This", "is", "just", "text", "with:", "nothing", "specific"],
        )
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])

    def test_parse_tag(self):
        """Test tag query parse
        """
        res = self.parser.parse("#TG")
        self.assertCountEqual(res["remaining"], [])
        self.assertCountEqual(res["tag"], ["TG"])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])

    def test_parse_title(self):
        """Test title query parse
        """
        res = self.parser.parse("title:mytitle")
        self.assertCountEqual(res["remaining"], [])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], ["mytitle"])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])

    def test_parse_title_exact(self):
        """Test title exact query parse
        """
        res = self.parser.parse(""" title:""mytitle"" """)
        self.assertCountEqual(res["remaining"], [])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], ["mytitle"])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])

    def test_parse_artist(self):
        """Test artist query parse
        """
        res = self.parser.parse("artist:myartist")
        self.assertCountEqual(res["remaining"], [])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], ["myartist"])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])

    def test_parse_artist_exact(self):
        """Test artist exact query parse
        """
        res = self.parser.parse(""" artist:""myartist"" """)
        self.assertCountEqual(res["remaining"], [])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], ["myartist"])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])

    def test_parse_work(self):
        """Test work query parse
        """
        res = self.parser.parse("work:mywork")
        self.assertCountEqual(res["remaining"], [])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], ["mywork"])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])

    def test_parse_work_exact(self):
        """Test work exact query parse
        """
        res = self.parser.parse(""" work:""mywork"" """)
        self.assertCountEqual(res["remaining"], [])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], ["mywork"])
        self.assertCountEqual(res["work_type"].keys(), [])

    def test_parse_work_type(self):
        """Test work type query parse
        """
        res = self.parser.parse("wt2:mywork")
        self.assertCountEqual(res["remaining"], [])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), ["wt2"])
        self.assertCountEqual(res["work_type"]["wt2"]["contains"], ["mywork"])
        self.assertCountEqual(res["work_type"]["wt2"]["exact"], [])

    def test_parse_work_type_exact(self):
        """Test work type exact query parse
        """
        res = self.parser.parse(""" wt2:""mywork"" """)
        self.assertCountEqual(res["remaining"], [])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), ["wt2"])
        self.assertCountEqual(res["work_type"]["wt2"]["contains"], [])
        self.assertCountEqual(res["work_type"]["wt2"]["exact"], ["mywork"])

    def test_parse_contains_multi_words(self):
        """Test query parse with multi words criteria
        """
        res = self.parser.parse(r"title: words\ words\ words remain")
        self.assertCountEqual(res["remaining"], ["remain"])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], ["words words words"])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])

        res = self.parser.parse("""title:"words words words" remain""")
        self.assertCountEqual(res["remaining"], ["remain"])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], ["words words words"])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])

    def test_parse_remaining_multi_words(self):
        """Test query parse with multi words remaining
        """
        res = self.parser.parse(r"word words\ words\ words remain")
        self.assertCountEqual(res["remaining"], ["word", "words words words", "remain"])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])

        res = self.parser.parse(""" word"words words words" remain""")
        self.assertCountEqual(res["remaining"], ["word", "words words words", "remain"])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])

    def test_parse_old_worktype(self):
        """This test attempts to reproduce a bug where old work types were kept in
        memory
        """
        # Pre-assertion, keywords contains wt1 and wt2
        self.assertCountEqual(
            self.parser.keywords, ["artist", "work", "title", "wt1", "wt2"]
        )

        # Request with work type 2
        res = self.parser.parse("wt2:mywork")
        self.assertCountEqual(res["remaining"], [])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), ["wt2"])
        self.assertCountEqual(res["work_type"]["wt2"]["contains"], ["mywork"])
        self.assertCountEqual(res["work_type"]["wt2"]["exact"], [])

        # Now remove work type 2
        self.wt2.delete()

        # Create a new parser so that keywords are re-initialized with current
        # workTypes
        self.parser = QueryLanguageParser()

        # Check parser keywords, should not include wt2 anymore
        self.assertCountEqual(self.parser.keywords, ["artist", "work", "title", "wt1"])

        # Now the request with wt2 should not be parsed since wt2 is not a
        # keyword anymore
        res = self.parser.parse("wt2:mywork")
        self.assertCountEqual(res["remaining"], ["wt2:mywork"])
        self.assertCountEqual(res["tag"], [])
        self.assertCountEqual(res["title"]["contains"], [])
        self.assertCountEqual(res["title"]["exact"], [])
        self.assertCountEqual(res["artist"]["contains"], [])
        self.assertCountEqual(res["artist"]["exact"], [])
        self.assertCountEqual(res["work"]["contains"], [])
        self.assertCountEqual(res["work"]["exact"], [])
        self.assertCountEqual(res["work_type"].keys(), [])
