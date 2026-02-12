import SwiftUI
import UIKit

/// Utility to export SwiftUI views as PNG images for app icons
@MainActor
class IconExporter {
    
    /// All required icon sizes for iOS app
    static let iconSizes: [(size: CGFloat, name: String)] = [
        // iPhone
        (1024, "Icon-1024"),           // App Store
        (180, "Icon-60@3x"),           // iPhone App @3x
        (120, "Icon-60@2x"),           // iPhone App @2x
        (120, "Icon-40@3x"),           // iPhone Spotlight @3x
        (80, "Icon-40@2x"),            // iPhone Spotlight @2x
        (87, "Icon-29@3x"),            // iPhone Settings @3x
        (58, "Icon-29@2x"),            // iPhone Settings @2x
        (60, "Icon-20@3x"),            // iPhone Notification @3x
        (40, "Icon-20@2x"),            // iPhone Notification @2x
        
        // iPad
        (167, "Icon-83.5@2x"),         // iPad Pro App @2x
        (152, "Icon-76@2x"),           // iPad App @2x
        (76, "Icon-76@1x"),            // iPad App @1x
        (80, "Icon-40@2x-1"),          // iPad Spotlight @2x
        (40, "Icon-40@1x"),            // iPad Spotlight @1x
        (58, "Icon-29@2x-1"),          // iPad Settings @2x
        (29, "Icon-29@1x"),            // iPad Settings @1x
        (40, "Icon-20@2x-1"),          // iPad Notification @2x
        (20, "Icon-20@1x")             // iPad Notification @1x
    ]
    
    /// Export app icon at specified size
    static func exportIcon(size: CGFloat, name: String) -> UIImage? {
        let view = AppIconGenerator(size: size)
        let controller = UIHostingController(rootView: view)
        controller.view.bounds = CGRect(origin: .zero, size: CGSize(width: size, height: size))
        controller.view.backgroundColor = .clear
        
        let renderer = UIGraphicsImageRenderer(size: CGSize(width: size, height: size))
        return renderer.image { context in
            controller.view.drawHierarchy(in: controller.view.bounds, afterScreenUpdates: true)
        }
    }
    
    /// Export all icon sizes to Documents directory
    static func exportAllIcons() -> [String: URL] {
        var exportedFiles: [String: URL] = [:]
        
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let iconsFolder = documentsPath.appendingPathComponent("AppIcons", isDirectory: true)
        
        // Create folder if needed
        try? FileManager.default.createDirectory(at: iconsFolder, withIntermediateDirectories: true)
        
        for (size, name) in iconSizes {
            if let image = exportIcon(size: size, name: name),
               let data = image.pngData() {
                let fileURL = iconsFolder.appendingPathComponent("\(name).png")
                try? data.write(to: fileURL)
                exportedFiles[name] = fileURL
                debugLog("[IconExporter] Exported \(name).png (\(Int(size))x\(Int(size)))")
            }
        }
        
        debugLog("[IconExporter] Exported \(exportedFiles.count) icons to: \(iconsFolder.path)")
        return exportedFiles
    }
    
    /// Generate Contents.json for AppIcon.appiconset
    static func generateContentsJSON() -> String {
        """
        {
          "images": [
            {
              "filename": "Icon-20@2x.png",
              "idiom": "iphone",
              "scale": "2x",
              "size": "20x20"
            },
            {
              "filename": "Icon-20@3x.png",
              "idiom": "iphone",
              "scale": "3x",
              "size": "20x20"
            },
            {
              "filename": "Icon-29@2x.png",
              "idiom": "iphone",
              "scale": "2x",
              "size": "29x29"
            },
            {
              "filename": "Icon-29@3x.png",
              "idiom": "iphone",
              "scale": "3x",
              "size": "29x29"
            },
            {
              "filename": "Icon-40@2x.png",
              "idiom": "iphone",
              "scale": "2x",
              "size": "40x40"
            },
            {
              "filename": "Icon-40@3x.png",
              "idiom": "iphone",
              "scale": "3x",
              "size": "40x40"
            },
            {
              "filename": "Icon-60@2x.png",
              "idiom": "iphone",
              "scale": "2x",
              "size": "60x60"
            },
            {
              "filename": "Icon-60@3x.png",
              "idiom": "iphone",
              "scale": "3x",
              "size": "60x60"
            },
            {
              "filename": "Icon-20@1x.png",
              "idiom": "ipad",
              "scale": "1x",
              "size": "20x20"
            },
            {
              "filename": "Icon-20@2x-1.png",
              "idiom": "ipad",
              "scale": "2x",
              "size": "20x20"
            },
            {
              "filename": "Icon-29@1x.png",
              "idiom": "ipad",
              "scale": "1x",
              "size": "29x29"
            },
            {
              "filename": "Icon-29@2x-1.png",
              "idiom": "ipad",
              "scale": "2x",
              "size": "29x29"
            },
            {
              "filename": "Icon-40@1x.png",
              "idiom": "ipad",
              "scale": "1x",
              "size": "40x40"
            },
            {
              "filename": "Icon-40@2x-1.png",
              "idiom": "ipad",
              "scale": "2x",
              "size": "40x40"
            },
            {
              "filename": "Icon-76@1x.png",
              "idiom": "ipad",
              "scale": "1x",
              "size": "76x76"
            },
            {
              "filename": "Icon-76@2x.png",
              "idiom": "ipad",
              "scale": "2x",
              "size": "76x76"
            },
            {
              "filename": "Icon-83.5@2x.png",
              "idiom": "ipad",
              "scale": "2x",
              "size": "83.5x83.5"
            },
            {
              "filename": "Icon-1024.png",
              "idiom": "ios-marketing",
              "scale": "1x",
              "size": "1024x1024"
            }
          ],
          "info": {
            "author": "xcode",
            "version": 1
          }
        }
        """
    }
}

#if DEBUG
/// Debug view to trigger icon export
struct IconExporterView: View {
    @State private var isExporting = false
    @State private var exportMessage = ""
    
    var body: some View {
        VStack(spacing: 30) {
            Text("App Icon Exporter")
                .font(.title)
                .foregroundColor(.white)
            
            if isExporting {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle(tint: CyberpunkTheme.accentCyan))
                Text("Exporting icons...")
                    .foregroundColor(CyberpunkTheme.textSecondary)
            } else {
                Button("Export All Icons") {
                    exportIcons()
                }
                .padding()
                .background(CyberpunkTheme.accentCyan)
                .foregroundColor(.black)
                .cornerRadius(8)
            }
            
            if !exportMessage.isEmpty {
                Text(exportMessage)
                    .font(.caption)
                    .foregroundColor(CyberpunkTheme.accentGreen)
                    .multilineTextAlignment(.center)
                    .padding()
            }
            
            // Preview
            AppIconGenerator(size: 180)
                .frame(width: 180, height: 180)
        }
        .padding()
        .background(CyberpunkTheme.bgPrimary)
    }
    
    private func exportIcons() {
        isExporting = true
        exportMessage = ""
        
        Task {
            let exported = IconExporter.exportAllIcons()
            
            await MainActor.run {
                isExporting = false
                exportMessage = "✓ Exported \(exported.count) icons\nCheck Files app → On My iPhone → AppIcons"
            }
        }
    }
}

#Preview {
    IconExporterView()
}
#endif
