import Foundation
import Vision
import AppKit

func recognizeTextWithBoxes(from imagePath: String) {
    guard let image = NSImage(contentsOfFile: imagePath),
          let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        fputs("Error: Failed to load image at \(imagePath)\n", stderr)
        exit(1)
    }

    let requestHandler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    let request = VNRecognizeTextRequest { request, error in
        if let error = error {
            fputs("Vision error: \(error.localizedDescription)\n", stderr)
            return
        }
        guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
        for obs in observations {
            guard let top = obs.topCandidates(1).first else { continue }
            let b = obs.boundingBox
            // Format: x,y,w,h:::recognized_text
            // Note: Vision boundingBox coordinates are normalized [0.0, 1.0], origin at bottom-left
            print("\(b.origin.x),\(b.origin.y),\(b.size.width),\(b.size.height):::\(top.string)")
        }
    }
    request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]
    request.usesLanguageCorrection = true
    request.recognitionLevel = .accurate

    do {
        try requestHandler.perform([request])
    } catch {
        fputs("Request execution error: \(error.localizedDescription)\n", stderr)
        exit(1)
    }
}

if CommandLine.arguments.count > 1 {
    recognizeTextWithBoxes(from: CommandLine.arguments[1])
} else {
    fputs("Usage: ocr_boxes_bin <image_path>\n", stderr)
    exit(1)
}
