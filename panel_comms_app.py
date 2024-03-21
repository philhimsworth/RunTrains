import serial_asyncio
import asyncio

from Trains import database
from Trains import sections

async def main():

	# Open database connection
	db = database.db_connect("trains.db")

	ser_reader, ser_writer = await serial_asyncio.open_serial_connection(url='/dev/ttyACM1')
 
	#await asyncio.gather(   sender_function(db, ser_writer))
    
	await asyncio.gather(   sender_function(db, ser_writer),
                            reader_function(db, ser_reader))

	#await asyncio.gather(   reader_function(db, ser_reader))
    

async def sender_function(db, ser):

	current_section_state = -1

	while True:
	
		try:
			
			new_section_state = database.get_state(db, "sections")
							
			# auto route current step
			auto_step_c1 = sections.identify_auto_sequence_step(1, new_section_state)
			auto_step_c2 = sections.identify_auto_sequence_step(2, new_section_state)
				
			auto_next_step_ok_c1 = 1 if sections.is_next_auto_sequence_step_available(1, new_section_state, auto_step_c1) else 0
			auto_next_step_ok_c2 = 1 if sections.is_next_auto_sequence_step_available(2, new_section_state, auto_step_c2) else 0
			
			station_active = 1 if sections.is_section_active(new_section_state, sections.station_section) else 0
			
			msg = f'{auto_step_c1},{auto_next_step_ok_c1},{auto_step_c2},{auto_next_step_ok_c2},{station_active}\n'
			ser.write(msg.encode('utf-8'))
			print(f'send: {msg}')
			
			current_section_state = new_section_state

			await asyncio.sleep(1)
			
		except Exception as e:
			print("Sender exception:", e)
			
async def reader_function(db, ser):
	
	while True:

		try:				
			line = await ser.readline()
			if (b'\n' in line):
				line2 = line.decode()
				try:
					print("Rx:",line2)
				except Exception as e:
					print("Rx: (unprintable)")
				
				if (line2.find("C1") != -1 or line2.find("C2") != -1):
					
					section_state = database.get_state(db, "sections")
				
					if (line2.find("C1") != -1):
						auto_step_c1 = sections.identify_auto_sequence_step(1, section_state)
						if sections.is_next_auto_sequence_step_available(1, section_state, auto_step_c1):
							print("C1")
							sections.next_auto_sequence_step(db, 1)
							database.commit(db)
						else:
							print("C1 is not ready")

					if (line2.find("C2") != -1):
						auto_step_c2 = sections.identify_auto_sequence_step(2, section_state)
						if sections.is_next_auto_sequence_step_available(2, section_state, auto_step_c2):
							print("C2")
							sections.next_auto_sequence_step(db, 2)
							database.commit(db)
						else:
							print("C2 is not ready")

		except Exception as e:
			print(f'reader_function exception: {e}')
            


if __name__ == '__main__':

	asyncio.run(main())


