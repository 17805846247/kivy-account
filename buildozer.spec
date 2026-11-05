[app]
title = 我的工具包
package.name = myapp
package.domain = org.mytool
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
requirements = python3,kivy==2.2.1,jnius==1.4.1
p4a.branch = v2023.09.16
orientation = portrait
fullscreen = 0
android.api = 33
android.ndk = 23b
android.build_tools = 33.0.2
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
