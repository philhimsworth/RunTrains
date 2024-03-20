from Trains import database
#from Trains import sectionrelays

outer_section = 1
inner_section = 2
crossover_section = 3
slip_section = 4
station_section = 5


def resend_state(db):

    try:

        # Retrieve current section state as single value
        current_state = database.get_state(db, "sections")

        # Reapply
        sectionrelays.output_section_value(current_state)

    except Exception as e:
        print(e)


# Read the values from the submitted form and update the section state value.
def update_state(db, section_form):

    try:

        # Retrieve current state as single value
        current_state = database.get_state(db, "sections")

        new_state = current_state
        section_string = "section"
        for section_name in section_form:
            # section_name is of the form "section<x>"
            section_name_index = section_name.find(section_string)
            if section_name_index != -1:
                section_number_index = section_name_index + len(section_string)

                section_number = int(section_name[section_number_index])
                controller = int(section_form[section_name])

                if controller == 0:
                    new_state = turn_off_section(new_state, section_number)
                else:
                    new_state = turn_on_section(new_state, section_number, controller)

        new_state = set_slip_section_state_auto(new_state)
        new_state = set_section_polarities(new_state)

        if new_state != current_state:
            database.set_state(db, "sections", new_state)
            # Let the periodic update write to the relays
            #sectionrelays.output_section_value(new_state)

    except Exception as e:
        print(e)

def set_section(db, section_number, controller):

    try:

        # Retrieve current state as single value
        current_state = database.get_state(db, "sections")
        new_state = current_state
        
        if controller == 0:
            new_state = turn_off_section(new_state, section_number)
        else:
            new_state = turn_on_section(new_state, section_number, controller)

        new_state = set_slip_section_state_auto(new_state)
        new_state = set_section_polarities(new_state)

        if new_state != current_state:
            database.set_state(db, "sections", new_state)

    except Exception as e:
        print(e)
    

# Manual switch of station polarity
def manual_set_station_polarity(db, new_station_polarity):
    
    try:
                         
        # Retrieve current state as single value
        current_state = database.get_state(db, "sections")

        new_state = set_section_polarity(current_state, station_section, new_station_polarity)
         
        # if the state was updated, update the value in the database
        if new_state != current_state:
            database.set_state(db, "sections", new_state)

    except Exception as e:
        print(e)

# Get bit number for "section active" state
def get_section_on_bit(section):
    bit = -1
    if section == outer_section:     bit = 1
    if section == inner_section:     bit = 3
    if section == crossover_section: bit = 5
    if section == slip_section:      bit = 7
    if section == station_section:   bit = 9
    return bit


# Get bit number for "controller select" state
def get_section_controller_select_bit(section):
    bit = -1
    if section == outer_section:     bit = 0
    if section == inner_section:     bit = 2
    if section == crossover_section: bit = 4
    if section == slip_section:      bit = 6
    if section == station_section:   bit = 8
    return bit


# Get bit number for "polarity" state
def get_section_polarity_bit(section):
    bit = -1
    if section == slip_section:      bit = 10
    if section == station_section:   bit = 11
    return bit


# Determine if a controller is active for a given section
def is_controller_active(section_state, section, controller):
    
    if is_section_active(section_state, section):
        # section is active; is it this controller?
        bit = get_section_controller_select_bit(section)

        # is C2 active for this section?
        if (section_state & 1 << bit) != 0:
            # yes; is C2 the subject of this request?
            return controller == 2
        else:
            # no; is C1 the subject of this request?
            return controller == 1
    else:
        # section not active, so this controller is not active
        return False


# Determine if a section is active
def is_section_active(section_state, section):

    bit = get_section_on_bit(section)
    return (section_state & 1 << bit) != 0


def get_section_controller(section_state, section):
    if not is_section_active(section_state, section):
        # section off
        return 0
    else:
        if is_controller_active(section_state, section, 1):
            # section on and controlled by C1
            return 1
        else:
            # section on and controlled by C2
            return 2


# Determine if the polarity of a section has been switched.
def get_section_polarity(section_state, section):
    bit = get_section_polarity_bit(section)
    if bit != -1:
        return (section_state & 1 << bit) != 0
    else:
        # Section without a polarity switch control
        return False


def set_section_polarity(current_state, section, polarity):
    
    section_pol_bit = get_section_polarity_bit(section)

    # set or clear the polarity bit as requested
    if polarity == 1:
        new_state = current_state | (1 << section_pol_bit)
    else:
        new_state = current_state & ~(1 << section_pol_bit)

    return new_state
    

# Turn off a given section; disable and reset controller select state.
# This modifies a supplied "state" value and returns it with the changes applied.
def turn_off_section(current_state, section):

    print("Turning off ", section, sep='')

    # clear "on" bit for section
    bit = get_section_on_bit(section)
    new_state = current_state & ~(1 << bit)

    # if controller 2 is active for this section, turn it off
    cs_bit = get_section_controller_select_bit(section)
    new_state = new_state & ~(1 << cs_bit)

    return new_state


