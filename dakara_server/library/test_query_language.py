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
        """
        Test to test complex query parse
        """
        res = self.parser.parse("""hey  artist: me work:you wt1:workName title: test\ Test remain stuff #tagg wt3:test artist:"my artist" work:""exact Work"" i   """)
        self.assertCountEqual(res['remaining'], ['remain', 'stuff', 'hey', 'i', 'wt3:test'])
        self.assertCountEqual(res['tag'], ['TAGG'])
        self.assertCountEqual(res['title']['contains'], ['test Test'])
        self.assertCountEqual(res['title']['exact'], [])
        self.assertCountEqual(res['artist']['contains'], ['me', 'my artist'])
        self.assertCountEqual(res['artist']['exact'], [])
        self.assertCountEqual(res['work']['contains'], ['you'])
        self.assertCountEqual(res['work']['exact'], ["exact Work"])
        self.assertCountEqual(res['work_type'].keys(), ['wt1'])
        self.assertCountEqual(res['work_type']['wt1']['contains'], ['workName'])
        self.assertCountEqual(res['work_type']['wt1']['exact'], [])

    def test_parse_contains_multi_words(self):
        """
        Test to test query parse with multi words criteria
        """
        res = self.parser.parse(r"title: words\ words\ words remain")
        self.assertCountEqual(res['remaining'], ['remain'])
        self.assertCountEqual(res['tag'], [])
        self.assertCountEqual(res['title']['contains'], ['words words words'])
        self.assertCountEqual(res['title']['exact'], [])
        self.assertCountEqual(res['artist']['contains'], [])
        self.assertCountEqual(res['artist']['exact'], [])
        self.assertCountEqual(res['work']['contains'], [])
        self.assertCountEqual(res['work']['exact'], [])
        self.assertCountEqual(res['work_type'].keys(), [])

        res = self.parser.parse("""title:"words words words" remain""")
        self.assertCountEqual(res['remaining'], ['remain'])
        self.assertCountEqual(res['tag'], [])
        self.assertCountEqual(res['title']['contains'], ['words words words'])
        self.assertCountEqual(res['title']['exact'], [])
        self.assertCountEqual(res['artist']['contains'], [])
        self.assertCountEqual(res['artist']['exact'], [])
        self.assertCountEqual(res['work']['contains'], [])
        self.assertCountEqual(res['work']['exact'], [])
        self.assertCountEqual(res['work_type'].keys(), [])
