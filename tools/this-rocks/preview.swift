import Foundation
import AppKit
import ImageIO
import UniformTypeIdentifiers

let root=URL(fileURLWithPath:FileManager.default.currentDirectoryPath)
let out=root.appendingPathComponent("builds/this-rocks-previews")
let entries=try JSONSerialization.jsonObject(with:Data(contentsOf:out.appendingPathComponent("render-input.json"))) as! [[String:Any]]
struct P {var x:Double;var y:Double;var z:Double}
func point(_ a:[Double])->P {P(x:a[0],y:a[1],z:a[2])}
func rotate(_ p:P,_ r:[String:Any]?)->P {
 guard let r=r else{return p}
 let o=r["origin"] as! [Double];let angle=(r["angle"] as! Double)*Double.pi/180
 var v=[p.x-o[0],p.y-o[1],p.z-o[2]]
 let axis=r["axis"] as! String;let ab=axis=="x" ? (1,2):axis=="y" ? (2,0):(0,1)
 let a=v[ab.0],b=v[ab.1],c=cos(angle),s=sin(angle)
 v[ab.0]=c*a-s*b;v[ab.1]=s*a+c*b
 if r["rescale"] as? Bool == true {v[ab.0]/=c;v[ab.1]/=c}
 return P(x:v[0]+o[0],y:v[1]+o[1],z:v[2]+o[2])
}
struct Face {var points:[P];var uv:[Double];var texture:String;var rotation:Int;var side:String}
var imageCache=[String:CGImage]()
func image(_ path:String)->CGImage {
 if let x=imageCache[path]{return x}
 let s=CGImageSourceCreateWithURL(URL(fileURLWithPath:path) as CFURL,nil)!
 var x=CGImageSourceCreateImageAtIndex(s,0,nil)!
 if x.height>x.width {x=x.cropping(to:CGRect(x:0,y:0,width:x.width,height:x.width))!}
 imageCache[path]=x;return x
}
func render(_ chosen:[[String:Any]],_ file:String,_ cols:Int) {
 let rows=(chosen.count+cols-1)/cols,w=cols*320,h=rows*230+80
 let ctx=CGContext(data:nil,width:w,height:h,bitsPerComponent:8,bytesPerRow:w*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
 ctx.setFillColor(CGColor(red:0.065,green:0.08,blue:0.085,alpha:1));ctx.fill(CGRect(x:0,y:0,width:w,height:h))
 NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=NSGraphicsContext(cgContext:ctx,flipped:false)
 func text(_ s:String,_ x:Double,_ y:Double,_ size:Double){
  let a:[NSAttributedString.Key:Any]=[.font:NSFont.systemFont(ofSize:size,weight:.medium),.foregroundColor:NSColor(calibratedWhite:0.91,alpha:1)]
  let t=s as NSString;let sz=t.size(withAttributes:a);t.draw(at:NSPoint(x:x-sz.width/2,y:y),withAttributes:a)
 }
 text("THIS ROCKS!  •  RESOURCE-PACK MODEL PREVIEW",Double(w)/2,Double(h)-36,20)
 for (i,entry) in chosen.enumerated(){
  let name=entry["name"] as! String,m=entry["model"] as! [String:Any],slots=m["textures"] as! [String:String]
  let cx=Double(i%cols*320+160),cy=Double(h-100-i/cols*230)
  func project(_ p:P)->CGPoint {CGPoint(x:cx+(p.x-p.z)*8,y:cy-35+p.y*9-(p.x+p.z-16)*4)}
  ctx.setFillColor(CGColor(red:0.12,green:0.15,blue:0.15,alpha:1));ctx.fill(CGRect(x:cx-148,y:cy-158,width:296,height:210))
  var fs=[Face]()
  for e in m["elements"] as! [[String:Any]] {
   let a=e["from"] as! [Double],b=e["to"] as! [Double],x=a[0],y=a[1],z=a[2],X=b[0],Y=b[1],Z=b[2]
   let corners:[String:[[Double]]]=[
    "up":[[x,Y,z],[x,Y,Z],[X,Y,Z],[X,Y,z]],"down":[[x,y,Z],[x,y,z],[X,y,z],[X,y,Z]],
    "north":[[X,y,z],[x,y,z],[x,Y,z],[X,Y,z]],"south":[[x,y,Z],[X,y,Z],[X,Y,Z],[x,Y,Z]],
    "west":[[x,y,z],[x,y,Z],[x,Y,Z],[x,Y,z]],"east":[[X,y,Z],[X,y,z],[X,Y,z],[X,Y,Z]]]
   for(side,f)in e["faces"] as! [String:[String:Any]]{
    var t=f["texture"] as! String
    while t.hasPrefix("#"){t=slots[String(t.dropFirst())]!}
    fs.append(Face(points:corners[side]!.map{rotate(point($0),e["rotation"] as? [String:Any])},uv:f["uv"] as? [Double] ?? [0,0,16,16],texture:t,rotation:f["rotation"] as? Int ?? 0,side:side))
   }
  }
  func depth(_ f:Face)->Double {var d=0.0;for p in f.points {d += p.x+p.z+2.0*p.y};return d}
  fs.sort{depth($0)<depth($1)}
  for f in fs {
   let p=f.points.map(project),a=p[0],b=p[1],c=p[2]
   if (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)<=0.00001 {continue}
   let uv=f.uv
   var ts=[CGPoint(x:uv[2],y:16-uv[3]),CGPoint(x:uv[0],y:16-uv[3]),CGPoint(x:uv[0],y:16-uv[1]),CGPoint(x:uv[2],y:16-uv[1])]
   let n=f.rotation/90;if n>0{ts=Array(ts[n...])+Array(ts[..<n])}
   let u=ts[0],v=ts[1],t=ts[2],dx=v.x-u.x,dy=v.y-u.y,ex=t.x-u.x,ey=t.y-u.y,det=dx*ey-ex*dy
   if abs(det)<0.00001{continue}
   let A=((b.x-a.x)*ey-(c.x-a.x)*dy)/det,B=((b.y-a.y)*ey-(c.y-a.y)*dy)/det
   let C=(dx*(c.x-a.x)-ex*(b.x-a.x))/det,D=(dx*(c.y-a.y)-ex*(b.y-a.y))/det
   let transform=CGAffineTransform(a:A,b:B,c:C,d:D,tx:a.x-A*u.x-C*u.y,ty:a.y-B*u.x-D*u.y)
   ctx.saveGState();ctx.beginPath();ctx.move(to:p[0]);for q in p.dropFirst(){ctx.addLine(to:q)};ctx.closePath();ctx.clip()
   ctx.concatenate(transform);ctx.interpolationQuality = .none
   ctx.draw(image(f.texture),in:CGRect(x:0,y:0,width:16,height:16));ctx.restoreGState()
   if f.side != "up" {ctx.saveGState();ctx.beginPath();ctx.move(to:p[0]);for q in p.dropFirst(){ctx.addLine(to:q)};ctx.closePath();ctx.setFillColor(CGColor(gray:0,alpha:f.side=="east" ? 0.17:0.30));ctx.fillPath();ctx.restoreGState()}
  }
  text(name.replacingOccurrences(of:"_",with:" "),cx,cy-140,14)
 }
 NSGraphicsContext.restoreGraphicsState()
 let dest=CGImageDestinationCreateWithURL(out.appendingPathComponent(file) as CFURL,UTType.png.identifier as CFString,1,nil)!
 CGImageDestinationAddImage(dest,ctx.makeImage()!,nil);CGImageDestinationFinalize(dest)
 print(file)
}
let overview=["rock_tiny","rock_small","rock_medium","rock_large","oak_stick_small","birch_stick_medium","spruce_stick_large","pinecone","seashell_white","seashell_pink","seashell_yellow","starfish_orange","starfish_pink","starfish_red","geyser_off","nether_geyser_off"]
render(overview.map{n in entries.first{$0["name"] as! String == n}!},"overview.png",4)
render(Array(entries[..<44]),"rocks.png",4)
render(Array(entries[44..<83]),"branches.png",3)
render(Array(entries[83...]),"coast-and-vents.png",4)
