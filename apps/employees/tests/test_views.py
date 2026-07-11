from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class IndexViewTestCase(APITestCase):
    def test_get_index_page(self):
        """トップページ (IndexView) が 200 OK を返すことを確認"""
        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
