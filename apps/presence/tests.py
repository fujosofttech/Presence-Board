from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from apps.employees.models import Department, Group, StatusMaster, Employee
from apps.presence.models import Presence, PresenceHistory
from apps.presence.events import event_bus


class SSEStreamViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.client.force_login(self.user)
        self.url = reverse('presence:sse-stream')

    def test_sse_stream_header(self):
        """SSE ストリームエンドポイントが正しいヘッダーを返すことを確認"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        self.assertEqual(response['Cache-Control'], 'no-cache')

class PresenceAPITestCase(APITestCase):
    def setUp(self):
        # ユーザーと認証設定
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.client.force_login(self.user)

        # テストマスタデータの作成
        self.department = Department.objects.create(name='開発部', display_order=1)
        self.group = Group.objects.create(department=self.department, name='開発1G', display_order=1)
        
        self.status_present = StatusMaster.objects.create(name='PRESENT', display_order=1)
        self.status_out = StatusMaster.objects.create(name='OUT', display_order=2)
        self.status_direct_home = StatusMaster.objects.create(name='DIRECT_HOME', display_order=3)
        self.status_meeting = StatusMaster.objects.create(name='MEETING', display_order=4)

        # ログインユーザーと紐づくEmployeeの作成 (emailが一致)
        self.employee = Employee.objects.create(
            employee_no='E0001',
            name='テスト太郎',
            email='test@example.com',
            department=self.department,
            group=self.group,
            display_order=1
        )

        # 別の社員の作成
        self.other_employee = Employee.objects.create(
            employee_no='E0002',
            name='テスト次郎',
            email='other@example.com',
            department=self.department,
            group=self.group,
            display_order=2
        )

        self.list_url = reverse('presence:presence-list')
        self.update_url = reverse('presence:presence-me')

    def test_get_presence_list(self):
        """在席一覧データが正しく取得できること"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 社員が2名返ってくること
        self.assertEqual(len(response.data), 2)
        
        # 存在しない場合のデフォルト値（PRESENT）がセットされていること
        emp0 = response.data[0]
        self.assertEqual(emp0['presence']['status'], 'PRESENT')
        self.assertEqual(emp0['presence']['destination'], '')

    def test_patch_presence_me_present(self):
        """PRESENT状態への更新が正しく動作すること"""
        data = {
            "status": "PRESENT",
            "destination": "",
            "return_time": None
        }
        response = self.client.patch(self.update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # DBにPresenceレコードが作成されていること
        presence = Presence.objects.get(employee=self.employee)
        self.assertEqual(presence.status.name, 'PRESENT')
        self.assertEqual(presence.destination, '')
        
        # 履歴レコードが作成されていること
        self.assertEqual(PresenceHistory.objects.filter(employee=self.employee).count(), 1)
        history = PresenceHistory.objects.first()
        self.assertEqual(history.status.name, 'PRESENT')

    def test_patch_presence_me_out_validation_success(self):
        """OUT状態への更新がバリデーション成功し、SSEイベントが発生すること"""
        # SSEブロードキャストテスト用のリスナーを登録
        q = event_bus.register()

        data = {
            "status": "OUT",
            "destination": "〇〇商事",
            "return_time": "2026-07-11T18:00:00+09:00"
        }
        response = self.client.patch(self.update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 履歴レコードとPresenceが正しく格納されていること
        presence = Presence.objects.get(employee=self.employee)
        self.assertEqual(presence.status.name, 'OUT')
        self.assertEqual(presence.destination, '〇〇商事')

        # SSE イベントバスに正しく流れているか
        event_name, event_data = q.get(timeout=1)
        self.assertEqual(event_name, 'presence_updated')
        self.assertEqual(event_data['employee_no'], 'E0001')
        self.assertEqual(event_data['status'], 'OUT')
        self.assertEqual(event_data['destination'], '〇〇商事')

        event_bus.unregister(q)

    def test_patch_presence_me_out_validation_error(self):
        """OUT状態で行先や戻り時間が未設定の場合、バリデーションエラーとなること"""
        data = {
            "status": "OUT",
            "destination": "",  # 空白不可
            "return_time": None # 必須
        }
        response = self.client.patch(self.update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 'E0001')
        self.assertIn('destination', response.data['details'])
        self.assertIn('return_time', response.data['details'])

    def test_patch_presence_me_direct_home_override(self):
        """DIRECT_HOMEのとき、return_timeが強制的にnullになること"""
        data = {
            "status": "DIRECT_HOME",
            "destination": "直帰します",
            "return_time": "2026-07-11T20:00:00+09:00" # 指定しても強制的にnullになるはず
        }
        response = self.client.patch(self.update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        presence = Presence.objects.get(employee=self.employee)
        self.assertEqual(presence.status.name, 'DIRECT_HOME')
        self.assertIsNone(presence.end_datetime)

    def test_patch_presence_me_invalid_status(self):
        """存在しないステータスを指定した場合にエラーとなること"""
        data = {
            "status": "UNKNOWN_STATUS",
            "destination": "",
            "return_time": None
        }
        response = self.client.patch(self.update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 'E0001')
