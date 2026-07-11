from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from apps.employees.models import Department, Group, WorkLocation, StatusMaster, Employee

class EmployeeAPITestCase(APITestCase):
    def setUp(self):
        # テスト用ユーザーの作成と認証設定
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # テストデータの作成
        self.department = Department.objects.create(name='開発部', display_order=1)
        self.group = Group.objects.create(department=self.department, name='開発1G', display_order=1)
        self.work_location = WorkLocation.objects.create(
            company_name='顧客A', office_name='本社', address='東京都', display_order=1
        )
        self.status_master = StatusMaster.objects.create(
            name=StatusMaster.StatusCode.PRESENT, display_order=1
        )
        self.employee = Employee.objects.create(
            employee_no='E0001',
            name='テスト太郎',
            email='taro@example.com',
            department=self.department,
            group=self.group,
            work_location=self.work_location,
            display_order=1
        )

        # URLの準備
        self.employee_list_url = reverse('employee-list')
        self.employee_detail_url = reverse('employee-detail', kwargs={'pk': self.employee.pk})

    def test_get_employee_list_authenticated(self):
        """認証済みで社員一覧を取得できることを確認"""
        response = self.client.get(self.employee_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'テスト太郎')

    def test_get_employee_list_unauthenticated(self):
        """未認証で社員一覧を取得しようとすると401になることを確認"""
        self.client.credentials()  # 資格情報をクリア
        response = self.client.get(self.employee_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'], 'E4001')

    def test_create_employee_success(self):
        """社員を新しく登録できることを確認"""
        data = {
            "employee_no": "E0002",
            "name": "テスト次郎",
            "email": "jiro@example.com",
            "department": self.department.id,
            "group": self.group.id,
            "work_location": self.work_location.id,
            "display_order": 2
        }
        response = self.client.post(self.employee_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Employee.objects.filter(employee_no="E0002").count(), 1)

    def test_create_employee_validation_error(self):
        """所属課とグループの整合性エラーが発生したときに指定形式のエラーが返ることを確認"""
        other_dept = Department.objects.create(name='営業部', display_order=2)
        # self.group は self.department に属しているため、other_dept との組み合わせはバリデーションエラー
        data = {
            "employee_no": "E0003",
            "name": "テスト花子",
            "email": "hanako@example.com",
            "department": other_dept.id,
            "group": self.group.id,
            "display_order": 3
        }
        response = self.client.post(self.employee_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 'E4000')
        self.assertIn('group', response.data['details'])

    def test_soft_delete_employee(self):
        """DELETEリクエストで物理削除されず、deleted_atが更新されることを確認"""
        response = self.client.delete(self.employee_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 物理削除されていないこと
        employee = Employee.objects.get(pk=self.employee.pk)
        self.assertIsNotNone(employee.deleted_at)

        # 取得APIからは除外されること
        response = self.client.get(self.employee_list_url)
        self.assertEqual(len(response.data), 0)

    def test_employee_search(self):
        """検索機能のテスト"""
        # 別の社員の追加
        Employee.objects.create(
            employee_no='E0002',
            name='佐藤次郎',
            email='satow@example.com',
            department=self.department,
            group=self.group,
            display_order=2
        )
        response = self.client.get(self.employee_list_url, {'search': '佐藤'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '佐藤次郎')

    def test_employee_filtering(self):
        """所属課/グループフィルタリングのテスト"""
        other_dept = Department.objects.create(name='営業部', display_order=2)
        other_group = Group.objects.create(department=other_dept, name='営業1G', display_order=1)
        Employee.objects.create(
            employee_no='E0002',
            name='営業社員',
            email='eigyo@example.com',
            department=other_dept,
            group=other_group,
            display_order=2
        )
        
        # 開発部で絞り込み
        response = self.client.get(self.employee_list_url, {'department': self.department.id})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'テスト太郎')

        # 営業部で絞り込み
        response = self.client.get(self.employee_list_url, {'department': other_dept.id})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '営業社員')
