// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "RalphShared",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .library(name: "RalphShared", targets: ["RalphShared"])
    ],
    targets: [
        .target(
            name: "RalphShared",
            dependencies: [],
            path: "Sources/RalphShared"
        ),
        .testTarget(
            name: "RalphSharedTests",
            dependencies: ["RalphShared"],
            path: "Tests/RalphSharedTests"
        )
    ]
)
