import re
import webbrowser
from kivy.lang import Builder
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel

# ============================================================
# ملاحظات التوافق مع iOS:
# 1. VideoPlayer من Kivy غير مدعوم على iOS - تم استبداله
# 2. TS streams تُفتح عبر VLC أو Infuse المثبتين على الجهاز
# 3. M3U8 (HLS) تُفتح مباشرة عبر متصفح Safari المدمج
# 4. روابط HTTP العادية تُنسخ مع إشعار للمستخدم
# ============================================================

KV = '''
MDScreenManager:
    id: screen_manager

    # --- الشاشة الرئيسية ---
    MDScreen:
        name: "main_screen"
        md_bg_color: 0.03, 0.03, 0.05, 1

        MDBoxLayout:
            orientation: 'vertical'
            padding: ["16dp", "20dp", "16dp", "16dp"]
            spacing: "14dp"

            # هيدر التطبيق
            MDBoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: "50dp"

                MDLabel:
                    text: "𝝠 l i e n 𝝴"
                    font_style: "H4"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 0, 0.33, 1

                MDIconButton:
                    icon: "refresh"
                    theme_icon_color: "Custom"
                    icon_color: 1, 1, 1, 1
                    on_release: app.fetch_m3u_from_url()

            # شريط البحث
            MDCard:
                size_hint_y: None
                height: "48dp"
                radius: [12, 12, 12, 12]
                md_bg_color: 0.08, 0.08, 0.12, 1
                elevation: 0
                padding: ["10dp", 0, "10dp", 0]

                MDBoxLayout:
                    orientation: 'horizontal'
                    spacing: "8dp"

                    MDIconButton:
                        icon: "magnify"
                        theme_icon_color: "Custom"
                        icon_color: 0.5, 0.5, 0.6, 1
                        pos_hint: {"center_y": .5}

                    TextInput:
                        id: search_input
                        hint_text: "البحث عن قناة، فيلم، باقة..."
                        hint_text_color: 0.4, 0.4, 0.5, 1
                        foreground_color: 1, 1, 1, 1
                        background_color: 0, 0, 0, 0
                        multiline: False
                        font_size: "15sp"
                        cursor_color: 1, 0, 0.33, 1
                        pos_hint: {"center_y": .5}
                        on_text: app.on_search_text_change(*args)

            # عداد القنوات
            MDLabel:
                id: counter_label
                text: "جاري الاتصال بالسيرفر وجلب القنوات..."
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.5, 0.5, 0.6, 1
                size_hint_y: None
                height: self.texture_size[1]

            # فلتر التصنيفات
            MDBoxLayout:
                id: filter_bar
                orientation: 'horizontal'
                size_hint_y: None
                height: "36dp"
                spacing: "8dp"

                ScrollView:
                    do_scroll_y: False
                    MDBoxLayout:
                        id: filter_buttons_box
                        orientation: 'horizontal'
                        spacing: "8dp"
                        adaptive_width: True

            # قائمة القنوات
            MDCard:
                radius: [16, 16, 16, 16]
                md_bg_color: 0.06, 0.06, 0.09, 1
                elevation: 0
                padding: ["2dp", "4dp", "2dp", "4dp"]

                ScrollView:
                    bar_width: "4dp"
                    scroll_type: ['content', 'bars']

                    MDList:
                        id: channel_list
                        spacing: "4dp"

            # Toast إشعار
            MDCard:
                id: toast_card
                size_hint_y: None
                height: "40dp"
                radius: [10, 10, 10, 10]
                md_bg_color: 1, 0, 0.33, 0.15
                line_color: 1, 0, 0.33, 0.4
                elevation: 0
                opacity: 0
                padding: ["10dp", 0, "10dp", 0]

                MDLabel:
                    id: toast_label
                    text: ""
                    halign: "center"
                    valign: "middle"
                    theme_text_color: "Custom"
                    text_color: 1, 0.3, 0.5, 1
                    bold: True
                    font_style: "Caption"
'''


class AlienXPlayerApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.M3U_URL = "https://manageilystore.rf.gd/uploads/main.m3u"
        self.channels = []
        self.filtered_channels = []
        self.all_groups = []
        self.current_group = "الكل"
        self.search_timer = None
        self.player_dialog = None
        return Builder.load_string(KV)

    def on_start(self):
        self.fetch_m3u_from_url()

    # ─────────────────────────────────────────
    # تحميل وتحليل ملف M3U
    # ─────────────────────────────────────────
    def fetch_m3u_from_url(self):
        self.root.ids.counter_label.text = "🔄 جاري تحميل ملف IPTV المحدث من السيرفر..."
        UrlRequest(
            self.M3U_URL,
            on_success=self.on_download_success,
            on_failure=self.on_download_error,
            on_error=self.on_download_error,
            timeout=15
        )

    def on_download_success(self, request, result):
        self.channels = []
        current_name = ""
        current_group = ""
        current_logo = ""

        lines = result.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#EXTINF:"):
                parts = line.split(",")
                current_name = parts[-1].strip() if parts else "قناة غير معروفة"
                group_match = re.search(r'group-title="([^"]+)"', line)
                current_group = group_match.group(1) if group_match else "عام"
                logo_match = re.search(r'tvg-logo="([^"]+)"', line)
                current_logo = logo_match.group(1) if logo_match else ""
            elif not line.startswith("#") and current_name:
                # تحديد نوع الرابط لمعالجة التشغيل الصحيح
                url_type = self._detect_stream_type(line)
                self.channels.append({
                    "name": current_name,
                    "group": current_group,
                    "logo": current_logo,
                    "url": line,
                    "type": url_type
                })
                current_name = ""

        # استخراج التصنيفات الفريدة
        groups = list(dict.fromkeys([ch["group"] for ch in self.channels]))
        self.all_groups = ["الكل"] + groups

        self.filtered_channels = self.channels
        self._build_filter_buttons()
        self.update_list_view()

    def _detect_stream_type(self, url):
        """تحديد نوع الرابط: hls / ts / rtmp / http"""
        url_lower = url.lower()
        if ".m3u8" in url_lower:
            return "hls"
        elif ".ts" in url_lower:
            return "ts"
        elif url_lower.startswith("rtmp"):
            return "rtmp"
        else:
            return "http"

    def on_download_error(self, request, error):
        self.root.ids.counter_label.text = "⚠️ فشل جلب الملف. تأكد من اتصال الإنترنت أو الرابط."

    # ─────────────────────────────────────────
    # فلتر التصنيفات
    # ─────────────────────────────────────────
    def _build_filter_buttons(self):
        from kivymd.uix.button import MDChip
        box = self.root.ids.filter_buttons_box
        box.clear_widgets()
        for group in self.all_groups:
            btn = MDRaisedButton(
                text=group,
                size_hint=(None, None),
                height="32dp",
                md_bg_color=(1, 0, 0.33, 1) if group == self.current_group else (0.1, 0.1, 0.15, 1),
                font_size="12sp"
            )
            btn.bind(on_release=lambda x, g=group: self.filter_by_group(g))
            box.add_widget(btn)

    def filter_by_group(self, group):
        self.current_group = group
        self._build_filter_buttons()
        query = self.root.ids.search_input.text.lower().strip()
        self._apply_filters(query, group)

    # ─────────────────────────────────────────
    # البحث
    # ─────────────────────────────────────────
    def on_search_text_change(self, instance, text):
        if self.search_timer:
            self.search_timer.cancel()
        self.search_timer = Clock.schedule_once(
            lambda dt: self._apply_filters(text.lower().strip(), self.current_group), 0.3
        )

    def _apply_filters(self, query, group):
        result = self.channels

        if group != "الكل":
            result = [ch for ch in result if ch["group"] == group]

        if query:
            result = [
                ch for ch in result
                if query in ch["name"].lower() or query in ch["group"].lower()
            ]

        self.filtered_channels = result
        self.update_list_view()

    # ─────────────────────────────────────────
    # عرض القائمة
    # ─────────────────────────────────────────
    def update_list_view(self):
        list_widget = self.root.ids.channel_list
        list_widget.clear_widgets()

        total = len(self.filtered_channels)
        self.root.ids.counter_label.text = f"✅ {total} قناة متاحة — البث المباشر"

        for ch in self.filtered_channels[:150]:
            # أيقونة مختلفة حسب نوع البث
            type_icon = {
                "hls": "television-play",
                "ts": "television-classic",
                "rtmp": "access-point",
                "http": "web"
            }.get(ch["type"], "play-circle")

            item = TwoLineAvatarIconListItem(
                text=ch["name"],
                secondary_text=f"📂 {ch['group']}  •  🔗 {ch['type'].upper()}",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                secondary_theme_text_color="Custom",
                secondary_text_color=(0.5, 0.5, 0.6, 1)
            )

            play_icon = IconLeftWidget(
                icon=type_icon,
                theme_icon_color="Custom",
                icon_color=(1, 0, 0.33, 1)
            )
            play_icon.bind(
                on_release=lambda x, ch=ch: self.open_stream(ch)
            )

            copy_icon = IconRightWidget(
                icon="content-copy",
                theme_icon_color="Custom",
                icon_color=(0.5, 0.5, 0.6, 1)
            )
            copy_icon.bind(
                on_release=lambda x, url=ch["url"], name=ch["name"]: self.copy_link(url, name)
            )

            item.add_widget(play_icon)
            item.add_widget(copy_icon)
            list_widget.add_widget(item)

    # ─────────────────────────────────────────
    # تشغيل البث — متوافق مع iOS بالكامل
    # ─────────────────────────────────────────
    def open_stream(self, ch):
        """
        iOS لا يدعم VideoPlayer من Kivy.
        الحل: فتح الرابط عبر VLC أو Safari حسب النوع.
        - HLS (m3u8) → Safari يشغلها natively
        - TS / RTMP  → VLC app عبر vlc://
        - HTTP       → نسخ الرابط + إشعار
        """
        url = ch["url"]
        name = ch["name"]
        stream_type = ch["type"]

        if stream_type == "hls":
            # Safari يدعم HLS بشكل أصلي
            webbrowser.open(url)
            self.show_toast(f"▶️ يفتح في Safari: {name[:20]}")

        elif stream_type in ("ts", "rtmp"):
            # محاولة فتح VLC أولاً
            vlc_url = f"vlc://{url}"
            try:
                webbrowser.open(vlc_url)
                self.show_toast(f"▶️ يفتح في VLC: {name[:20]}")
            except Exception:
                # fallback: نسخ الرابط
                Clipboard.copy(url)
                self.show_toast(f"📋 نُسخ الرابط (TS) — افتح VLC يدوياً")

        else:
            # HTTP عادي — نسخ الرابط
            Clipboard.copy(url)
            self.show_player_dialog(name, url)

    def show_player_dialog(self, name, url):
        """ديالوج يعطي خيارات التشغيل"""
        if self.player_dialog:
            self.player_dialog.dismiss()

        self.player_dialog = MDDialog(
            title=f"[b]{name}[/b]",
            text=f"نوع الرابط: HTTP\nتم نسخ الرابط تلقائياً\n\n{url[:60]}...",
            buttons=[
                MDFlatButton(
                    text="فتح في Safari",
                    on_release=lambda x: (webbrowser.open(url), self.player_dialog.dismiss())
                ),
                MDRaisedButton(
                    text="فتح في VLC",
                    md_bg_color=(1, 0, 0.33, 1),
                    on_release=lambda x: (webbrowser.open(f"vlc://{url}"), self.player_dialog.dismiss())
                ),
            ]
        )
        self.player_dialog.open()

    # ─────────────────────────────────────────
    # نسخ الرابط
    # ─────────────────────────────────────────
    def copy_link(self, url, name):
        Clipboard.copy(url)
        self.show_toast(f"📋 تم نسخ: {name[:25]}")

    # ─────────────────────────────────────────
    # Toast إشعار
    # ─────────────────────────────────────────
    def show_toast(self, message):
        self.root.ids.toast_label.text = message
        self.root.ids.toast_card.opacity = 1
        Clock.schedule_once(self.hide_toast, 2.5)

    def hide_toast(self, dt):
        self.root.ids.toast_card.opacity = 0


if __name__ == '__main__':
    AlienXPlayerApp().run()
