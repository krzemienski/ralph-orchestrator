import Foundation

/// Response from exporting the current configuration.
public struct ExportConfigResponse: Decodable {
    public let content: String
    public let filename: String

    public init(content: String, filename: String) {
        self.content = content
        self.filename = filename
    }
}

/// Request body for importing a configuration.
public struct ImportConfigRequest: Encodable {
    public let content: String

    public init(content: String) {
        self.content = content
    }
}

/// Response after importing a configuration.
public struct ImportConfigResponse: Decodable {
    public let status: String
    public let path: String

    public init(status: String, path: String) {
        self.status = status
        self.path = path
    }
}
