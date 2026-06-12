import re
from kivy.lang import Builder
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget

# تصميم UI/UX فاخر متوافق مع نظام iOS ومشغل فيديو مدمج
KV = '''
MDScreenManager:
    id: screen_manager
    
    # --- الشاشة الرئيسية: تصفح وبحث ---
    MDScreen:
        name: "main_screen"
        md_bg_color: 0.03, 0.03, 0.05, 1  # خلفية سوداء عميقة مثل Apple TV

        MDBoxLayout:
            orientation: 'vertical'
            padding: ["16dp", "20dp", "16dp", "16dp"]
            spacing: "14dp"

            # هيدر التطبيق الأنيق
            MDBoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: "50dp"
                
                MDLabel:
                    text: "𝝠 l i e n 𝝴"
                    font_style: "H4"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 0, 0.33, 1  # نيون وردي حاد
                
                MDIconButton:
                    icon: "refresh"
                    theme_icon_color: "Custom"
                    icon_color: 1, 1, 1, 1
                    on_release: app.fetch_m3u_from_url()

            # شريط البحث بستايل كروت iOS المعزولة
            MDCard:
                size_hint_y: None
                height: "48dp"
                radius: [12, 12, 12, 12]
                md_bg_color: 0.08, 0.08, 0.12, 1
                elevation: 0
                padding: ["10dp", 0, "10dp", 0]

                MDBoxLayout:
                    orientation: 'horizontal'
                    align_items: 'center'
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

            # عدّاد القنوات وحالة الشبكة
            MDLabel:
                id: counter_label
                text: "جاري الاتصال بالسيرفر وجلب القنوات..."
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.5, 0.5, 0.6, 1
                size_hint_y: None
                height: self.texture_size[1]

            # حاوية عرض القنوات
            MDCard:
                radius: [16, 16, 16, 16]
                md_bg_color: 0.06, 0.06, 0.09, 1
                elevation: 0
                padding: ["2dp", "4dp", "2dp", "4dp"]

                ScrollView:
                    bar_width: "4dp"
                    scroll_type: ['content', 'bars']
                    
                    MDSelectionList:
                        id: channel_list
                        spacing: "6dp"

            # إشعار التنبيه العائم (Toast)
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

    # --- شاشة مشغل الفيديو السينمائي ---
    MDScreen:
        name: "player_screen"
        md_bg_color: 0, 0, 0, 1
        on_leave: video_player.state = 'stop'

        MDBoxLayout:
            orientation: 'vertical'

            # البار العلوي للمشغل لضمان العودة
            MDBoxLayout:
                size_hint_y: None
                height: "50dp"
                padding: ["10dp", 0, "10dp", 0]
                md_bg_color: 0.05, 0.05, 0.08, 1
                
                MDIconButton:
                    icon: "arrow-left"
                    theme_icon_color: "Custom"
                    icon_color: 1, 1, 1, 1
                    on_release: screen_manager.current = "main_screen"
                
                MDLabel:
                    id: player_title
                    text: "تشغيل البث المباشر"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    halign: "center"
                    valign: "middle"

            # عنصر مشغل الفيديو الفعلي المدعوم من الكور الأساسي لكيفي
            VideoPlayer:
                id: video_player
                source: ""
                state: 'stop'
                options: {'allow_stretch': True}
'''

class AlienXPlayerApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        # رابط ملفك المباشر والذكي على استضافتك
        self.M3U_URL = "https://manageilystore.rf.gd/uploads/main.m3u"
        self.channels = []
        self.filtered_channels = []
        self.search_timer = None
        return Builder.load_string(KV)

    def on_start(self):
        # تحميل القنوات فوراً عند إقلاع التطبيق
        self.fetch_m3u_from_url()

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
        
        # تحليل بيانات الملف النصية القادمة من السيرفر مباشرة
        lines = result.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#EXTINF:"):
                parts = line.split(",")
                current_name = parts[-1] if parts else "قناة غير معروفة"
                group_match = re.search(r'group-title="([^"]+)"', line)
                current_group = group_match.group(1) if group_match else "عام"
            elif not line.startswith("#") and current_name:
                self.channels.append({
                    "name": current_name,
                    "group": current_group,
                    "url": line
                })
                current_name = ""
        
        self.filtered_channels = self.channels
        self.update_list_view()

    def on_download_error(self, request, error):
        self.root.ids.counter_label.text = "⚠️ فشل جلب الملف. تأكد من اتصال الإنترنت أو الرابط."

    def on_search_text_change(self, instance, text):
        if self.search_timer:
            self.search_timer.cancel()
        self.search_timer = Clock.schedule_once(lambda dt: self.execute_filter(text), 0.3)

    def execute_filter(self, query):
        query = query.lower().strip()
        if not query:
            self.filtered_channels = self.channels
        else:
            self.filtered_channels = [
                ch for ch in self.channels 
                if query in ch["name"].lower() or query in ch["group"].lower()
            ]
        self.update_list_view()

    def update_list_view(self):
        list_widget = self.root.ids.channel_list
        list_widget.clear_widgets()
        
        total = len(self.filtered_channels)
        self.root.ids.counter_label.text = f"تم مزامنة {total} قناة متاح بثها الآن"
        
        # عرض أول 150 عنصر لضمان خفة وسلاسة التمرير الفائقة على أجهزة الايفون
        for ch in self.filtered_channels[:150]:
            item = TwoLineAvatarIconListItem(
                text=ch["name"],
                secondary_text=f"📂 {ch['group']}",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                secondary_theme_text_color="Custom",
                secondary_text_color=(0.5, 0.5, 0.6, 1)
            )
            
            # أيقونة التشغيل على اليسار
            play_icon = IconLeftWidget(icon="play-circle", theme_icon_color="Custom", icon_color=(1, 0, 0.33, 1))
            play_icon.bind(on_release=lambda x, url=ch["url"], name=ch["name"]: self.open_player(url, name))
            
            # أيقونة النسخ على اليمين
            copy_icon = IconRightWidget(icon="content-copy", theme_icon_color="Custom", icon_color=(0.5, 0.5, 0.6, 1))
            copy_icon.bind(on_release=lambda x, url=ch["url"], name=ch["name"]: self.copy_link(url, name))
            
            item.add_widget(play_icon)
            item.add_widget(copy_icon)
            list_widget.add_widget(item)

    def open_player(self, url, name):
        # تفعيل وتوجيه المشغل نحو شاشة البث المباشر
        self.root.ids.player_title.text = name
        self.root.ids.video_player.source = url
        self.root.ids.screen_manager.current = "player_screen"
        self.root.ids.video_player.state = 'play'

    def copy_link(self, url, name):
        Clipboard.copy(url)
        self.root.ids.toast_label.text = f"📋 تم نسخ رابط: {name[:25]}..."
        self.root.ids.toast_card.opacity = 1
        Clock.schedule_once(self.hide_toast, 2)

    def hide_toast(self, dt):
        self.root.ids.toast_card.opacity = 0

if __name__ == '__main__':
    AlienXPlayerApp().run()
