from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from apps.employees.models import Department, Group, StatusMaster, Employee, WorkLocation
from apps.presence.models import Presence, PresenceHistory, FavoriteDestination, ScheduledStatus, AuditLog
from apps.presence.events import event_publisher, MemoryEventPublisher
from django.utils import timezone
from datetime import timedelta
from django.core.management import call_command
from io import StringIO


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

    def test_invalid_event_name_raises_value_error(self):
        """イベント種別整理: 定義外のイベント名をブロードキャストしようとした場合に ValueError が発生することを確認"""
        from apps.presence.events import event_publisher
        with self.assertRaises(ValueError):
            event_publisher.broadcast("invalid_event_type_name_test", {"dummy": "data"})

    def test_event_publisher_subscribe_and_broadcast(self):
        """Subscription と MemoryEventPublisher による購読と配信のテスト"""
        from apps.presence.events import event_publisher
        subscription = event_publisher.subscribe()
        
        # 配信
        test_data = {"test_key": "test_val"}
        event_publisher.broadcast("presence_updated", test_data)
        
        # 受信
        event_name, data = subscription.get(timeout=1)
        self.assertEqual(event_name, "presence_updated")
        self.assertEqual(data, test_data)
        
        subscription.close()

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
        self.status_remote = StatusMaster.objects.create(name='REMOTE', display_order=3)

        # 勤務場所の作成
        self.work_location1 = WorkLocation.objects.create(
            company_name="顧客A", office_name="本社", address="東京都", display_order=1
        )

        # テスト社員の作成
        self.emp1 = Employee.objects.create(
            employee_no='E0001', name='山田太郎', email='yamada@example.com',
            department=self.dept_dev, group=self.group_dev1, display_order=1
        )
        self.emp2 = Employee.objects.create(
            employee_no='E0002', name='佐藤花子', email='sato@example.com',
            department=self.dept_sales, group=self.group_sales1, work_location=self.work_location1, display_order=2
        )
        self.emp3 = Employee.objects.create(
            employee_no='E0003', name='鈴木一郎', email='suzuki@example.com',
            department=self.dept_dev, group=self.group_dev1, display_order=3
        )

        # Presence の設定
        Presence.objects.create(
            employee=self.emp1, status=self.status_present, destination='', updated_by=self.user
        )
        Presence.objects.create(
            employee=self.emp2, status=self.status_out, destination='〇〇商事', updated_by=self.user
        )
        Presence.objects.create(
            employee=self.emp3, status=self.status_remote, destination='', updated_by=self.user
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
        self.assertEqual(len(response.data), 3)

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

    def test_search_q_natural_language(self):
        """自然言語を意識したq検索（敬称除外、部署名検索、日本語状態名検索、複数語AND検索）が動作すること"""
        # 「田中さん」→「田中」 (敬称除外) -> テストデータにはいないが、山田さんでテスト
        response = self.client.get(self.search_url, {'q': '山田さん'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '山田太郎')

        # 「本日 外出」 (ノイズ除外＋ステータスマップ)
        response = self.client.get(self.search_url, {'q': '本日 外出'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '佐藤花子')

        # 「今日 在宅」 (ノイズ除外＋ステータスマップ)
        response = self.client.get(self.search_url, {'q': '今日 在宅'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '鈴木一郎')

        # 「営業部 外出」 (複数語AND)
        response = self.client.get(self.search_url, {'q': '営業部 外出'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '佐藤花子')

        # 「山田 開発部 在籍」 (3語AND)
        response = self.client.get(self.search_url, {'q': '山田 開発部 在籍'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '山田太郎')

        # 「PRESENT」 (英語ステータス直接検索)
        response = self.client.get(self.search_url, {'q': 'PRESENT'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '山田太郎')

        # 「present」 (英語ステータス直接検索・小文字)
        response = self.client.get(self.search_url, {'q': 'present'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '山田太郎')

        # 「在席」 (ステータスマップ「在席」)
        response = self.client.get(self.search_url, {'q': '在席'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '山田太郎')

        # 「在宅」 (ステータスマップ「在宅」)
        response = self.client.get(self.search_url, {'q': '在宅'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '鈴木一郎')

        # 「リモート」 (ステータスマップ「リモート」)
        response = self.client.get(self.search_url, {'q': 'リモート'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '鈴木一郎')

        # 「顧客A」 (勤務地会社名検索)
        response = self.client.get(self.search_url, {'q': '顧客A'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '佐藤花子')

        # 「本社」 (勤務地事業所名検索)
        response = self.client.get(self.search_url, {'q': '本社'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '佐藤花子')

        # マッチしない組み合わせ
        response = self.client.get(self.search_url, {'q': '山田 外出'})
        self.assertEqual(len(response.data), 0)

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
        self.assertEqual(len(response.data), 2)
        self.assertTrue(any(emp['name'] == '山田太郎' for emp in response.data))
        self.assertTrue(any(emp['name'] == '鈴木一郎' for emp in response.data))

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

    def test_cannot_delete_other_employee_favorite(self):
        """他人のお気に入り行先を削除しようとした場合に404エラーになること"""
        other_employee = Employee.objects.create(
            employee_no='E0002', name='テスト次郎', email='jiro@example.com',
            department=self.department, group=self.group, display_order=2
        )
        other_favorite = FavoriteDestination.objects.create(
            employee=other_employee, destination="〇〇株式会社", display_order=1
        )
        delete_url = reverse('presence:favorite-detail', kwargs={'pk': other_favorite.id})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 他人のお気に入りが削除されていないこと
        self.assertEqual(FavoriteDestination.objects.count(), 1)


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
        target_date = timezone.localdate() + timedelta(days=1)
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
        target_date = timezone.localdate() - timedelta(days=1)
        data = {
            "target_date": str(target_date),
            "status": "PRESENT"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("target_date", response.data['details'])

    def test_post_duplicate_error(self):
        target_date = timezone.localdate() + timedelta(days=1)
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
        target_date = timezone.localdate() + timedelta(days=1)
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
        today = timezone.localdate()
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
        target_date = timezone.localdate() + timedelta(days=2)
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
        target_date = timezone.localdate() # Today is considered past/current, cannot be modified
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
        target_date = timezone.localdate() + timedelta(days=2)
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

    def test_cannot_modify_other_employee_scheduled_status(self):
        """他人の ScheduledStatus に対する変更・削除ができない（404 になる）ことを確認"""
        other_employee = Employee.objects.create(
            employee_no='E0002',
            name='テスト次郎',
            email='jiro@example.com',
            department=self.department,
            group=self.group,
            display_order=2
        )
        target_date = timezone.localdate() + timedelta(days=2)
        other_scheduled = ScheduledStatus.objects.create(
            employee=other_employee,
            target_date=target_date,
            status=self.status_present
        )

        detail_url = reverse('presence:scheduled-status-detail', kwargs={'pk': other_scheduled.id})

        # 他人の予定を変更しようとする
        data = {"destination": "侵入テスト"}
        response = self.client.patch(detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 他人の予定を削除しようとする
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_patch_duplicate_error(self):
        """PATCHで既存の日付に変更しようとした場合に重複エラーになること"""
        date1 = timezone.localdate() + timedelta(days=2)
        date2 = timezone.localdate() + timedelta(days=3)
        ScheduledStatus.objects.create(employee=self.employee, target_date=date1, status=self.status_present)
        scheduled2 = ScheduledStatus.objects.create(employee=self.employee, target_date=date2, status=self.status_present)

        detail_url = reverse('presence:scheduled-status-detail', kwargs={'pk': scheduled2.id})
        data = {"target_date": str(date1)}
        response = self.client.patch(detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], "E0004")

    def test_post_edit_delete_repost(self):
        """登録 → 編集 → 削除 → 再登録 の一連の流れが成功すること"""
        target_date = timezone.localdate() + timedelta(days=1)
        
        # 1. 登録
        data = {
            "target_date": str(target_date),
            "status": "OUT",
            "destination": "初期行先",
            "end_time": "15:00"
        }
        res1 = self.client.post(self.list_url, data, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        scheduled_id = res1.data['id']

        # 2. 編集
        detail_url = reverse('presence:scheduled-status-detail', kwargs={'pk': scheduled_id})
        res2 = self.client.patch(detail_url, {"destination": "変更行先"}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['destination'], "変更行先")

        # 3. 削除
        res3 = self.client.delete(detail_url)
        self.assertEqual(res3.status_code, status.HTTP_204_NO_CONTENT)

        # 4. 再登録 (削除されているので同じ日付で登録できるはず)
        data['destination'] = "再登録行先"
        res4 = self.client.post(self.list_url, data, format='json')
        self.assertEqual(res4.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res4.data['destination'], "再登録行先")


class ApplyScheduledStatusTestCase(APITestCase):
    def setUp(self):
        # ユーザーと認証設定
        self.user = User.objects.create_superuser(username='admin', email='admin@example.com', password='password123')
        
        # テストマスタデータの作成
        self.department = Department.objects.create(name='開発部', display_order=1)
        self.group = Group.objects.create(department=self.department, name='開発1G', display_order=1)
        
        self.status_present = StatusMaster.objects.create(name='PRESENT', display_order=1)
        self.status_out = StatusMaster.objects.create(name='OUT', display_order=2)

        self.employee = Employee.objects.create(
            employee_no='E0001',
            name='テスト太郎',
            email='test@example.com',
            department=self.department,
            group=self.group,
            display_order=1
        )

    def test_apply_scheduled_status_idempotency(self):
        """バッチ実行による適用と冪等性のテスト"""
        today = timezone.localdate()
        
        # 当日の予定を作成
        ScheduledStatus.objects.create(
            employee=self.employee,
            target_date=today,
            status=self.status_out,
            destination="テスト先",
            start_time="10:00",
            end_time="18:00"
        )
        
        out = StringIO()
        
        # 1回目の実行
        call_command('apply_scheduled_status', stdout=out)
        self.assertIn("1 件適用", out.getvalue())
        
        # PresenceとHistoryが作成されていることを確認
        presence = Presence.objects.filter(employee=self.employee).first()
        self.assertIsNotNone(presence)
        self.assertEqual(presence.status.name, "OUT")
        self.assertEqual(presence.destination, "テスト先")
        
        history_count = PresenceHistory.objects.filter(employee=self.employee).count()
        self.assertEqual(history_count, 1)
        
        # 2回目の実行 (冪等性)
        out = StringIO()
        call_command('apply_scheduled_status', stdout=out)
        self.assertIn("1 件スキップ", out.getvalue())
        
        # Historyが増えていないことを確認
        new_history_count = PresenceHistory.objects.filter(employee=self.employee).count()
        self.assertEqual(new_history_count, 1)


    def test_batch_broadcast_on_apply_scheduled_status(self):
        """自動反映バッチの実行時に SSE 経由でステータス更新イベントがブロードキャストされることを確認"""
        from unittest.mock import patch
        from apps.presence.models import ScheduledStatus
        from datetime import date
        
        # 予定データの作成
        ScheduledStatus.objects.create(
            employee=self.employee,
            target_date=date.today(),
            status=self.status_out,
            destination="本社"
        )
        
        with patch('apps.presence.management.commands.apply_scheduled_status.event_publisher') as mock_pub:
            # コマンド実行
            call_command('apply_scheduled_status')
            
            # ブロードキャストが正しく呼ばれたか確認
            mock_pub.broadcast.assert_called_once()
            call_args = mock_pub.broadcast.call_args[0]
            self.assertEqual(call_args[0], 'presence_updated')
            self.assertEqual(call_args[1]['employee_no'], self.employee.employee_no)
            self.assertEqual(call_args[1]['status'], 'OUT')


class AuditLogAndHistorySearchViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='adminuser', email='admin@example.com', password='password123')
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)

        self.department = Department.objects.create(name='開発部', display_order=1)
        self.group = Group.objects.create(department=self.department, name='開発1G', display_order=1)
        self.employee = Employee.objects.create(
            employee_no='E9999',
            name='テスト九郎',
            email='test9@example.com',
            department=self.department,
            group=self.group,
            display_order=100
        )
        self.status_present = StatusMaster.objects.create(name='PRESENT', display_order=1)
        self.status_out = StatusMaster.objects.create(name='OUT', display_order=2)
        
        # 既存ログを一旦クリアしてテストしやすくする
        AuditLog.objects.all().delete()
        PresenceHistory.objects.all().delete()

    def test_login_signals_create_audit_logs(self):
        """ログイン・ログアウト・ログイン失敗シグナルが監査ログを生成することを確認"""
        from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
        
        # ログイン成功シグナル
        user_logged_in.send(sender=User, request=None, user=self.user)
        log1 = AuditLog.objects.filter(action='LOGIN_SUCCESS').first()
        self.assertIsNotNone(log1)
        self.assertIn("ログインに成功しました", log1.description)
        self.assertEqual(log1.user, self.user)
        
        # ログアウトシグナル
        user_logged_out.send(sender=User, request=None, user=self.user)
        log2 = AuditLog.objects.filter(action='LOGOUT').first()
        self.assertIsNotNone(log2)
        self.assertIn("ログアウトしました", log2.description)
        self.assertEqual(log2.user, self.user)
        
        # ログイン失敗シグナル
        user_login_failed.send(sender=User, credentials={'username': 'adminuser'}, request=None)
        log3 = AuditLog.objects.filter(action='LOGIN_FAILED').first()
        self.assertIsNotNone(log3)
        self.assertIn("ログイン試行に失敗しました", log3.description)
        self.assertEqual(log3.user, self.user)

    def test_presence_change_creates_audit_log(self):
        """状態変更時に自動的に状態変更監査ログが作成されることを確認"""
        Presence.objects.create(
            employee=self.employee,
            status=self.status_present,
            destination="本社"
        )
        log = AuditLog.objects.filter(action='PRESENCE_UPDATE').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.employee, self.employee)
        self.assertIn("状態: PRESENT", log.description)
        self.assertIn("行先: 本社", log.description)

    def test_admin_master_operations_create_audit_logs(self):
        """管理者マスタ操作（作成・更新・削除）で管理操作ログが作成されることを確認"""
        # 作成
        new_dep = Department.objects.create(name='人事部', display_order=2)
        log_create = AuditLog.objects.filter(action='ADMIN_OP', description__contains="課 が新規作成されました").first()
        self.assertIsNotNone(log_create)
        self.assertIn("人事部", log_create.description)

        # 更新
        new_dep.name = '総務部'
        new_dep.save()
        log_update = AuditLog.objects.filter(action='ADMIN_OP', description__contains="課 が更新されました").first()
        self.assertIsNotNone(log_update)
        self.assertIn("総務部", log_update.description)

        # 削除
        new_dep.delete()
        log_delete = AuditLog.objects.filter(action='ADMIN_OP', description__contains="課 が削除されました").first()
        self.assertIsNotNone(log_delete)

    def test_presence_history_search_api(self):
        """状態変更履歴の検索APIが正しい結果を返すことを確認"""
        # 履歴データの仕込み
        PresenceHistory.objects.create(
            employee=self.employee,
            status=self.status_present,
            destination="自社",
            start_datetime=timezone.now() - timedelta(days=2)
        )
        
        PresenceHistory.objects.create(
            employee=self.employee,
            status=self.status_out,
            destination="客先A",
            start_datetime=timezone.now() - timedelta(days=1)
        )

        url = reverse('presence:presence-history')

        # 1. 絞り込みなしで全件取得
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

        # 2. 社員(ID)で絞り込み
        response = self.client.get(url, {'employee': self.employee.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # 3. 社員番号で絞り込み
        response = self.client.get(url, {'employee': 'E9999'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # 4. 状態(ID)で絞り込み
        response = self.client.get(url, {'status': self.status_out.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['destination'], '客先A')

        # 5. 状態名で絞り込み
        response = self.client.get(url, {'status': 'PRESENT'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['destination'], '自社')

        # 6. 期間(start_date / end_date)で絞り込み
        tomorrow_str = (timezone.localdate() + timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_str = (timezone.localdate() - timedelta(days=1)).strftime('%Y-%m-%d')

        response = self.client.get(url, {'start_date': yesterday_str, 'end_date': tomorrow_str})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # 7. 不正な日付形式
        response = self.client.get(url, {'start_date': 'invalid-date'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 'E0001')

    def test_prune_old_data_command(self):
        """prune_old_data コマンドが指定日数を経過した履歴と監査ログを正しく削除することを確認"""
        # 1. 閾値より古いデータ
        old_time = timezone.now() - timedelta(days=400)
        h_old = PresenceHistory.objects.create(
            employee=self.employee,
            status=self.status_present,
            destination="大昔",
        )
        PresenceHistory.objects.filter(id=h_old.id).update(created_at=old_time)

        audit_old = AuditLog.objects.create(
            action='LOGIN_SUCCESS',
            description='大昔のログイン',
        )
        AuditLog.objects.filter(id=audit_old.id).update(created_at=old_time)

        # 2. 新しいデータ (閾値以内)
        h_new = PresenceHistory.objects.create(
            employee=self.employee,
            status=self.status_present,
            destination="最近",
        )
        audit_new = AuditLog.objects.create(
            action='LOGIN_SUCCESS',
            description='最近のログイン',
        )

        # コマンド実行
        out = StringIO()
        call_command('prune_old_data', stdout=out)
        
        # 削除のログ文が出力されているか
        self.assertIn("PresenceHistory", out.getvalue())
        self.assertIn("AuditLog", out.getvalue())

        # 古いデータが削除され、新しいデータが残っているか
        self.assertFalse(PresenceHistory.objects.filter(id=h_old.id).exists())
        self.assertTrue(PresenceHistory.objects.filter(id=h_new.id).exists())
        self.assertFalse(AuditLog.objects.filter(id=audit_old.id).exists())
        self.assertTrue(AuditLog.objects.filter(id=audit_new.id).exists())

    def test_ai_token_operation_audit_log(self):
        """Token認証を使用したリクエスト時に監査ログにAIエージェント情報が記録されることを確認"""
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=self.user)
        
        # ユーザーと社員のメールアドレスを一致させる
        self.employee.email = self.user.email
        self.employee.save()
        
        # クライアントでToken認証を使用
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # 在席情報を更新
        url = reverse('presence:presence-me')
        data = {
            'status': 'OUT',
            'destination': '客先B',
            'return_time': '2026-07-12T23:59:59+09:00'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 生成された監査ログを確認
        log = AuditLog.objects.filter(action='PRESENCE_UPDATE').first()
        self.assertIsNotNone(log)
        self.assertIn("AIエージェント操作", log.description)
        self.assertIn(f"Token: {token.key[:8]}", log.description)

    def test_mcp_tools(self):
        """MCP用Python関数ツール群が正しく動作することを確認"""
        from apps.presence.services import mcp_tools
        
        # 1. presence_update
        res_update = mcp_tools.presence_update(
            employee_no=self.employee.employee_no,
            status_name='OUT',
            destination='客先C',
            end_datetime_str='2026-07-12T23:59:59+09:00',
            performer_username=self.user.username
        )
        self.assertEqual(res_update['status'], 'OUT')
        self.assertEqual(res_update['destination'], '客先C')
        
        # 2. employee_find
        res_find = mcp_tools.employee_find(employee_no=self.employee.employee_no)
        self.assertEqual(res_find['name'], self.employee.name)
        self.assertEqual(res_find['status'], 'OUT')
        self.assertEqual(res_find['destination'], '客先C')
        
        # 3. presence_search
        res_search = mcp_tools.presence_search(query=self.employee.name)
        self.assertEqual(len(res_search), 1)
        self.assertEqual(res_search[0]['employee_no'], self.employee.employee_no)
        
        # 4. presence_list
        res_list = mcp_tools.presence_list(department_name=self.department.name)
        self.assertEqual(len(res_list), 1)
        self.assertEqual(res_list[0]['employee_no'], self.employee.employee_no)
