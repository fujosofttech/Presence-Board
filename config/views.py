from django.views.generic import TemplateView

class IndexView(TemplateView):
    """
    Vue SPA エントリーポイント (index.html) を配信するビュー。
    """
    template_name = "index.html"
