[app]
title = AlienX
package.name = alienx
package.domain = org.mohamed
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,kivymd

orientation = portrait
osx.kivy_version = 2.3.0
ios.kivy_ios_version = master

# --- السطور السحرية لحل الخطأ اللعين وتخطي تفعيل توقيع أبل المدفوع ---
ios.codesign.allowed = False
ios.codesign.development = False
ios.codesign.production = False

[buildozer]
log_level = 2
warn_on_root = 1
