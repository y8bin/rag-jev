import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
let pdf = CGPDFDocument(URL(fileURLWithPath: CommandLine.arguments[1]) as CFURL)!
for n in 1...pdf.numberOfPages {
 let page = pdf.page(at: n)!
 let rect = page.getBoxRect(.mediaBox)
 let scale: CGFloat = 2
 let context = CGContext(data: nil, width: Int(rect.width * scale), height: Int(rect.height * scale), bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
 context.setFillColor(CGColor(gray: 1, alpha: 1))
 context.fill(CGRect(x: 0, y: 0, width: rect.width * scale, height: rect.height * scale))
 context.scaleBy(x: scale, y: scale)
 context.drawPDFPage(page)
 let url = URL(fileURLWithPath: CommandLine.arguments[2] + "/page-" + String(n) + ".png")
 let dest = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil)!
 CGImageDestinationAddImage(dest, context.makeImage()!, nil)
 assert(CGImageDestinationFinalize(dest))
 print(url.path)
}
