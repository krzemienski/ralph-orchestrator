import Foundation
import RalphShared

// MARK: - TemplateStore

/// Manages persistence of custom prompt templates using UserDefaults.
@MainActor
final class TemplateStore: ObservableObject {
    private let userDefaultsKey = "customPromptTemplates"

    @Published private(set) var customTemplates: [PromptTemplate] = []

    init() {
        loadCustomTemplates()
    }

    /// All templates: bundled + custom.
    var allTemplates: [PromptTemplate] {
        PromptTemplate.bundled + customTemplates
    }

    /// Load custom templates from UserDefaults.
    func loadCustomTemplates() {
        guard let data = UserDefaults.standard.data(forKey: userDefaultsKey) else {
            customTemplates = []
            return
        }
        do {
            customTemplates = try JSONDecoder().decode([PromptTemplate].self, from: data)
        } catch {
            #if DEBUG
            print("Failed to decode custom templates: \(error)")
            #endif
            customTemplates = []
        }
    }

    /// Save a new custom template or update an existing one.
    func saveCustom(_ template: PromptTemplate) {
        var templateToSave = template
        templateToSave.isBundled = false // Ensure custom templates are never bundled

        if let index = customTemplates.firstIndex(where: { $0.id == template.id }) {
            // Update existing
            templateToSave.updatedAt = Date()
            customTemplates[index] = templateToSave
        } else {
            // Add new
            customTemplates.append(templateToSave)
        }
        persistToUserDefaults()
    }

    /// Delete a custom template by ID. Bundled templates cannot be deleted.
    func deleteCustom(id: UUID) {
        // Check if it's a bundled template
        if PromptTemplate.bundled.contains(where: { $0.id == id }) {
            return // Cannot delete bundled templates
        }
        customTemplates.removeAll { $0.id == id }
        persistToUserDefaults()
    }

    /// Create a new custom template with initial values.
    func createCustomTemplate(name: String, content: String, description: String) -> PromptTemplate {
        let now = Date()
        let template = PromptTemplate(
            id: UUID(),
            name: name,
            content: content,
            description: description,
            isBundled: false,
            createdAt: now,
            updatedAt: now
        )
        saveCustom(template)
        return template
    }

    private func persistToUserDefaults() {
        do {
            let data = try JSONEncoder().encode(customTemplates)
            UserDefaults.standard.set(data, forKey: userDefaultsKey)
        } catch {
            #if DEBUG
            print("Failed to encode custom templates: \(error)")
            #endif
        }
    }
}
