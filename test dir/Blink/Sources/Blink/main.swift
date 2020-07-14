import SwiftIO

let blue = DigitalOut(Id.BLUE)
let red = DigitalOut(Id.RED)


while true {
    blue.toggle()
    sleep(ms: 100)
}