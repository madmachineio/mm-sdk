import SwiftIO

let red = DigitalOut(Id.RED)

var count = 0

while true {
    red.toggle()
    let value = hello(5, count)
    sleep(ms: value)
    count += 1
}