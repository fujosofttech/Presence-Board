from django.db.models import Q
from typing import List
from apps.presence.services.search_parser import SearchQuery, get_dynamic_status_map

# 検索対象となるモデルのフィールド定義（部分一致）
# 今後、検索対象フィールドを追加する場合はこのリストに追加するだけで機能します
SEARCH_FIELDS = [
    'name__icontains',
    'employee_no__icontains',
    'presence__destination__icontains',
    'presence__status__name__icontains',
    'department__name__icontains',
    'group__name__icontains',
    'work_location__company_name__icontains',
    'work_location__office_name__icontains',
]

class SearchBuilder:
    """
    SearchQuery DTOからDjango ORM用の検索条件 (Qオブジェクトのリスト) を構築するビルダー。
    """

    @classmethod
    def build_conditions(cls, query: SearchQuery) -> List[Q]:
        conditions = []
        status_map = get_dynamic_status_map()

        for keyword in query.keywords:
            part_q = Q()
            
            # 定義された検索対象フィールドに対して動的に Q オブジェクトを組み立て
            for field_name in SEARCH_FIELDS:
                part_q |= Q(**{field_name: keyword})

            # 4. 日本語状態名から状態コードへのマッピング一致
            for jp_status, en_status in status_map.items():
                if jp_status in keyword:
                    part_q |= Q(presence__status__name=en_status)

            # 5. 状態コード直接指定（大文字小文字問わず）の一致
            upper_keyword = keyword.upper()
            if upper_keyword in ["PRESENT", "CUSTOMER", "OUT", "MEETING", "REMOTE", "HOLIDAY", "LEAVE", "DIRECT_HOME"]:
                part_q |= Q(presence__status__name=upper_keyword)

            if part_q:
                conditions.append(part_q)

        return conditions
