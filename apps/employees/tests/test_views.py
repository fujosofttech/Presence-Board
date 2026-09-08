from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from apps.employees.models import Department, Group, Employee

class IndexViewTestCase(APITestCase):
    def test_get_index_page(self):
        """トップページ (IndexView) が 200 OK を返すことを確認"""
        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AuthViewTestCase(APITestCase):
    def setUp(self):
        # 組織と社員データの作成
        self.department = Department.objects.create(name="開発部", display_order=1)
        self.group = Group.objects.create(department=self.department, name="第1グループ", display_order=1)
        
        self.username = "testuser"
        self.password = "testpass1234"
        self.email = "test@example.com"
        
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email=self.email
        )
        
        self.employee = Employee.objects.create(
            employee_no="E1001",
            name="テストユーザー",
            email=self.email,
            department=self.department,
            group=self.group
        )

    def test_get_auth_unauthenticated(self):
        """未ログイン時のGET /api/v1/auth/ の応答確認"""
        url = reverse('auth')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['authenticated'])

    def test_get_auth_authenticated(self):
        """ログイン時のGET /api/v1/auth/ の応答確認"""
        self.client.force_login(self.user)
        url = reverse('auth')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['authenticated'])
        self.assertEqual(response.data['user']['username'], self.username)
        self.assertEqual(response.data['employee']['employee_no'], "E1001")

    def test_post_auth_success(self):
        """ログイン成功時の確認"""
        url = reverse('auth')
        data = {
            "username": self.username,
            "password": self.password
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['authenticated'])
        self.assertEqual(response.data['user']['username'], self.username)

    def test_post_auth_with_employee_no(self):
        """社員番号によるログイン成功の確認"""
        url = reverse('auth')
        data = {
            "username": "E1001",
            "password": self.password
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['authenticated'])
        self.assertEqual(response.data['user']['username'], self.username)

    def test_post_auth_failed(self):
        """ログイン失敗時（誤ったパスワード）の確認"""
        url = reverse('auth')
        data = {
            "username": self.username,
            "password": "wrongpassword"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'], "E0001")

    def test_post_auth_missing_fields(self):
        """ログイン失敗時（フィールド不足）の確認"""
        url = reverse('auth')
        data = {
            "username": self.username
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], "E0001")

    def test_logout(self):
        """ログアウト処理の確認"""
        self.client.force_login(self.user)
        url = reverse('logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Logout successful")
        
        # ログアウトされたか確認
        auth_url = reverse('auth')
        response = self.client.get(auth_url)
        self.assertFalse(response.data['authenticated'])


class SetPasswordViewTestCase(APITestCase):
    def setUp(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        self.user = User.objects.create_user(
            username="newuser",
            email="newuser@example.com",
            password="initialpass123",
            is_active=False
        )
        self.token = default_token_generator.make_token(self.user)
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.url = reverse('set_password', kwargs={'uidb64': self.uidb64, 'token': self.token})

    def test_get_set_password_page_valid_token(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "パスワード設定")

    def test_get_set_password_page_invalid_token(self):
        invalid_url = reverse('set_password', kwargs={'uidb64': self.uidb64, 'token': 'invalid-token'})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "無効")

    def test_post_set_password_success(self):
        response = self.client.post(self.url, {
            'password': 'NewSecurePassword123!',
            'password_confirm': 'NewSecurePassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "設定完了")
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.check_password('NewSecurePassword123!'))

    def test_post_set_password_mismatch(self):
        response = self.client.post(self.url, {
            'password': 'NewSecurePassword123!',
            'password_confirm': 'DifferentPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "一致しません")
