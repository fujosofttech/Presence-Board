from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, AuthenticationFailed
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Django REST Framework の例外をキャッチし、共通のエラーレスポンス形式に変換する。
    仕様書 06_API設計.md に準拠:
    {
        "error_code": "E0001",
        "message": "エラーメッセージ",
        "details": {}
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        # 認証されていない場合や認証に失敗した場合はステータスコードを 401 Unauthorized に書き換える
        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            response.status_code = status.HTTP_401_UNAUTHORIZED

        # ステータスコードに応じたエラーコードと一般的なメッセージの設定
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_code = "E4000"
            message = "入力内容にエラーがあります。"
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            error_code = "E4001"
            message = "認証情報が無効であるか、提供されていません。"
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            error_code = "E4003"
            message = "このアクションを実行する権限がありません。"
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            error_code = "E4004"
            message = "該当するリソースが見つかりません。"
        else:
            error_code = f"E{response.status_code}"
            message = "エラーが発生しました。"

        details = response.data

        response.data = {
            "error_code": error_code,
            "message": message,
            "details": details
        }
    else:
        # 未ハンドリングのサーバーエラー (500 Internal Server Error など)
        logger.error("Unhandled exception occurred: %s", str(exc), exc_info=exc)
        response = Response(
            {
                "error_code": "E5000",
                "message": "サーバー内部でエラーが発生しました。",
                "details": {"error": str(exc)}
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
