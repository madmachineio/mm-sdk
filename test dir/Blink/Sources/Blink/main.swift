import SwiftIO

let blue = DigitalOut(Id.BLUE)

var count = 0

while true {
    blue.toggle()
    let value = hello(5, count)
    sleep(ms: value)
    count += 1
}