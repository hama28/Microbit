import time
from bluepy import btle

devadr     = "f4:b1:61:fe:06:bd"

uuid_service_led = "e95dd91d-251d-470a-a062-fa1922dfa9a8"
uuid_led_text    = "e95d93ee-251d-470a-a062-fa1922dfa9a8"


per = btle.Peripheral(devadr, btle.ADDR_TYPE_RANDOM)

svcLed = per.getServiceByUUID(uuid_service_led)
chLedText = svcLed.getCharacteristics(uuid_led_text)[0]
chLedText.write("Hello".encode("utf-8"))
time.sleep(5)

per.disconnect()