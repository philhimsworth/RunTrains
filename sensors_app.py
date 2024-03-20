import serial

from Trains import database
from Trains import sections

def main():

	# Open database connection
	db = database.db_connect("trains.db")

	ser = serial.Serial('/dev/ttyACM0', timeout=1)

	while True:
	
		try:
			line = ser.readline()
			if (b'\n' in line):
				line2 = line.decode()
				try:
					print("Rx:",line2)
				except Exception as e:
					print("Rx: (unprintable)")
				
				colon_pos = line2.find(":")
				if colon_pos != -1:
					sensor_num = int(line2[colon_pos+1:])
					SensorTriggered(db, sensor_num)
		except Exception as e:
			print("Loop exception:", e)
            

def SensorTriggered(db, sensor_num):

	try:
		
		# Retrieve current mainline section state as single value
		current_section_state = database.get_state(db, "sections")
		new_section_state = current_section_state
		
		# If sensor 1 is triggered when a route is set from the station to the inner track, turn off the station section
		# to reset the route over the slip.
		if sensor_num == 1:
			if (sections.is_section_active(current_section_state, sections.inner_section) and
				sections.get_section_controller(current_section_state, sections.inner_section) == sections.get_section_controller(current_section_state, sections.station_section)):
				print('Triggered:', sensor_num)
				new_section_state = sections.turn_off_section(current_section_state, sections.station_section)

		# If sensor 1 is triggered when the canal siding is set, unset it
		if sensor_num == 1:
			canal_siding_state = database.get_state(db, "canal_siding")
			if canal_siding_state == 1:
				database.set_state(db, "canal_siding", 0)
				database.commit(db)
 

			
		# If sensor 2 is triggered when a route is set from inner -> cx -> outer, turn off the cx section (and the inner if it
		# is on the same controller; leave it if it has already been changed)
		if sensor_num == 2:
			if (sections.is_section_active(current_section_state, sections.outer_section) and
				sections.get_section_controller(current_section_state, sections.crossover_section) == sections.get_section_controller(current_section_state, sections.outer_section)):
				new_section_state = sections.turn_off_section(current_section_state, sections.crossover_section)
				# turn off inner as well if on same controller
				if sections.get_section_controller(current_section_state, sections.inner_section) == sections.get_section_controller(current_section_state, sections.outer_section):
					new_section_state = sections.turn_off_section(new_section_state, sections.inner_section)


		# if any changes have been made, update automatically set states
		if new_section_state != current_section_state:
			new_section_state = sections.set_slip_section_state_auto(new_section_state)
			new_section_state = sections.set_section_polarities(new_section_state)

			print("Updating section: ", current_section_state," -> ", new_section_state)
			
			database.set_state(db, "sections", new_section_state)
			database.commit(db)

	except Exception as e:
		print("SensorTriggered exception: sensor_num:", sensor_num, "ex: ", e)
	
	

if __name__ == '__main__':

    main()


