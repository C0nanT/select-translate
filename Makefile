.PHONY: start test android android-apk

ANDROID_HOME ?= $(HOME)/Android/Sdk
ADB := $(ANDROID_HOME)/platform-tools/adb
APK := android/app/build/outputs/apk/debug/app-debug.apk

# roda preso ao terminal: Ctrl+C ou fechar o terminal desliga
start:
	python3 -u tradutor.py

# testes unitarios do PC (sem GTK/rede)
test:
	python3 -m unittest discover -s tests -v

# gera o APK debug e instala no tablet (USB, Depuracao USB ligada)
android: android-apk
	$(ADB) install -r $(APK)

# so gera o APK (fica em $(APK))
android-apk:
	cd android && ANDROID_HOME=$(ANDROID_HOME) ./gradlew assembleDebug
