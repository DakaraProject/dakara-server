from django.core.urlresolvers import reverse
from rest_framework import status

from .base_test import BaseAPITestCase


class WorkListViewAPIViewTestCase(BaseAPITestCase):
    url = reverse('library-work-list')

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create test data
        self.create_library_test_data()

    def test_get_work_list(self):
        """Test to verify work list with no query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get works list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

        # works are sorted by name
        self.check_work_json(response.data['results'][0], self.work1)
        self.check_work_json(response.data['results'][1], self.work2)
        self.check_work_json(response.data['results'][2], self.work3)

        # Check song count
        self.assertEqual(response.data['results'][0]['song_count'], 1)
        self.assertEqual(response.data['results'][1]['song_count'], 0)
        self.assertEqual(response.data['results'][2]['song_count'], 0)

    def test_get_work_list_forbidden(self):
        """Test to verify unauthenticated user can't get work list
        """
        # Attempt to get works list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_work_list_type_filter(self):
        """Test to verify work list with work type filter
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get works list for type wt1
        # should return only work1 and work2
        response = self.client.get(self.url, {'type': 'wt1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

        # works are sorted by name
        self.check_work_json(response.data['results'][0], self.work1)
        self.check_work_json(response.data['results'][1], self.work2)

        # Get works list for type wt2
        # should return only work3
        response = self.client.get(self.url, {'type': 'wt2'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)

        # works are sorted by name
        self.check_work_json(response.data['results'][0], self.work3)

    def test_get_work_list_with_query(self):
        """Test to verify work list with query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get works list with query = "ork1"
        # Should only return work1
        self.work_query_test("ork1", [self.work1])

        # Get works list with query = "tist1"
        # Should not return any work
        self.work_query_test("tist1", [])

    def test_get_work_list_with_query_alternative_title(self):
        """Test to verify work list with query alternative title
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get works list with query = "ltTitle1"
        # Shoud only return work1
        self.work_query_test("ltTitle1", [self.work1])

    def test_get_work_list_with_query_empty(self):
        """Test to verify work list with empty query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get works list with query = ""
        # Should return all works
        self.work_query_test("", [self.work1, self.work2, self.work3])

    def test_get_work_list_with_query_no_keywords(self):
        """Test to verify work query do not parse keywords
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get works list with query = "title:work1"
        # Should not return anything since it searched for the whole string
        self.work_query_test("title:work1", [], ['title:work1'])

    def test_get_works_list_with_query__multi_words(self):
        """Test query parse with multi words remaining
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get works list with escaped space query
        # Should not return anything but check query
        self.work_query_test(
            r"word words\ words\ words remain", [], [
                'word', 'words words words', 'remain'])

        # Get works list with quoted query
        # Should not return anything but check query
        self.work_query_test(
            """ word"words words words" remain""", [], [
                'word', 'words words words', 'remain'])

    def work_query_test(self, query, expected_works, remaining=None):
        """Method to test a work request with a given query and worktype

        Returned work should be the same as expected_works,
        in the same order.
        """
        # TODO This only works when there is only one page of works
        response = self.client.get(self.url, {'query': query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], len(expected_works))
        results = response.data['results']
        self.assertEqual(len(results), len(expected_works))
        for work, expected_work in zip(results, expected_works):
            self.assertEqual(work['id'], expected_work.id)

        if remaining is not None:
            self.assertEqual(response.data['query']['remaining'], remaining)
