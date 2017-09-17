from django.core.urlresolvers import reverse
from rest_framework import status
from .base_test import BaseAPITestCase

class WorkTypeListAPIViewTestCase(BaseAPITestCase):
    url = reverse('library-worktype-list')

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create test data
        self.create_library_test_data()

    def test_get_work_type_list(self):
        """
        Test to verify work type list
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get work type list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

        # Artists are sorted by name
        self.check_work_type_json(response.data['results'][0], self.wt1)
        self.check_work_type_json(response.data['results'][1], self.wt2)

    def test_get_work_type_list_forbidden(self):
        """
        Test to verify unauthenticated user can't get work type list 
        """
        # Attempt to get work type list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
