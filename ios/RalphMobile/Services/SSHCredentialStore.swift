import Foundation
import Security

/// SSH credentials for connecting to a remote host.
struct SSHCredentials: Codable, Equatable {
    let host: String
    let port: Int
    let username: String
    let password: String
    let serverPort: Int

    /// Convenience: default SSH port
    static let defaultSSHPort = 22
    /// Convenience: default ralph-mobile-server port
    static let defaultServerPort = 8080
}

/// Secure storage for SSH credentials using the iOS Keychain.
/// Follows the same pattern as KeychainService but stores SSHCredentials
/// keyed by hostname. Uses kSecAttrAccessibleWhenUnlockedThisDeviceOnly
/// for stronger security (credentials don't sync to other devices or backups).
enum SSHCredentialStore {
    private static let service = "dev.ralph.RalphMobile.ssh"

    /// Save SSH credentials for a given hostname.
    /// Overwrites any existing credentials for this host.
    static func save(_ credentials: SSHCredentials) {
        guard let data = try? JSONEncoder().encode(credentials) else {
            print("[SSHCredentialStore] Failed to encode credentials")
            return
        }

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: credentials.host,
        ]

        // Delete existing entry first (upsert pattern)
        SecItemDelete(query as CFDictionary)

        var addQuery = query
        addQuery[kSecValueData as String] = data
        addQuery[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly

        let status = SecItemAdd(addQuery as CFDictionary, nil)
        if status != errSecSuccess {
            print("[SSHCredentialStore] Failed to save credentials: \(status)")
        }
    }

    /// Load SSH credentials for a given hostname.
    /// Returns nil if no credentials are stored.
    static func load(for host: String) -> SSHCredentials? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: host,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let credentials = try? JSONDecoder().decode(SSHCredentials.self, from: data) else {
            return nil
        }

        return credentials
    }

    /// Load the most recently saved credentials (any host).
    /// Useful for auto-filling the credential form on return visits.
    static func loadMostRecent() -> SSHCredentials? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let credentials = try? JSONDecoder().decode(SSHCredentials.self, from: data) else {
            return nil
        }

        return credentials
    }

    /// Delete stored credentials for a given hostname.
    static func delete(for host: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: host,
        ]

        SecItemDelete(query as CFDictionary)
    }

    /// Check if credentials exist for a given hostname.
    static func exists(for host: String) -> Bool {
        load(for: host) != nil
    }
}
