import Foundation
import Vision

struct OCRBox: Codable {
    let text: String
    let confidence: Float
    let x: Double
    let y: Double
    let width: Double
    let height: Double
}

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write(Data("usage: apple_vision_ocr <image-path>\n".utf8))
    exit(2)
}

let imageURL = URL(fileURLWithPath: CommandLine.arguments[1])
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.minimumTextHeight = 0.006

do {
    let handler = VNImageRequestHandler(url: imageURL, options: [:])
    try handler.perform([request])
    let boxes: [OCRBox] = (request.results ?? []).compactMap { observation in
        guard let candidate = observation.topCandidates(1).first else { return nil }
        let bounds = observation.boundingBox
        return OCRBox(
            text: candidate.string,
            confidence: candidate.confidence,
            x: bounds.origin.x,
            y: bounds.origin.y,
            width: bounds.size.width,
            height: bounds.size.height
        )
    }
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.sortedKeys]
    FileHandle.standardOutput.write(try encoder.encode(boxes))
    FileHandle.standardOutput.write(Data("\n".utf8))
} catch {
    FileHandle.standardError.write(Data("Apple Vision OCR failed: \(error)\n".utf8))
    exit(1)
}
