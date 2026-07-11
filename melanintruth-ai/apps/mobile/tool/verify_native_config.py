from __future__ import annotations

import plistlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def verify_android() -> None:
    manifest = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text()
    require("android.permission.CAMERA" in manifest, "Android CAMERA permission is missing.")
    require("android.permission.INTERNET" in manifest, "Android INTERNET permission is missing.")
    require('android:usesCleartextTraffic="false"' in manifest, "Android cleartext traffic must be disabled.")
    require('android:allowBackup="false"' in manifest, "Android application backup must be disabled.")
    require('android:label="MelaninTruth"' in manifest, "Android application label is incorrect.")

    gradle = (ROOT / "android/app/build.gradle.kts").read_text()
    require('applicationId = "com.hakilixlabs.melanintruth"' in gradle, "Android application ID is incorrect.")
    require('namespace = "com.hakilixlabs.melanintruth"' in gradle, "Android namespace is incorrect.")
    require("minSdk = 23" in gradle, "Android minSdk must be 23 or higher.")
    require('signingConfigs.getByName("debug")' not in gradle, "Android release must never use debug signing.")
    require("isMinifyEnabled = true" in gradle, "Android release code shrinking must be enabled.")
    require("isShrinkResources = true" in gradle, "Android release resource shrinking must be enabled.")

    activity = ROOT / "android/app/src/main/kotlin/com/hakilixlabs/melanintruth/MainActivity.kt"
    require(activity.exists(), "Android MainActivity does not match the release namespace.")


def verify_ios() -> None:
    info_path = ROOT / "ios/Runner/Info.plist"
    with info_path.open("rb") as handle:
        info = plistlib.load(handle)

    require(info.get("CFBundleDisplayName") == "MelaninTruth", "iOS display name is incorrect.")
    require(bool(info.get("NSCameraUsageDescription")), "iOS camera usage description is missing.")
    ats = info.get("NSAppTransportSecurity", {})
    require(ats.get("NSAllowsArbitraryLoads") is False, "iOS arbitrary network loads must be disabled.")
    require(info.get("ITSAppUsesNonExemptEncryption") is False, "iOS export-compliance declaration is missing.")

    project = (ROOT / "ios/Runner.xcodeproj/project.pbxproj").read_text()
    require("com.hakilixlabs.melanintruth" in project, "iOS bundle identifier is incorrect.")
    targets = [float(value) for value in re.findall(r"IPHONEOS_DEPLOYMENT_TARGET = ([0-9.]+);", project)]
    require(targets and min(targets) >= 13.0, "iOS deployment target must be 13.0 or higher.")


def verify_release_gateway() -> None:
    main = (ROOT / "lib/main.dart").read_text()
    environment = (ROOT / "lib/src/environment.dart").read_text()
    require("MobileEnvironment.fromCompileTime" in main, "Mobile entry point must use validated environment configuration.")
    require("releaseMode" in environment, "Release environment validation is missing.")
    require("Release builds require an HTTPS" in environment, "Release HTTPS enforcement is missing.")


def verify_native_workflow() -> None:
    workflow = (ROOT.parents[2] / ".github/workflows/mobile-native-ci.yml").read_text()
    require(
        "ANDROID_AVD_HOME: ${{ github.workspace }}/.android/avd" in workflow,
        "Android AVD home must be explicit and use an allowed job context.",
    )
    require('--path "$AVD_PATH"' in workflow, "Android AVD creation must use an explicit path.")
    require('test -f "$AVD_CONFIG"' in workflow, "Android AVD configuration must be verified.")
    require(
        'if [ "${{ steps.boot.outcome }}" = "success" ]; then' in workflow,
        "ADB diagnostics must only run after a successful emulator boot.",
    )
    require(
        "group: mobile-native-ci-${{ github.ref }}" in workflow,
        "Native CI must cancel stale runs for the same PR or branch.",
    )


def main() -> None:
    verify_android()
    verify_ios()
    verify_release_gateway()
    verify_native_workflow()
    print("Native release configuration verified.")


if __name__ == "__main__":
    main()
