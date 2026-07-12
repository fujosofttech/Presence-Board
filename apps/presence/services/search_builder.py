from django.db.models import Q
from typing import List
from apps.presence.services.search_parser import SearchQuery, get_dynamic_status_map

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
            # 1. 基本項目（氏名、社員番号、行先、ステータス英語名）の部分一致
            part_q |= Q(name__icontains=keyword)
            part_q |= Q(employee_no__icontains=keyword)
            part_q |= Q(presence__destination__icontains=keyword)
            part_q |= Q(presence__status__name__icontains=keyword)
            
            # 2. 組織階層（部署名、グループ名）の部分一致
            part_q |= Q(department__name__icontains=keyword)
            part_q |= Q(group__name__icontains=keyword)

            # 3. 勤務場所（会社名、事業所名）の部分一致（推奨①の対応）
            part_q |= Q(work_location__company_name__icontains=keyword)
            part_q |= Q(work_location__office_name__icontains=keyword)

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
