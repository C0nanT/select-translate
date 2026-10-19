.PHONY: start test test-pc test-android hooks android android-apk

ANDROID_HOME ?= $(HOME)/Android/Sdk
ADB := $(ANDROID_HOME)/platform-tools/adb
APK := android/app/build/outputs/apk/debug/app-debug.apk

# roda preso ao terminal: Ctrl+C ou fechar o terminal desliga
start:
	python3 -u pc/translator.py

# PC + Android
test: test-pc test-android

# testes unitarios do PC (sem GTK/rede)
test-pc:
	python3 -m unittest discover -s pc/tests -v

# testes unitarios do Android (Gradle, sem aparelho): nucleo (JVM puro) + app
test-android:
	cd android && ANDROID_HOME=$(ANDROID_HOME) ./gradlew :core:test :app:testDebugUnitTest

# ativa o pre-push versionado em hooks/ (uma vez por clone; repetir e seguro)
hooks:
	git config core.hooksPath hooks
	chmod +x hooks/pre-push

# gera o APK debug e instala no tablet (USB, Depuracao USB ligada)
android: android-apk
	$(ADB) install -r $(APK)

# so gera o APK (fica em $(APK))
android-apk:
	cd android && ANDROID_HOME=$(ANDROID_HOME) ./gradlew assembleDebug
