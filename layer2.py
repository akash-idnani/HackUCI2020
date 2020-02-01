from crc16 import crc16xmodem
#from layer1 import send_byte

def send_byte(a):
	pass

START_BYTE = 170
STOP_BYTE = 13
bytes_received = list()


def send_packet(data: bytes) -> bool:
	length = len(data)

	# Check that data is less than or equal to 256 bytes
	if (length > 256):
		return False

	# Start byte
	send_byte(START_BYTE)

	# Length
	send_byte(length)

	# Data
	for b in data:
		send_byte(b)

	# Checksum
	send_byte(crc16xmodem(data))

	# Stop byte
	send_byte(STOP_BYTE)

	return True


def get_all_start_bytes() -> list:
	return [i for i in range(len(bytes_received)) if bytes_received[i] == START_BYTE]


def check_if_packet(byte : bytes):
	global bytes_received
	bytes_received.append(byte)

	for start_index in get_all_start_bytes():
		length = 0
		try:
			length = bytes_received[start_index+1]
			print (bytes_received[start_index+length+4])
			if (bytes_received[start_index+length+4] != STOP_BYTE):
				continue

		except IndexError:
			print('Exception')
			continue

		# Packet slice
		packet = bytes_received[start_index : start_index+4+length]

		# Get data
		data = packet[2 : length+2]

		# Get checksum
		checksum = packet[length+2] << 8
		checksum = checksum | packet[length+3]

		# Compare computed checksum with receieved checksum
		if (crc16xmodem(data) == checksum):
			print(data) 
			bytes_received = list()


if __name__ == "__main__":
	data = str.encode('Hello', 'ascii')
	crc = crc16xmodem(data)
	crc_top = crc >> 8
	crc_bottom = crc & 0xFF

	packet = [START_BYTE, 5] + list(data) + [crc_top, crc_bottom, STOP_BYTE]
	print(packet)

	for b in packet:
		check_if_packet(b)

	data = str.encode('World!', 'ascii')
	crc = crc16xmodem(data)
	crc_top = crc >> 8
	crc_bottom = crc & 0xFF

	packet = [START_BYTE, 6] + list(data) + [crc_top, crc_bottom, STOP_BYTE]
	print(packet)

	for b in packet:
		check_if_packet(b)