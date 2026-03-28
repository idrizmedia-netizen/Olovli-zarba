[app]

# (str) Ilova nomi
title = Olovli Zarba

# (str) Paket nomi (faqat kichik harflar va pastki chiziq)
package.name = olovli_zarba

# (str) Paket domeni (identifikatsiya uchun)
package.domain = org.idrizmedia

# (str) Manba kodlari joylashgan papka
source.dir = .

# (list) Ilovaga qo'shiladigan fayl kengaytmalari
source.include_exts = py,png,jpg,kv,atlas,db,txt

# (str) Ilova versiyasi
version = 1.0

# (list) Kerakli kutubxonalar (Requirements)
requirements = python3,kivy==2.3.0,sqlite3,hostpython3

# (str) Asosiy logotip fayli
icon.filename = icon.png

# (str) Ekran holati (faqat vertikal)
orientation = portrait

# (bool) To'liq ekran rejimi
fullscreen = 1

# (list) Android arxitekturalari (zamonaviy telefonlar uchun)
android.archs = arm64-v8a, armeabi-v7a

# (int) Android API darajasi (Google Play talabi bo'yicha)
android.api = 31
android.build_tools_version = 31.0.0

# (int) Minimal Android API (Android 5.0+)
android.minapi = 21

# (int) Android NDK versiyasi
android.ndk = 23b
android.accept_sdk_license = True

# (str) Android SDK yo'li (Buildozer o'zi yuklab oladi)
# android.sdk_path = 

# (list) Android ruxsatnomalari
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (bool) Ilova o'chirilganda ma'lumotlarni saqlab qolish
android.allow_backup = True

# (str) Android loglevel
android.logcat_filters = *:S python:D

# (bool) Buildozer-ni root foydalanuvchi sifatida ishlatish (agar kerak bo'lsa)
warn_on_root = 1

[buildozer]

# (int) Log darajasi (2 - batafsil xatoliklarni ko'rsatadi)
log_level = 2

# (str) Bin papkasi (tayyor APK shu yerga tushadi)
bin_dir = ./bin
