import CoAP
import cbor2 as cbor
from scapy.all import *

coap = CoAP.Message()
coap.new_header(type=CoAP.CON, code=CoAP.GET)
coap.add_option (CoAP.Uri_path, "accelerometers")
coap.add_option (CoAP.Uri_path, "maximum")
coap.add_option (CoAP.Uri_query, "date=today")
coap.add_option (CoAP.Uri_query, "unit=m/s^2")
coap.add_option (CoAP.Accept, CoAP.Content_format_CBOR)
coap.add_option (CoAP.No_Response, 0b00000010) # block 2.xx notification
coap.add_option (CoAP.SCP82_Param, "TLV") 

coap.dump(hexa=True)

hexdump (coap.buffer)
