.PHONY: start test test-pc test-android hooks android android-apk

ANDROID_HOME ?= $(HOME)/Android/Sdk
ADB := $(ANDROID_HOME)/platform-tools/adb
APK := android/app/build/outputs/apk/debug/app-debug.apk

# runs attached to the terminal: Ctrl+C or closing the terminal stops it
start:
	python3 -u pc/translator.py

# PC + Android
test: test-pc test-android

# PC unit tests (no GTK/network)
test-pc:
	python3 -m unittest discover -s pc/tests -v

# Android unit tests (Gradle, no device): core (pure JVM) + app
test-android:
	cd android && ANDROID_HOME=$(ANDROID_HOME) ./gradlew :core:test :app:testDebugUnitTest

# enables the pre-push hook versioned in hooks/ (once per clone; safe to repeat)
hooks:
	git config core.hooksPath hooks
	chmod +x hooks/pre-push

# builds the debug APK and installs it on the tablet (USB, USB debugging on)
android: android-apk
	$(ADB) install -r $(APK)

# only builds the APK (lands in $(APK))
android-apk:
	cd android && ANDROID_HOME=$(ANDROID_HOME) ./gradlew assembleDebug
