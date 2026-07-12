from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from apps.employees.models import Department, Group, StatusMaster, Employee
from apps.presence.models import Presence, PresenceHistory, FavoriteDestination, ScheduledStatus
from apps.presence.events import event_publisher, MemoryEventPublisher
from django.utils import timezone
from datetime import timedelta


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
        q = None
        if isinstance(event_publisher, MemoryEventPublisher):
            q = event_publisher.register()

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
        if q is not None:
            event_name, event_data = q.get(timeout=1)
            self.assertEqual(event_name, 'presence_updated')
            self.assertEqual(event_data['employee_no'], 'E0001')
            self.assertEqual(event_data['status'], 'OUT')
            self.assertEqual(event_data['destination'], '〇〇商事')

            event_publisher.unregister(q)

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


class PresenceSearchAPITestCase(APITestCase):
    def setUp(self):
        # ユーザーと認証設定
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.client.force_login(self.user)

        # テストマスタデータの作成
        self.dept_dev = Department.objects.create(name='開発部', display_order=1)
        self.dept_sales = Department.objects.create(name='営業部', display_order=2)
        
        self.group_dev1 = Group.objects.create(department=self.dept_dev, name='開発1G', display_order=1)
        self.group_sales1 = Group.objects.create(department=self.dept_sales, name='営業1G', display_order=1)
        
        self.status_present = StatusMaster.objects.create(name='PRESENT', display_order=1)
        self.status_out = StatusMaster.objects.create(name='OUT', display_order=2)

        # テスト社員の作成
        self.emp1 = Employee.objects.create(
            employee_no='E0001', name='山田太郎', email='yamada@example.com',
            department=self.dept_dev, group=self.group_dev1, display_order=1
        )
        self.emp2 = Employee.objects.create(
            employee_no='E0002', name='佐藤花子', email='sato@example.com',
            department=self.dept_sales, group=self.group_sales1, display_order=2
        )

        # Presence の設定
        Presence.objects.create(
            employee=self.emp1, status=self.status_present, destination='', updated_by=self.user
        )
        Presence.objects.create(
            employee=self.emp2, status=self.status_out, destination='〇〇商事', updated_by=self.user
        )

        self.search_url = reverse('presence:presence-search')

    def test_search_unauthenticated(self):
        """未認証でアクセスしたときに401エラーが返ること"""
        self.client.logout()
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_all(self):
        """パラメータなしの場合は全社員が返ること"""
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_search_q_by_name(self):
        """qによる氏名部分一致検索が正しく機能すること"""
        response = self.client.get(self.search_url, {'q': '山田'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '山田太郎')

    def test_search_q_by_employee_no(self):
        """qによる社員番号部分一致検索が正しく機能すること"""
        response = self.client.get(self.search_url, {'q': 'E0002'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '佐藤花子')

    def test_search_q_by_destination(self):
        """qによる行先部分一致検索が正しく機能すること"""
        response = self.client.get(self.search_url, {'q': '〇〇商事'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '佐藤花子')

    def test_search_q_by_status(self):
        """qによる状態名部分一致検索が正しく機能すること"""
        response = self.client.get(self.search_url, {'q': 'PRESENT'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '山田太郎')

    def test_search_by_individual_params(self):
        """個別パラメータでの絞り込みが正しく機能すること"""
        # name
        response = self.client.get(self.search_url, {'name': '山田'})
        self.assertEqual(len(response.data), 1)

        # employee_no
        response = self.client.get(self.search_url, {'employee_no': 'e0002'}) # 大文字小文字無視
        self.assertEqual(len(response.data), 1)

        # status
        response = self.client.get(self.search_url, {'status': 'out'}) # 大文字小文字無視
        self.assertEqual(len(response.data), 1)

        # department
        response = self.client.get(self.search_url, {'department': self.dept_dev.id})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '山田太郎')

        # group
        response = self.client.get(self.search_url, {'group': self.group_sales1.id})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '佐藤花子')

class FavoriteDestinationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.client.force_login(self.user)
        self.department = Department.objects.create(name='開発部', display_order=1)
        self.group = Group.objects.create(department=self.department, name='開発1G', display_order=1)
        self.employee = Employee.objects.create(
            employee_no='E0001', name='山田太郎', email='test@example.com',
            department=self.department, group=self.group, display_order=1
        )
        self.list_url = reverse('presence:favorite-list')
        
    def test_get_favorite_list_empty(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_post_and_get_favorite(self):
        data = {"destination": "〇〇株式会社", "display_order": 1}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FavoriteDestination.objects.count(), 1)

        response = self.client.get(self.list_url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['destination'], "〇〇株式会社")

    def test_post_duplicate_favorite(self):
        FavoriteDestination.objects.create(employee=self.employee, destination="〇〇株式会社", display_order=1)
        data = {"destination": "〇〇株式会社", "display_order": 2}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_favorite(self):
        favorite = FavoriteDestination.objects.create(employee=self.employee, destination="〇〇株式会社", display_order=1)
        delete_url = reverse('presence:favorite-detail', kwargs={'pk': favorite.id})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(FavoriteDestination.objects.count(), 0)

class RecentDestinationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.client.force_login(self.user)
        self.department = Department.objects.create(name='開発部', display_order=1)
        self.group = Group.objects.create(department=self.department, name='開発1G', display_order=1)
        self.employee = Employee.objects.create(
            employee_no='E0001', name='山田太郎', email='test@example.com',
            department=self.department, group=self.group, display_order=1
        )
        self.status_out = StatusMaster.objects.create(name='OUT', display_order=2)
        self.recent_url = reverse('presence:recent-list')

    def test_get_recent_destinations(self):
        # 古い履歴
        old_hist = PresenceHistory.objects.create(employee=self.employee, status=self.status_out, destination="古い会社")
        old_time = timezone.now() - timedelta(days=35)
        PresenceHistory.objects.filter(id=old_hist.id).update(created_at=old_time)
        
        # 新しい履歴（重複含む）
        PresenceHistory.objects.create(employee=self.employee, status=self.status_out, destination="B社")
        PresenceHistory.objects.create(employee=self.employee, status=self.status_out, destination="A社")
        PresenceHistory.objects.create(employee=self.employee, status=self.status_out, destination="B社")
        
        # 空の履歴
        PresenceHistory.objects.create(employee=self.employee, status=self.status_out, destination="")
        
        response = self.client.get(self.recent_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # B社とA社が返るはず（最後にB社が使われているのでB社が先）
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['destination'], "B社")
        self.assertEqual(response.data[1]['destination'], "A社")


class ScheduledStatusAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.client.force_login(self.user)
        self.department = Department.objects.create(name='開発部', display_order=1)
        self.group = Group.objects.create(department=self.department, name='開発1G', display_order=1)
        self.employee = Employee.objects.create(
            employee_no='E0001', name='山田太郎', email='test@example.com',
            department=self.department, group=self.group, display_order=1
        )
        self.status_out = StatusMaster.objects.create(name='OUT', display_order=1)
        self.status_present = StatusMaster.objects.create(name='PRESENT', display_order=2)
        self.status_direct_home = StatusMaster.objects.create(name='DIRECT_HOME', display_order=3)
        self.list_url = reverse('presence:scheduled-status-list')

    def test_post_scheduled_status(self):
        target_date = timezone.now().date() + timedelta(days=1)
        data = {
            "target_date": str(target_date),
            "status": "OUT",
            "destination": "得意先A",
            "start_time": "13:00",
            "end_time": "15:00",
            "memo": "訪問"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ScheduledStatus.objects.count(), 1)
        
        scheduled = ScheduledStatus.objects.first()
        self.assertEqual(scheduled.destination, "得意先A")

    def test_post_past_date_error(self):
        target_date = timezone.now().date() - timedelta(days=1)
        data = {
            "target_date": str(target_date),
            "status": "PRESENT"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("target_date", response.data['details'])

    def test_post_duplicate_error(self):
        target_date = timezone.now().date() + timedelta(days=1)
        ScheduledStatus.objects.create(
            employee=self.employee,
            target_date=target_date,
            status=self.status_present
        )
        data = {
            "target_date": str(target_date),
            "status": "OUT",
            "destination": "得意先A",
            "start_time": "13:00",
            "end_time": "15:00"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], "E0004")

    def test_post_validation_error(self):
        target_date = timezone.now().date() + timedelta(days=1)
        data = {
            "target_date": str(target_date),
            "status": "OUT",
            "destination": "", # OUT requires destination
            "end_time": None # OUT requires end_time
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("destination", response.data['details'])
        self.assertIn("end_time", response.data['details'])

    def test_get_scheduled_status_list(self):
        today = timezone.now().date()
        past = today - timedelta(days=1)
        future = today + timedelta(days=31)
        valid_date = today + timedelta(days=5)

        ScheduledStatus.objects.create(employee=self.employee, target_date=past, status=self.status_present)
        ScheduledStatus.objects.create(employee=self.employee, target_date=valid_date, status=self.status_present)
        ScheduledStatus.objects.create(employee=self.employee, target_date=future, status=self.status_present)
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return valid_date
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['target_date'], str(valid_date))

    def test_patch_scheduled_status(self):
        target_date = timezone.now().date() + timedelta(days=2)
        scheduled = ScheduledStatus.objects.create(
            employee=self.employee,
            target_date=target_date,
            status=self.status_present
        )
        detail_url = reverse('presence:scheduled-status-detail', kwargs={'pk': scheduled.id})
        data = {
            "status": "OUT",
            "destination": "新しい場所",
            "start_time": "10:00",
            "end_time": "12:00"
        }
        response = self.client.patch(detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        scheduled.refresh_from_db()
        self.assertEqual(scheduled.status.name, "OUT")
        self.assertEqual(scheduled.destination, "新しい場所")

    def test_patch_past_date_error(self):
        target_date = timezone.now().date() # Today is considered past/current, cannot be modified
        scheduled = ScheduledStatus.objects.create(
            employee=self.employee,
            target_date=target_date,
            status=self.status_present
        )
        detail_url = reverse('presence:scheduled-status-detail', kwargs={'pk': scheduled.id})
        data = {"status": "OUT", "destination": "test", "end_time": "10:00"}
        response = self.client.patch(detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], "E0006")

    def test_delete_scheduled_status(self):
        target_date = timezone.now().date() + timedelta(days=2)
        scheduled = ScheduledStatus.objects.create(
            employee=self.employee,
            target_date=target_date,
            status=self.status_present
        )
        detail_url = reverse('presence:scheduled-status-detail', kwargs={'pk': scheduled.id})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        scheduled.refresh_from_db()
        self.assertIsNotNone(scheduled.deleted_at)

    def test_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

