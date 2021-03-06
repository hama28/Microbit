from scene import *
import cb
import struct
import time

UUID_SERVICE_LED   = 'E95DD91D-251D-470A-A062-FA1922DFA9A8'
UUID_LED_TEXT      = 'E95D93EE-251D-470A-A062-FA1922DFA9A8'
UUID_SERVICE_IOPIN = 'E95D127B-251D-470A-A062-FA1922DFA9A8'
UUID_PIN_IO_CONF   = 'E95DB9FE-251D-470A-A062-FA1922DFA9A8'
UUID_PIN_AD_CONF   = 'E95D5899-251D-470A-A062-FA1922DFA9A8'
UUID_PIN_DATA      = 'E95D8D00-251D-470A-A062-FA1922DFA9A8'

delegate     = None
label_status = None
is_connected = False

class Folo_Control (Scene):
	def setup(self):
		global label_status
		global is_connected
		
		self.background_color = '#e0e0e0'
		
		label_status = LabelNode('Status', position=(180,600), parent=self, color='black')
		
		self.follow_button = SpriteNode('iob:arrow_up_a_256', position=(185,450))
		self.add_child(self.follow_button)
		
		self.back_button   = SpriteNode('iob:arrow_down_a_256', position=(185,110))
		self.add_child(self.back_button)
		
		self.right_button  = SpriteNode('iob:arrow_return_right_256', position=(285,300))
		self.add_child(self.right_button)
		
		self.left_button   = SpriteNode('iob:arrow_return_left_256', position=(90,300))
		self.add_child(self.left_button)
		
		self.connect_button = SpriteNode('iob:bluetooth_32', position=(50,600))
		self.add_child(self.connect_button)
		
		self.current_button = None
		self.current_button_name = ''
		
		is_connected = False
						
	def touch_began(self, touch):
		global label_status
		global is_connected
		
		touch_loc = self.point_from_scene(touch.location)
		if is_connected and touch_loc in self.follow_button.frame:
			# move forward
			self.current_button = self.follow_button
			self.current_button_name = 'follow'
			label_status.text = 'follow'
			delegate.send_action(1, 0)
			
		elif is_connected and touch_loc in self.back_button.frame:
			# move back
			self.current_button = self.back_button
			self.current_button_name = 'back'
			label_status.text = 'back'
			delegate.send_action(-1, 0)
			
		elif is_connected and touch_loc in self.right_button.frame:
			# turn right
			self.current_button = self.right_button
			self.current_button_name = 'right'
			label_status.text = 'right'
			delegate.send_action(0, 1)
			
		elif is_connected and touch_loc in self.left_button.frame:
			# turn left
			self.current_button = self.left_button
			self.current_button_name = 'left'
			label_status.text = 'left'
			delegate.send_action(0, -1)
		
		elif touch_loc in self.connect_button.frame:
			self.current_button = self.connect_button
			self.current_button_name = 'connect'
			label_status.text = 'connect'

	def touch_ended(self, touch):
		global label_status
		global delegate
		global is_connected
		
		touch_loc = self.point_from_scene(touch.location)
		if self.current_button == self.connect_button and touch_loc in self.connect_button.frame:
			if is_connected :
				# disconnection
				delegate.send_action(0, 0)
				cb.reset()
				is_connected = False
				delegate = None
				label_status.text = 'disconnected'
			else :
				# start conenction
				label_status.text = 'Scanning ...'
				delegate = MyCentralManagerDelegate()
				cb.set_central_delegate(delegate)
				cb.scan_for_peripherals()
		
		else :
			if is_connected :
				# release button
				delegate.send_action(0, 0)
				label_status.text == ''
				
class MyCentralManagerDelegate (object):
	def __init__(self):
		self.peripheral = None
		self.chara_io   = None

	def did_discover_peripheral(self, p):
		global label_status

		if p.name and 'BBC micro:bit' in p.name and not self.peripheral:
			self.peripheral = p
			cb.connect_peripheral(self.peripheral)
			label_status.text = 'micro:bitを見つけました'

		if not self.peripheral :
			label_status.text = 'micro:bitが見つかりません'
			cb.reset()

	def did_connect_peripheral(self, p):
		p.discover_services()

	def did_fail_to_connect_peripheral(self, p, error):
		global label_status
		global is_connected
		is_connected = False
		label_status.text = 'Failed to connect'

	def did_disconnect_peripheral(self, p, error):
		global label_status
		global is_connected
		is_connected = False
		print('Disconnected, error: %s' % (error,))
		label_status.text = 'Disconnected'
		self.peripheral = None
		self.chara_io   = None

	def did_discover_services(self, p, error):
		for s in p.services:
			if UUID_SERVICE_IOPIN in s.uuid:
				p.discover_characteristics(s)

	def did_discover_characteristics(self, s, error):
		global label_status
		global is_connected
		
		set_ad_conf = False
		set_io_conf = False
		set_ch_io   = False
				
		if UUID_SERVICE_IOPIN in s.uuid:
			for c in s.characteristics:
				if UUID_PIN_IO_CONF in c.uuid:
					#print('PIN IO characteristics... set output mode  to all port')
					self.peripheral.write_characteristic_value(c, b'\x00\x00\x00\x00', True)
					set_io_conf = True

				elif UUID_PIN_AD_CONF in c.uuid:
					#print('PIN AD characteristics... set analog mode to port13-16')
					self.peripheral.write_characteristic_value(c, b'\x00\xe0\x01\x00', True)
					set_ad_conf = True
				
				elif UUID_PIN_DATA in c.uuid:
					#get characteristic
					self.chara_io = c
					set_ch_io = True

		if set_ad_conf and set_io_conf and set_ch_io:
			is_connected = True
			label_status.text = 'connected'
			#turn left
			#print('PIN AD characteristics... set \xff to port16')
			#self.peripheral.write_characteristic_value(c, b'\x10\xff', True)

	def did_write_value(self, c, error):
		#print('output to IO')
		pass
		
	def send_action(self, move, turn):
		if self.peripheral and self.chara_io:
			#print('move = %d turn = %d' %(move, turn))
			if move == 0 and turn == 0 :
				self.peripheral.write_characteristic_value(self.chara_io, b'\x0d\x00', True)
				self.peripheral.write_characteristic_value(self.chara_io, b'\x0e\x00', True)
				self.peripheral.write_characteristic_value(self.chara_io, b'\x0f\x00', True)
				self.peripheral.write_characteristic_value(self.chara_io, b'\x10\x00', True)
				
				label_status.text = ''
				
			elif move > 0 :
				# move forward
				self.peripheral.write_characteristic_value(self.chara_io, b'\x0e\x00', True)
				self.peripheral.write_characteristic_value(self.chara_io, b'\x0d\xff', True)
				
			elif move < 0 :
				# move back
				self.peripheral.write_characteristic_value(self.chara_io, b'\x0d\x00', True)
				self.peripheral.write_characteristic_value(self.chara_io, b'\x0e\xff', True)
				
			elif turn > 0 :
				# turn right
				self.peripheral.write_characteristic_value(self.chara_io, b'\x0f\x00', True)
				self.peripheral.write_characteristic_value(self.chara_io, b'\x10\xff', True)
				
			elif turn < 0 :
				# turn left
				self.peripheral.write_characteristic_value(self.chara_io, b'\x10\x00', True)
				self.peripheral.write_characteristic_value(self.chara_io, b'\x0f\xff', True)

if __name__ == '__main__':
	run(Folo_Control(), PORTRAIT, show_fps=True)