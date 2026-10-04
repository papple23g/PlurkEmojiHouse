import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from myapp.models import SiteViews


class Command(BaseCommand):
    help = "一次性讀取舊 Firebase 累積數；既有 SQL 計數不會被覆寫。"

    def handle(self, *args: object, **options: object) -> None:
        if SiteViews.objects.filter(pk="PlurkEmojiHouse").exists():
            self.stdout.write("計數已初始化，未變更。")
            return
        try:
            response = requests.get(
                "https://nidojs-project.firebaseio.com/PlurkEmojiHouse/WebSiteViews.json",
                timeout=15,
            )
            response.raise_for_status()
            total = response.json()
        except (requests.RequestException, ValueError) as error:
            raise CommandError("無法讀取舊累積數；未初始化，請稍後重試。") from error
        if type(total) is not int or not 0 <= total < 2**63 - 1:
            raise CommandError("舊累積數不是有效非負整數；未初始化。")
        counter, created = SiteViews.objects.get_or_create(
            name="PlurkEmojiHouse",
            defaults={"total": total, "imported_total": total, "imported_at": timezone.now()},
        )
        self.stdout.write(
            f"created={created} total={counter.total} imported_at={counter.imported_at.isoformat()}"
        )
