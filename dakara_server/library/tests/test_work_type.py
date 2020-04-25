from django.urls import reverse
from rest_framework import status

from internal.tests.base_test import UserModel
from library.tests.base_test import LibraryAPITestCase
from library.models import WorkType


class WorkTypeListViewAPIViewTestCase(LibraryAPITestCase):
    url = reverse("library-worktype-list")

    def setUp(self):
        # create a manager
        self.manager = self.create_user(
            "TestUserManager", library_level=UserModel.MANAGER
        )

        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create test data
        self.create_test_data()

    def test_get_work_type_list(self):
        """Test to verify work type list
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get work type list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

        # Artists are sorted by name
        self.check_work_type_json(response.data["results"][0], self.wt1)
        self.check_work_type_json(response.data["results"][1], self.wt2)

    def test_get_work_type_list_forbidden(self):
        """Test to verify unauthenticated user can't get work type list
        """
        # Attempt to get work type list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_work_type(self):
        """To to create a work type
        """
        # pre-assert there are 2 work types
        self.assertEqual(WorkType.objects.all().count(), 2)

        # authenticate as manager
        self.authenticate(self.manager)

        # create work type
        response = self.client.post(
            self.url, {"name": "wt3", "name_plural": "wt3s", "query_name": "wt3"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert there are now 3 work types
        self.assertEqual(WorkType.objects.all().count(), 3)


class WorkTypeViewAPIViewTestCase(LibraryAPITestCase):
    def setUp(self):
        # create a manager
        self.manager = self.create_user(
            "TestUserManager", library_level=UserModel.MANAGER
        )

        self.user = self.create_user("TestUser")

        # create test data
        self.create_test_data()

        # create urls
        self.url_wt1 = reverse("library-worktype", kwargs={"pk": self.wt1.id})

    def test_update_work_type_name(self):
        """Test manager can update work type name
        """
        # login as manager
        self.authenticate(self.manager)

        # pre-assert the work type has a given name
        self.assertEqual(self.wt1.name, "WorkType1")

        # alter the work type
        response = self.client.patch(self.url_wt1, {"name": "NewName"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the name changed
        self.assertEqual(WorkType.objects.get(id=self.wt1.id).name, "NewName")

    def test_update_work_type_name_user(self):
        """Test simple user cannot update work type name
        """
        # login as manager
        self.authenticate(self.user)

        # alter the work type
        response = self.client.patch(self.url_wt1, {"name": "NewName"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