# Turn on a given section and select given controller
# This modifies a supplied "state" value and returns it with the changes applied.
def turn_on_section(current_state, section, controller):

    print("Turning on ", section, " to C", controller, sep='')

    # set controller select bit for section
    cs_bit = get_section_controller_select_bit(section)

    if controller == 1:
        # turn off cs bit for c1
        new_state = current_state & ~(1 << cs_bit)
    elif controller == 2:
        # turn on cs bit for c2
        new_state = current_state | (1 << cs_bit)

    # set "on" bit for section
    on_bit = get_section_on_bit(section)
    new_state = new_state | (1 << on_bit)

    return new_state


# Set the state of the slip section based on the sections
# assigned to each controller.
def set_slip_section_state_auto(current_state):
    
    # default to unassigned
    new_state = turn_off_section(current_state, slip_section)
    slip_section_controller = 0
    
    # if a controller has the station and inner sections, give it the slip as well
    station_section_controller = get_section_controller(new_state, station_section)
    if station_section_controller != 0:
        inner_section_controller = get_section_controller(new_state, inner_section)
        if station_section_controller == inner_section_controller:
            slip_section_controller = station_section_controller
            
    # if the slip isn't required to connect the inner and station,
    # group it with the outer
    if slip_section_controller == 0:
        outer_section_controller = get_section_controller(new_state, outer_section)
        if outer_section_controller != 0:
            slip_section_controller = outer_section_controller
            
    # if the slip is to be assigned to a controller, do it
    if slip_section_controller != 0:
        new_state = turn_on_section(new_state, slip_section, slip_section_controller)
    
    return new_state

    
# Set polarity of station and slip sections.
# If the slip section is assigned to a controller, 
# it will have reverse polarity if the inner loop is
# also assigned to that controller.
# The station polarity is set the same.
def set_section_polarities(current_state):

    slip_controller = get_section_controller(current_state, slip_section)
    station_controller = get_section_controller(current_state, station_section)
    inner_controller = get_section_controller(current_state, inner_section)
    outer_controller = get_section_controller(current_state, outer_section)

    pol_bit_slip = get_section_polarity_bit(slip_section)
    pol_bit_station = get_section_polarity_bit(station_section)

    new_state = current_state

    # invert slip if enabled and set to the same controller as the inner loop and station
    if slip_controller != 0 and slip_controller == inner_controller and slip_controller == station_controller :
        new_state = set_section_polarity(new_state, slip_section, 1)
    else:
        new_state = set_section_polarity(new_state, slip_section, 0)

    # invert station if enabled and set to the same controller as the outer loop
    if station_controller == outer_controller and station_controller != 0:
        new_state = set_section_polarity(new_state, station_section, 1)
    # set station to normal if enabled and set to the same controller as the inner loop    
    if station_controller == inner_controller and station_controller != 0:
        new_state = set_section_polarity(new_state, station_section, 0)

    return new_state


def all_off(db):
    
    database.set_state(db, "sections", 0)

    
# Move to next step in auto sequence.
# This depends on being able to identify the current step in the auto sequence
# from the current state.
#
# This function doesn't care if a required section is already in use; it assumes
# the UI will have either prevented or confirmed that.
#
# 1: All off; button reads "Start"
# 2: Station
# 3: Station + Inner
# 4: Inner only
# 5: Inner + crossover + outer
# 6: Outer only
# 7: Outer + station
# 8: Station only; button reads "Finish"
# Finish: all off

auto_unknown = -1
auto_0_off = 0
auto_1_station_outbound = 1
auto_2_station_inner = 2
auto_3_inner = 3
auto_4_inner_cx_outer = 4
auto_5_outer = 5
auto_6_outer_station = 6
auto_7_station_inbound = 7

def next_auto_sequence_step(db, this_controller):
    
    try:

        # Retrieve current state as single value
        current_state = database.get_state(db, "sections")

        current_auto_state = identify_auto_sequence_step(this_controller, current_state)
        
        print("Next auto sequence for C",this_controller," at step ",current_auto_state,sep='')
        
        if current_auto_state != auto_unknown:            
            new_state = set_next_auto_sequence_step(this_controller, current_state, current_auto_state)
            
            database.set_state(db, "sections", new_state)

    except Exception as e:
        print(e)
 
    return

