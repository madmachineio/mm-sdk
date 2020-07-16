import SwiftIO
import MadSHT3x

let blue = DigitalOut(Id.BLUE)
let red = DigitalOut(Id.RED)
let i2c = I2C(Id.I2C0)

let sht = MadSHT3x(i2c)

while true {
    blue.toggle()
    sleep(ms: 100)
}