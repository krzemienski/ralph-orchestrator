import Foundation

/// Shared formatters to prevent recreation on every render.
/// Creating formatters is expensive - use these static instances.
public enum Formatters {
    // MARK: - Date Formatters

    /// Time formatter: "HH:mm:ss"
    public static let timeFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "HH:mm:ss"
        return f
    }()

    /// Time formatter with milliseconds: "HH:mm:ss.SSS"
    public static let timeWithMillisFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "HH:mm:ss.SSS"
        return f
    }()

    /// Medium time style formatter
    public static let mediumTimeFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateStyle = .none
        f.timeStyle = .medium
        return f
    }()

    /// ISO8601 formatter with fractional seconds
    public static let iso8601Formatter: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()

    /// ISO8601 formatter without fractional seconds (fallback)
    public static let iso8601FormatterNoFractional: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()

    // MARK: - Number Formatters

    /// Number formatter with thousands separator
    public static let numberFormatter: NumberFormatter = {
        let f = NumberFormatter()
        f.numberStyle = .decimal
        f.groupingSeparator = ","
        return f
    }()

    /// Currency formatter (USD)
    public static let currencyFormatter: NumberFormatter = {
        let f = NumberFormatter()
        f.numberStyle = .currency
        f.currencyCode = "USD"
        return f
    }()

    /// Currency formatter with 4 decimal places (for small values)
    public static let precisionCurrencyFormatter: NumberFormatter = {
        let f = NumberFormatter()
        f.numberStyle = .currency
        f.currencyCode = "USD"
        f.maximumFractionDigits = 4
        return f
    }()
}
