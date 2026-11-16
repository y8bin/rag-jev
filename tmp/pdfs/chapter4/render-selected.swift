import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

// args: output directory, then PDF-path:page pairs (one-based).
let out = CommandLine.arguments[1]
for spec in CommandLine.arguments.dropFirst(2) {
    let parts = spec.split(separator: ":")
    let path = String(parts[0])
    let number = Int(parts[1])!
    let pdf = CGPDFDocument(URL(fileURLWithPath: path) as CFURL)!
    let page = pdf.page(at: number)!
    let rect = page.getBoxRect(.mediaBox)
    let scale: CGFloat = 1.3
    let context = CGContext(data: nil, width: Int(rect.width * scale), height: Int(rect.height * scale), bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    context.setFillColor(CGColor(gray: 1, alpha: 1))
    context.fill(CGRect(x: 0, y: 0, width: rect.width * scale, height: rect.height * scale))
    context.scaleBy(x: scale, y: scale)
    context.drawPDFPage(page)
    let name = URL(fileURLWithPath: path).deletingPathExtension().lastPathComponent
    let url = URL(fileURLWithPath: out + "/" + name + "-p" + String(number) + ".png")
    let dest = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(dest, context.makeImage()!, nil)
    assert(CGImageDestinationFinalize(dest))
    print(url.path)
}
