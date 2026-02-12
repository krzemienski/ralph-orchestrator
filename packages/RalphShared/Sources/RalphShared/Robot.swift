import Foundation

/// Response wrapper for the RObot questions endpoint.
public struct QuestionsResponse: Decodable {
    public let questions: [PendingQuestion]

    public init(questions: [PendingQuestion]) {
        self.questions = questions
    }
}

/// Represents a pending human-in-the-loop question from an agent.
/// Matches the JSON response from GET /api/robot/questions
public struct PendingQuestion: Decodable, Identifiable {
    public let id: String
    public let questionText: String
    public let sessionId: String
    public let askedAt: String
    public let timeoutAt: String
    public let iteration: UInt32
    public let hat: String?

    public enum CodingKeys: String, CodingKey {
        case id, iteration, hat
        case questionText = "question_text"
        case sessionId = "session_id"
        case askedAt = "asked_at"
        case timeoutAt = "timeout_at"
    }

    public init(
        id: String,
        questionText: String,
        sessionId: String,
        askedAt: String,
        timeoutAt: String,
        iteration: UInt32,
        hat: String?
    ) {
        self.id = id
        self.questionText = questionText
        self.sessionId = sessionId
        self.askedAt = askedAt
        self.timeoutAt = timeoutAt
        self.iteration = iteration
        self.hat = hat
    }
}

/// Request body for responding to a pending question.
public struct QuestionResponseRequest: Encodable {
    public let questionId: String
    public let responseText: String

    public enum CodingKeys: String, CodingKey {
        case questionId = "question_id"
        case responseText = "response_text"
    }

    public init(questionId: String, responseText: String) {
        self.questionId = questionId
        self.responseText = responseText
    }
}

/// Acknowledgement after submitting a question response.
public struct ResponseAck: Decodable {
    public let success: Bool
    public let questionId: String
    public let deliveredAt: String

    public enum CodingKeys: String, CodingKey {
        case success
        case questionId = "question_id"
        case deliveredAt = "delivered_at"
    }

    public init(success: Bool, questionId: String, deliveredAt: String) {
        self.success = success
        self.questionId = questionId
        self.deliveredAt = deliveredAt
    }
}

/// Request body for sending proactive guidance to a session.
public struct GuidanceRequest: Encodable {
    public let sessionId: String
    public let guidanceText: String

    public enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case guidanceText = "guidance_text"
    }

    public init(sessionId: String, guidanceText: String) {
        self.sessionId = sessionId
        self.guidanceText = guidanceText
    }
}

/// Acknowledgement after sending guidance.
public struct GuidanceAck: Decodable {
    public let success: Bool
    public let sessionId: String
    public let deliveredAt: String

    public enum CodingKeys: String, CodingKey {
        case success
        case sessionId = "session_id"
        case deliveredAt = "delivered_at"
    }

    public init(success: Bool, sessionId: String, deliveredAt: String) {
        self.success = success
        self.sessionId = sessionId
        self.deliveredAt = deliveredAt
    }
}
