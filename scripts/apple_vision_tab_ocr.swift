import Foundation
import Vision

struct TabOCRInput: Codable {
    let label: String
    let path: String
}

struct TabOCRManifest: Codable {
    let inputs: [TabOCRInput]
}

struct TabOCRResult: Codable {
    let token: String?
    let confidence: Float
    let uncertain: Bool
}

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write(Data("usage: apple_vision_tab_ocr <manifest-json>\n".utf8))
    exit(2)
}

do {
    let manifestURL = URL(fileURLWithPath: CommandLine.arguments[1])
    let manifest = try JSONDecoder().decode(TabOCRManifest.self, from: Data(contentsOf: manifestURL))
    var results: [String: TabOCRResult] = [:]
    let customWords = (0...36).flatMap { fret in
        let number = String(fret)
        return [number] + Array("ABCDEFG").map { number + String($0) }
    }
    for input in manifest.inputs {
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = false
        request.minimumTextHeight = 0.006
        request.customWords = customWords
        let handler = VNImageRequestHandler(url: URL(fileURLWithPath: input.path), options: [:])
        try handler.perform([request])
        let observations = (request.results ?? []).sorted {
            if abs($0.boundingBox.midY - $1.boundingBox.midY) > 0.15 {
                return $0.boundingBox.midY > $1.boundingBox.midY
            }
            return $0.boundingBox.minX < $1.boundingBox.minX
        }
        let candidates = observations.compactMap { $0.topCandidates(1).first }
        let token = candidates.map(\.string).joined().replacingOccurrences(of: " ", with: "")
        let confidence = candidates.map(\.confidence).min() ?? 0
        results[input.label] = TabOCRResult(
            token: token.isEmpty ? nil : token,
            confidence: confidence,
            uncertain: token.isEmpty || confidence < 0.5
        )
    }
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.sortedKeys]
    FileHandle.standardOutput.write(try encoder.encode(results))
    FileHandle.standardOutput.write(Data("\n".utf8))
} catch {
    FileHandle.standardError.write(Data("Apple Vision tab OCR failed: \(error)\n".utf8))
    exit(1)
}
