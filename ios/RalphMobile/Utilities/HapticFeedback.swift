import UIKit

/// Centralized haptic feedback utility.
/// Provides type-safe haptic feedback for significant user actions.
enum HapticFeedback {
    /// Trigger impact feedback (light, medium, heavy).
    static func impact(_ style: UIImpactFeedbackGenerator.FeedbackStyle) {
        UIImpactFeedbackGenerator(style: style).impactOccurred()
    }

    /// Trigger notification feedback (success, warning, error).
    static func notification(_ type: UINotificationFeedbackGenerator.FeedbackType) {
        UINotificationFeedbackGenerator().notificationOccurred(type)
    }

    /// Trigger selection changed feedback.
    static func selection() {
        UISelectionFeedbackGenerator().selectionChanged()
    }
}
