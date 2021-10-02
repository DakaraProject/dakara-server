from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from library.models import Work
from library.tests.base_test import LibraryAPITestCase

UserModel = get_user_model()


class WorkListViewTestCase(LibraryAPITestCase):
    url = reverse("library-work-list")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create a manager
        self.manager = self.create_user("ManagerUser", library_level=UserModel.MANAGER)

        # create test data
        self.create_test_data()

        # create urls
        self.url_work1 = reverse("library-work", kwargs={"pk": self.work1.id})

    def test_get_work_list(self):
        """Test to verify work list with no query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get works list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)

        # works are sorted by name
        self.check_work_json(response.data["results"][0], self.work1)
        self.check_work_json(response.data["results"][1], self.work2)
        self.check_work_json(response.data["results"][2], self.work3)

        # Check song count
        self.assertEqual(response.data["results"][0]["song_count"], 1)
        self.assertEqual(response.data["results"][1]["song_count"], 0)
        self.assertEqual(response.data["results"][2]["song_count"], 0)

    def test_get_work_list_forbidden(self):
        """Test to verify unauthenticated user can't get work list."""
        # Attempt to get works list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_work_list_type_filter(self):
        """Test to verify work list with work type filter."""
        # Login as simple user
        self.authenticate(self.user)

        # Get works list for type wt1
        # should return only work1 and work2
        response = self.client.get(self.url, {"type": "wt1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

        # works are sorted by name
        self.check_work_json(response.data["results"][0], self.work1)
        self.check_work_json(response.data["results"][1], self.work2)

        # Get works list for type wt2
        # should return only work3
        response = self.client.get(self.url, {"type": "wt2"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

        # works are sorted by name
        self.check_work_json(response.data["results"][0], self.work3)

    def test_get_work_list_with_query(self):
        """Test to verify work list with query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get works list with query = "ork1"
        # Should only return work1
        self.work_query_test("ork1", [self.work1])

        # Get works list with query = "tist1"
        # Should not return any work
        self.work_query_test("tist1", [])

    def test_get_work_list_with_query_alternative_title(self):
        """Test to verify work list with query alternative title."""
        # Login as simple user
        self.authenticate(self.user)

        # Get works list with query = "ltTitle1"
        # Should only return work1
        self.work_query_test("ltTitle1", [self.work1])

        # Get works list with query = "ltTitle2"
        # Should return work1 and work2
        self.work_query_test("ltTitle2", [self.work1, self.work2])

    def test_get_work_list_with_query_empty(self):
        """Test to verify work list with empty query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get works list with query = ""
        # Should return all works
        self.work_query_test("", [self.work1, self.work2, self.work3])

    def test_get_work_list_with_query_no_keywords(self):
        """Test to verify work query do not parse keywords."""
        # Login as simple user
        self.authenticate(self.user)

        # Get works list with query = "title:work1"
        # Should not return anything since it searched for the whole string
        self.work_query_test("title:work1", [], ["title:work1"])

    def test_get_works_list_with_query__multi_words(self):
        """Test query parse with multi words remaining."""
        # Login as simple user
        self.authenticate(self.user)

        # Get works list with escaped space query
        # Should not return anything but check query
        self.work_query_test(
            r"word words\ words\ words remain",
            [],
            ["word", "words words words", "remain"],
        )

        # Get works list with quoted query
        # Should not return anything but check query
        self.work_query_test(
            """ word"words words words" remain""",
            [],
            ["word", "words words words", "remain"],
        )

    def work_query_test(self, query, expected_works, remaining=None):
        """Method to test a work request with a given query and worktype.

        Returned work should be the same as expected_works,
        in the same order.
        """
        # TODO This only works when there is only one page of works
        response = self.client.get(self.url, {"query": query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], len(expected_works))
        results = response.data["results"]
        self.assertEqual(len(results), len(expected_works))
        for work, expected_work in zip(results, expected_works):
            self.assertEqual(work["id"], expected_work.id)

        if remaining is not None:
            self.assertEqual(response.data["query"]["remaining"], remaining)

    def test_post_work_simple(self):
        """Test to create a work without embedded data."""
        # pre-assert there are 3 works
        self.assertEqual(Work.objects.all().count(), 3)

        # authenticate as manager
        self.authenticate(self.manager)

        # create work
        response = self.client.post(
            self.url,
            {
                "title": "Girls und Panzer",
                "subtitle": "",
                "work_type": {"query_name": "anime"},
            },
        )
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert there are now 4 works
        self.assertEqual(Work.objects.all().count(), 4)

    def test_post_work_embedded(self):
        """Test to create a work with embedded data."""
        # pre-assert there are 3 works
        self.assertEqual(Work.objects.all().count(), 3)

        # authenticate as manager
        self.authenticate(self.manager)

        # create work
        response = self.client.post(
            self.url,
            {
                "title": "Girls und Panzer",
                "subtitle": "",
                "alternative_titles": [{"title": "Galupan"}, {"title": "Garupan"}],
                "work_type": {"query_name": "anime"},
            },
        )
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert there are now 4 works
        self.assertEqual(Work.objects.all().count(), 4)

    def test_put_work_simple(self):
        """Test to create a work without embedded data."""
        # pre-assert there are 3 works
        self.assertEqual(Work.objects.all().count(), 3)

        # authenticate as manager
        self.authenticate(self.manager)

        # create work
        response = self.client.put(
            self.url_work1,
            {
                "title": "Girls und Panzer",
                "subtitle": "",
                "work_type": {"query_name": "anime"},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert there are now 4 works
        self.assertEqual(Work.objects.all().count(), 3)

    def test_put_work_embedded(self):
        """Test to create a work with embedded data."""
        # pre-assert there are 3 works
        self.assertEqual(Work.objects.all().count(), 3)

        # authenticate as manager
        self.authenticate(self.manager)

        # create work
        response = self.client.put(
            self.url_work1,
            {
                "title": "Girls und Panzer",
                "subtitle": "",
                "alternative_titles": [{"title": "Galupan"}, {"title": "Garupan"}],
                "work_type": {"query_name": "anime"},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert there are now 4 works
        self.assertEqual(Work.objects.all().count(), 3)


class WorkPruneViewAPIViewTestCase(LibraryAPITestCase):
    url = reverse("library-work-prune")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser", library_level="m")

        # create test data
        self.create_test_data()

    def test_delete(self):
        """Test to prune works without songs."""
        # login as library manager
        self.authenticate(self.user)

        # check there are 3 works
        self.assertEqual(Work.objects.count(), 3)

        self.assertNotEqual(self.work1.song_set.count(), 0)

        # prune works
        response = self.client.delete(self.url)

        # check http status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check the response
        self.assertDictEqual(response.data, {"deleted_count": 2})

        # check there are only 1 work remaining
        self.assertEqual(Work.objects.count(), 1)

        # check artists with songs remains
        self.assertEqual(Work.objects.filter(pk=self.work2.pk).count(), 0)
        self.assertEqual(Work.objects.filter(pk=self.work3.pk).count(), 0)

    def test_delete_no_target(self):
        """Test to prune works when there are none to prune."""
        # login as library manager
        self.authenticate(self.user)

        # remove all works
        Work.objects.all().delete()

        # prune works
        response = self.client.delete(self.url)

        # check http status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check the response
        self.assertDictEqual(response.data, {"deleted_count": 0})
