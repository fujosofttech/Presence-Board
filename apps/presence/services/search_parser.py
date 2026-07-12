import re
from django.db.models import Q
from typing import List

# ノイズワード定義 (敬称、日付関連など)
NOISE_WORDS = {"本日", "今日", "予定", "の予定"}
HONORIFICS = ["さん", "くん", "様"]

# 日本語状態名から状態コードへのマッピング定義
STATUS_MAP = {
    "在席": "PRESENT",
    "在籍": "PRESENT",
    "客先": "CUSTOMER",
    "常駐": "CUSTOMER",
    "外出": "OUT",
    "出張": "OUT",
    "会議": "MEETING",
    "打合せ": "MEETING",
    "在宅": "REMOTE",
    "リモート": "REMOTE",
    "テレワーク": "REMOTE",
    "休暇": "HOLIDAY",
    "休み": "HOLIDAY",
    "有給": "HOLIDAY",
    "退社": "LEAVE",
    "帰宅": "LEAVE",
    "直帰": "DIRECT_HOME"
}

class SearchParser:
    """
    自然言語検索クエリをパースし、Django ORM用のQオブジェクトのリストを生成するサービス。
    """

    @classmethod
    def parse_query_to_conditions(cls, q: str) -> List[Q]:
        """
        検索クエリ文字列 q を解析し、ANDで結合すべき Q オブジェクトのリストを返します。
        """
        if not q:
            return []

        # 全角・半角スペースでキーワードを分割
        keywords = re.split(r'\s+', q.strip())
        conditions = []

        for keyword in keywords:
            if not keyword:
                continue

            part_q = Q()

            # 敬称などを末尾から除外したクリーンなキーワードを作成
            clean_keyword = keyword
            for honorific in HONORIFICS:
                if clean_keyword.endswith(honorific) and len(clean_keyword) > len(honorific):
                    clean_keyword = clean_keyword[:-len(honorific)]
                    break  # 最初に見つかった敬称を1回だけ除去

            # キーワードが純粋なノイズワードでなければ、部分一致検索の対象にする
            if clean_keyword not in NOISE_WORDS:
                part_q |= Q(name__icontains=clean_keyword)
                part_q |= Q(employee_no__icontains=clean_keyword)
                part_q |= Q(presence__destination__icontains=clean_keyword)
                part_q |= Q(presence__status__name__icontains=clean_keyword)
                part_q |= Q(department__name__icontains=clean_keyword)
                part_q |= Q(group__name__icontains=clean_keyword)

            # キーワード内に状態日本語名が含まれる場合、ステータスコード検索を追加
            for jp_status, en_status in STATUS_MAP.items():
                if jp_status in clean_keyword:
                    part_q |= Q(presence__status__name=en_status)

            if part_q:
                conditions.append(part_q)

        return conditions
