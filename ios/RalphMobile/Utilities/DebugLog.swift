import Foundation

/// Debug logging utility that only prints in DEBUG builds
func debugLog(_ message: String, file: String = #file, line: Int = #line, function: String = #function) {
    #if DEBUG
    let fileName = (file as NSString).lastPathComponent
    print("[\(fileName):\(line)] \(function) - \(message)")
    #endif
}
