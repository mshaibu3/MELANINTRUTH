import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:image_picker/image_picker.dart';

const maxCaptureBytes = 10 * 1024 * 1024;

class CaptureException implements Exception {
  const CaptureException(this.message);

  final String message;

  @override
  String toString() => message;
}

class CapturedImage {
  CapturedImage({
    required this.bytes,
    required this.contentType,
    required this.fileName,
  }) : checksumSha256 = sha256.convert(bytes).toString();

  final Uint8List bytes;
  final String contentType;
  final String fileName;
  final String checksumSha256;

  int get sizeBytes => bytes.lengthInBytes;
}

abstract interface class CaptureSource {
  Future<CapturedImage> capture();
}

class ImagePickerCaptureSource implements CaptureSource {
  ImagePickerCaptureSource({ImagePicker? picker}) : _picker = picker ?? ImagePicker();

  final ImagePicker _picker;

  @override
  Future<CapturedImage> capture() async {
    final selected = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 100,
      requestFullMetadata: false,
    );
    if (selected == null) {
      throw const CaptureException(
        'Camera capture was cancelled or permission was not granted.',
      );
    }

    final bytes = await selected.readAsBytes();
    if (bytes.isEmpty) {
      throw const CaptureException('The camera returned an empty image.');
    }
    if (bytes.lengthInBytes > maxCaptureBytes) {
      throw const CaptureException(
        'The captured image exceeds the 10 MB secure-upload limit.',
      );
    }

    final contentType = _contentType(selected.name);
    return CapturedImage(
      bytes: bytes,
      contentType: contentType,
      fileName: selected.name,
    );
  }

  String _contentType(String name) {
    final lower = name.toLowerCase();
    if (lower.endsWith('.png')) {
      return 'image/png';
    }
    if (lower.endsWith('.jpg') || lower.endsWith('.jpeg')) {
      return 'image/jpeg';
    }
    throw const CaptureException(
      'Only JPEG and PNG camera captures are supported.',
    );
  }
}

class PreviewCaptureSource implements CaptureSource {
  const PreviewCaptureSource();

  @override
  Future<CapturedImage> capture() async {
    return CapturedImage(
      bytes: Uint8List.fromList(<int>[0xFF, 0xD8, 0xFF, 0xD9]),
      contentType: 'image/jpeg',
      fileName: 'preview.jpg',
    );
  }
}
