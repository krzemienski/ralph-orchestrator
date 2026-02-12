import Foundation
import Security

/// Secure storage for API keys using the iOS Keychain.
/// Uses kSecClassGenericPassword with a fixed service identifier.
/// Keys persist across app reinstalls (standard Keychain behavior).
enum KeychainService {
    private static let service = "dev.ralph.RalphMobile"

    /// Save an API key for a given server URL.
    /// If a key already exists for this URL, it is overwritten.
    static func saveAPIKey(_ key: String, for serverURL: String) {
        guard !key.isEmpty else {
            deleteAPIKey(for: serverURL)
            return
        }

        let data = Data(key.utf8)
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: serverURL,
        ]

        // Delete existing item first (SecItemUpdate is fiddly)
        SecItemDelete(query as CFDictionary)

        var addQuery = query
        addQuery[kSecValueData as String] = data
        addQuery[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock

        let status = SecItemAdd(addQuery as CFDictionary, nil)
        if status != errSecSuccess {
            print("[KeychainService] Failed to save API key: \(status)")
        }
    }

    /// Load the API key for a given server URL.
    /// Returns nil if no key is stored.
    static func loadAPIKey(for serverURL: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: serverURL,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let key = String(data: data, encoding: .utf8) else {
            return nil
        }

        return key
    }

    /// Delete the stored API key for a given server URL.
    static func deleteAPIKey(for serverURL: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: serverURL,
        ]

        SecItemDelete(query as CFDictionary)
    }

    /// Check if an API key exists for a given server URL.
    static func hasAPIKey(for serverURL: String) -> Bool {
        loadAPIKey(for: serverURL) != nil
    }
}