# Look at the current section states and polarities to identify if the current state matches an auto state
def identify_auto_sequence_step(this_controller, current_state):
    
    station_controller = get_section_controller(current_state, station_section)
    inner_controller = get_section_controller(current_state, inner_section)
    cx_controller = get_section_controller(current_state, crossover_section)
    outer_controller = get_section_controller(current_state, outer_section)
    
    # Start
    if (station_controller == 0 and
    inner_controller != this_controller and
    cx_controller != this_controller and
    outer_controller != this_controller):
        return auto_0_off
        
    # Station outbound
    if (station_controller == this_controller and
        get_section_polarity(current_state, station_section) == 0 and
        inner_controller != this_controller and
        cx_controller != this_controller and
        outer_controller != this_controller):
        return auto_1_station_outbound
        
    # Station and inner
    if (station_controller == this_controller and
        inner_controller == this_controller and
        cx_controller != this_controller and
        outer_controller != this_controller):
        return auto_2_station_inner
        
    # Inner only
    if (inner_controller == this_controller and
    station_controller != this_controller and
    cx_controller != this_controller and
    outer_controller != this_controller):
        return auto_3_inner
        
    # Inner + crossover + outer
    if (inner_controller == this_controller and
    cx_controller == this_controller and
    outer_controller == this_controller and
    station_controller != this_controller):
        return auto_4_inner_cx_outer
            
    # Outer only
    if (outer_controller == this_controller and
    station_controller != this_controller and
    cx_controller != this_controller and
    inner_controller != this_controller):
        return auto_5_outer
        
    # Outer and station
    if (station_controller == this_controller and
    outer_controller == this_controller and
    cx_controller != this_controller and
    inner_controller != this_controller):
        return auto_6_outer_station
        
    # Station inbound
    if (station_controller == this_controller and
    get_section_polarity(current_state, station_section) == 1 and
    inner_controller != this_controller and
    cx_controller != this_controller and
    outer_controller != this_controller):
        return auto_7_station_inbound

    return auto_unknown


# Check if the sections required for the next auto state are free to use
def is_next_auto_sequence_step_available(this_controller, current_state, current_auto_state):
    
    # if unknown state then return value doesn't really matter
    if current_auto_state == -1:
        return False
    
    station_controller = get_section_controller(current_state, station_section)
    inner_controller = get_section_controller(current_state, inner_section)
    cx_controller = get_section_controller(current_state, crossover_section)
    outer_controller = get_section_controller(current_state, outer_section)

    if current_auto_state == auto_0_off:
        if station_controller != this_controller and station_controller != 0:
            return False
        
    if current_auto_state == auto_1_station_outbound:
        if inner_controller != this_controller and inner_controller != 0:
            return False
    
    # auto_2_station_inner to auto_3_inner just requires turning the station off, so
    # can always proceed.
     
    if current_auto_state == auto_3_inner:
        if ((cx_controller != this_controller and cx_controller != 0) or
        (outer_controller != this_controller and outer_controller != 0)):
            return False
    
    # auto_4_inner_cx_outer to auto_5_outer just requires turning inner + cx off, so 
    # can always proceed.
    
    if current_auto_state == auto_5_outer:
        if station_controller != this_controller and station_controller != 0:
            return False
 
    # Transitions that just involve turning sections off so can always proceed:
    #  auto_2_station_inner -> auto_3_inner
    #  auto_4_inner_cx_outer -> auto_5_outer
    #  auto_6_outer_station -> auto_7_station
    return True
    
# Set the section states to move to the next auto sequence state
def set_next_auto_sequence_step(this_controller, current_state, current_auto_state):
    
    new_state = current_state
    
    if current_auto_state == auto_0_off:
            # Currently off; set auto_1_station_start
            new_state = turn_on_section(new_state, station_section, this_controller)
            new_state = set_section_polarity(new_state, station_section, 0)
            
    if current_auto_state == auto_1_station_outbound:
            # Currently station start; set auto_2_station_inner
            new_state = turn_on_section(new_state, inner_section, this_controller)
            
    if current_auto_state == auto_2_station_inner:
            # Currently station+inner; set auto_3_inner
            new_state = turn_off_section(new_state, station_section)
            
    if current_auto_state == auto_3_inner:
            # Currently inner; set auto_4_inner_cx_outer
            new_state = turn_on_section(new_state, crossover_section, this_controller)
            new_state = turn_on_section(new_state, outer_section, this_controller)
            
    if current_auto_state == auto_4_inner_cx_outer:
            # Currently inner+cx+outer; set auto_5_outer
            new_state = turn_off_section(new_state, inner_section)
            new_state = turn_off_section(new_state, crossover_section)
            
    if current_auto_state == auto_5_outer:
            # Currently outer; set auto_6_outer_station
            new_state = turn_on_section(new_state, station_section, this_controller)
            
    if current_auto_state == auto_6_outer_station:
            # Currently outer+station; set auto_7_station_inbound
            new_state = turn_off_section(new_state, outer_section)
            
    if current_auto_state == auto_7_station_inbound:
            # Turn off station section and set its polarity ready for next outbound
            new_state = turn_off_section(new_state, station_section)
            new_state = set_section_polarity(new_state, station_section, 0)

    # Update slip section state and polarities as required
    new_state = set_slip_section_state_auto(new_state)
    new_state = set_section_polarities(new_state)

            
    return new_state
