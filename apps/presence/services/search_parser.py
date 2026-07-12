import re
from dataclasses import dataclass, field
from typing import List, Dict
from apps.employees.models import StatusMaster

# ノイズワード定義 (敬称、日付関連など)
NOISE_WORDS = {"本日", "今日", "予定", "の予定"}
HONORIFICS = ["さん", "くん", "様"]

def get_dynamic_status_map() -> Dict[str, str]:
    """
    StatusMaster.StatusCode から動的にステータスマップを生成します。
    """
    # 類義語やカバーしきれない日本語表現のデフォルトマップ
    mapping = {
        "在籍": "PRESENT",
        "在席": "PRESENT",
        "在宅": "REMOTE",
        "テレワーク": "REMOTE",
        "常駐": "CUSTOMER",
        "打合せ": "MEETING",
        "打合せ中": "MEETING",
        "休み": "HOLIDAY",
        "有給": "HOLIDAY",
        "有休": "HOLIDAY",
        "帰宅": "LEAVE",
        "直帰": "DIRECT_HOME"
    }
    # StatusMaster.StatusCode から動的にラベルを取得してマージ
    for code, label in StatusMaster.StatusCode.choices:
        # 「・」で区切られたものを分解して登録
        parts = label.split("・")
        for part in parts:
            part = part.strip()
            if part:
                mapping[part] = code
                # 「在宅勤務」の場合は「在宅」も登録
                if "在宅" in part:
                    mapping["在宅"] = code
                # 「有給休暇」や「休暇」の場合は「有休」「有給」も登録
                if "休暇" in part:
                    mapping["有休"] = code
                    mapping["有給"] = code
    return mapping


@dataclass
class SearchQuery:
    """
    パースされた検索条件を格納するDTO。
    将来のAI(LLM)との連携で構造化データを直接流し込める拡張性を提供します。
    """
    keywords: List[str] = field(default_factory=list)      # あいまい検索用のクリーンなキーワード
    status_codes: List[str] = field(default_factory=list)  # 状態コード (PRESENT, OUT 等)


class SearchParser:
    """
    自然言語検索クエリをパースし、SearchQuery DTOを生成するサービス。
    """

    @classmethod
    def parse_query(cls, q: str) -> SearchQuery:
        """
        クエリ文字列 q を解析し、SearchQuery DTOを返します。
        """
        dto = SearchQuery()
        if not q:
            return dto

        # 全角・半角スペースでキーワードを分割
        keywords = re.split(r'\s+', q.strip())
        status_map = get_dynamic_status_map()

        for keyword in keywords:
            if not keyword:
                continue

            # 敬称などを末尾から除外したクリーンなキーワードを作成
            clean_keyword = keyword
            for honorific in HONORIFICS:
                if clean_keyword.endswith(honorific) and len(clean_keyword) > len(honorific):
                    clean_keyword = clean_keyword[:-len(honorific)]
                    break  # 敬称は1回だけ除去

            # ノイズワード以外であれば、キーワード検索対象として追加
            if clean_keyword not in NOISE_WORDS:
                dto.keywords.append(clean_keyword)

            # 日本語状態名へのマッピングチェック
            for jp_status, en_status in status_map.items():
                if jp_status in clean_keyword:
                    if en_status not in dto.status_codes:
                        dto.status_codes.append(en_status)

            # 英語の状態コード（大文字小文字問わず）が直接指定された場合のチェック
            upper_keyword = clean_keyword.upper()
            if upper_keyword in [code for code, _ in StatusMaster.StatusCode.choices]:
                if upper_keyword not in dto.status_codes:
                    dto.status_codes.append(upper_keyword)

        return dto
