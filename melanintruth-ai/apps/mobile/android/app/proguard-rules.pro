# Preserve runtime annotations and generic signatures used by Flutter plugins.
-keepattributes RuntimeVisibleAnnotations,RuntimeInvisibleAnnotations,Signature

# Keep Flutter plugin registrant classes discovered through generated metadata.
-keep class io.flutter.plugins.** { *; }
-dontwarn io.flutter.embedding.**
