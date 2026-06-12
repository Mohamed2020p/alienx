import os
import re
from kivy.lang import Builder
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.list import TwoLineListItem

KV = '''
MDScreen:
    md_bg_color: 0.05, 0.05, 0.07, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: ["16dp", "24dp", "16dp", "16dp"]
        spacing: "16dp"

        MDLabel:
            text: "IPTV Stream Linker"
            font_style: "H4"
            bold: True
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: self.texture_size[1]
            halign: "left"

        MDCard:
            size_hint_y: None
            height: "50dp"
            radius: [14, 14, 14, 14]
            md_bg_color: 0.12, 0.12, 0.16, 1
            elevation: 0
            padding: ["12dp", 0, "12dp", 0]

            MDBoxLayout:
                orientation: 'horizontal'
                align_items: 'center'
                spacing: "10dp"

                MDIconButton:
                    icon: "magnify"
                    theme_icon_color: "Custom"
                    icon_color: 0.6, 0.6, 0.6, 1
                    pos_hint: {"center_y": .5}

                TextInput:
                    id: search_input
                    hint_text: "البحث عن قناة، فيلم، باقة..."
                    hint_text_color: 0.5, 0.5, 0.5, 1
                    foreground_color: 1, 1, 1, 1
                    background_color: 0, 0, 0, 0
                    multiline: False
                    font_name: "Roboto"
                    font_size: "16sp"
                    cursor_color: 0, 0.47, 1, 1
                    pos_hint: {"center_y": .5}
                    on_text: app.on_search_text_change(*args)

        MDLabel:
            id: counter_label
            text: "جاري فحص الملف..."
            font_style: "Caption"
            theme_text_color: "Custom"
            text_color: 0.5, 0.5, 0.6, 1
            size_hint_y: None
            height: self.texture_size[1]

        MDCard:
            radius: [20, 20, 20, 20]
            md_bg_color: 0.09, 0.09, 0.12, 1
            elevation: 0
            padding: ["4dp", "8dp", "4dp", "8dp"]

            ScrollView:
                bar_width: "4dp"
                scroll_type: ['content', 'bars']
                
                MDSelectionList:
                    id: channel_list
                    spacing: "8dp"

        MDCard:
            id: toast_card
            size_hint_y: None
            height: "45dp"
            radius: [12, 12, 12, 12]
            md_bg_color: 0, 0.47, 1, 0.2
            line_color: 0, 0.47, 1, 0.4
            elevation: 0
            opacity: 0
            padding: ["10dp", 0, "10dp", 0]
            
            MDLabel:
                id: toast_label
                text: "تم نسخ الرابط بنجاح"
                halign: "center"
                valign: "middle"
                theme_text_color: "Custom"
                text_color: 0, 0.6, 1, 1
                bold: True
                font_style: "Button"
'''

class iOSIPTVExtractor(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.M3U_FILE = "main.m3u"
        self.channels = []
        self.filtered_channels = []
        self.search_timer = None
        return Builder.load_string(KV)

    def on_start(self):
        self.parse_m3u()

    def parse_m3u(self):
        if not os.path.exists(self.M3U_FILE):
            self.root.ids.counter_label.text = "⚠️ لم يتم العثور على ملف main.m3u بجانب السكربت"
            return

        try:
            with open(self.M3U_FILE, "r", encoding="utf-8", errors="ignore") as f:
                current_name = ""
                current_group = ""
                
                for line in f:
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
        except Exception as e:
            self.root.ids.counter_label.text = f"خطأ: {str(e)}"

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
        self.root.ids.counter_label.text = f"تم العثور على {total} عنصر متاح"
        
        for ch in self.filtered_channels[:150]:
            item = TwoLineListItem(
                text=ch["name"],
                secondary_text=f"📂 {ch['group']}",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                secondary_theme_text_color="Custom",
                secondary_text_color=(0.5, 0.5, 0.6, 1)
            )
            item.bind(on_release=lambda x, url=ch["url"], name=ch["name"]: self.copy_link(url, name))
            list_widget.add_widget(item)

    def copy_link(self, url, name):
        Clipboard.copy(url)
        self.root.ids.toast_label.text = f"📋 تم نسخ رابط: {name[:25]}..."
        self.root.ids.toast_card.opacity = 1
        Clock.schedule_once(self.hide_toast, 2)

    def hide_toast(self, dt):
        self.root.ids.toast_card.opacity = 0

if __name__ == '__main__':
    iOSIPTVExtractor().run()
