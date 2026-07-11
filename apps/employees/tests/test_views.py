from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

class IndexViewTestCase(APITestCase):
    def test_get_index_page(self):
        """トップページ (IndexView) が 200 OK を返すことを確認"""
        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class SSEStreamViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.force_login(self.user)
        self.url = reverse('sse-stream')

    def test_sse_stream_header(self):
        """SSE ストリームエンドポイントが正しいヘッダーを返すことを確認"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        self.assertEqual(response['Cache-Control'], 'no-cache')
