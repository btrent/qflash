[app]

# (str) Title of your application
title = QFlash

# (str) Package name
package.name = qflash

# (str) Package domain (needed for android/ios packaging)
package.domain = com.drinkngames

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,sgf,json,kv,txt,rst,mp3,atlas,ttf,so,db

# (list) Source files to exclude (let empty to not excluding anything)
#source.exclude_exts = spec

# (str) Application versionning (method 1)
# version.regex = __version__ = '(.*)'
# version.filename = %(source.dir)s/main.py

# (str) Application versioning (method 2)
version = 0.1

# (list) Application requirements
requirements = kivy

#orientation = all
orientation = portrait

#presplash.filename = /source/github/knave/img/splash.png
icon.filename = /source/github/qflash/img/lightbulb_orb.png

fullscreen = 0

#
# Android specific
#

# (list) Permissions
android.permissions = VIBRATE,INTERNET

# (int) Android API to use
#android.api = 21

# (int) Minimum API required (8 = Android 2.2 devices)
#android.minapi = 8

# (int) Android SDK version to use
#android.sdk = 8

# (str) Android NDK version to use
android.ndk = 8e

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
#android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
#android.sdk_path = 

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.renpy.android.PythonActivity

android.manifest.intent_filters = filters.xml

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2
