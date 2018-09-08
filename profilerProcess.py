import multiprocessing
import globaldata
import json
from datetime import datetime
from datetime import timedelta
import sys
from collections import OrderedDict
import configparser

# Profiler Process
class ProfilerProcess(multiprocessing.Process):
    """ A class to create the profiles for IPs and the rest of data """
    def __init__(self, inputqueue, outputqueue, config, width):
        multiprocessing.Process.__init__(self)
        self.inputqueue = inputqueue
        self.outputqueue = outputqueue
        self.config = config
        self.width = width
        self.columns_defined = False
        self.read_configuration()
        self.timeformat = ''
        # Read the configuration
        self.read_configuration()

    def read_configuration(self):
        """ Read the configuration file for what we need """
        # Get the time window width, if it was not specified as a parameter 
        if self.width == None:
            try:
                self.width = int(config.get('parameters', 'time_window_width'))
            except configparser.NoOptionError:
                self.width = 60
            except (configparser.NoOptionError, configparser.NoSectionError, NameError):
                # There is a conf, but there is no option, or no section or no configuration file specified
                pass
        # Limit any width to be > 0
        elif self.width < 0:
            self.width = 60

        # Get the format of the time in the flows
        try:
            self.timeformat = config.get('timestamp', 'format')
        except (configparser.NoOptionError, configparser.NoSectionError, NameError):
            # There is a conf, but there is no option, or no section or no configuration file specified
            self.timeformat = '%Y/%m/%d %H:%M:%S.%f'

    def process_columns(self, line):
        """
        Analyze the line and detect the format
        Valid formats are:
            - CSV, typically generated by the ra tool of Argus
                - In the case of CSV, recognize commas or TABS as field separators
            - JSON, typically generated by Suricata
        The function returns True when the colums are alredy defined, which means you can continue analyzing the data. A return of False means the columns were not defined, but we defined now.
        A return of -2 means an error
        """
        self.column_values = {}
        self.column_values['starttime'] = False
        self.column_values['endtime'] = False
        self.column_values['dur'] = False
        self.column_values['proto'] = False
        self.column_values['appproto'] = False
        self.column_values['saddr'] = False
        self.column_values['sport'] = False
        self.column_values['dir'] = False
        self.column_values['daddr'] = False
        self.column_values['dport'] = False
        self.column_values['state'] = False
        self.column_values['pkts'] = False
        self.column_values['spkts'] = False
        self.column_values['dpkts'] = False
        self.column_values['bytes'] = False
        self.column_values['sbytes'] = False
        self.column_values['dbytes'] = False

        # If the columns are already defined, just get the correct values fast using indexes. If not, find the columns
        if self.columns_defined:
            # Read the lines fast
            nline = line.strip().split(self.separator)
            try:
                self.column_values['starttime'] = datetime.strptime(nline[self.column_idx['starttime']], self.timeformat)
            except IndexError:
                pass
            try:
                self.column_values['endtime'] = nline[self.column_idx['endtime']]
            except IndexError:
                pass
            try:
                self.column_values['dur'] = nline[self.column_idx['dur']]
            except IndexError:
                pass
            try:
                self.column_values['proto'] = nline[self.column_idx['proto']]
            except IndexError:
                pass
            try:
                self.column_values['appproto'] = nline[self.column_idx['appproto']]
            except IndexError:
                pass
            try:
                self.column_values['saddr'] = nline[self.column_idx['saddr']]
            except IndexError:
                pass
            try:
                self.column_values['sport'] = nline[self.column_idx['sport']]
            except IndexError:
                pass
            try:
                self.column_values['dir'] = nline[self.column_idx['dir']]
            except IndexError:
                pass
            try:
                self.column_values['daddr'] = nline[self.column_idx['daddr']]
            except IndexError:
                pass
            try:
                self.column_values['dport'] = nline[self.column_idx['dport']]
            except IndexError:
                pass
            try:
                self.column_values['state'] = nline[self.column_idx['state']]
            except IndexError:
                pass
            try:
                self.column_values['pkts'] = nline[self.column_idx['pkts']]
            except IndexError:
                pass
            try:
                self.column_values['spkts'] = nline[self.column_idx['spkts']]
            except IndexError:
                pass
            try:
                self.column_values['dpkts'] = nline[self.column_idx['dpkts']]
            except IndexError:
                pass
            try:
                self.column_values['bytes'] = nline[self.column_idx['bytes']]
            except IndexError:
                pass
            try:
                self.column_values['sbytes'] = nline[self.column_idx['sbytes']]
            except IndexError:
                pass
            try:
                self.column_values['dbytes'] = nline[self.column_idx['dbytes']]
            except IndexError:
                pass
        else:
            # Find the type of lines, and the columns indexes
            # These are the indexes for later
            self.column_idx = {}
            self.column_idx['starttime'] = False
            self.column_idx['endtime'] = False
            self.column_idx['dur'] = False
            self.column_idx['proto'] = False
            self.column_idx['appproto'] = False
            self.column_idx['saddr'] = False
            self.column_idx['sport'] = False
            self.column_idx['dir'] = False
            self.column_idx['daddr'] = False
            self.column_idx['dport'] = False
            self.column_idx['state'] = False
            self.column_idx['pkts'] = False
            self.column_idx['spkts'] = False
            self.column_idx['dpkts'] = False
            self.column_idx['bytes'] = False
            self.column_idx['sbytes'] = False
            self.column_idx['dbytes'] = False

            try:
                # Heuristic detection: can we read it as json?
                try:
                    data = json.loads(line)
                    data_type = 'json'
                except ValueError:
                    data_type = 'csv'

                if data_type == 'json':
                    # Only get the suricata flows, not all!
                    if data['event_type'] != 'flow':
                        return -2
                    # JSON
                    self.column_values['starttime'] = datetime.strptime(data['flow']['start'].split('+')[0], '%Y-%m-%dT%H:%M:%S.%f') # We do not process timezones now
                    self.column_values['endtime'] = datetime.strptime(data['flow']['end'].split('+')[0], '%Y-%m-%dT%H:%M:%S.%f')  # We do not process timezones now
                    difference = self.column_values['endtime'] - self.column_values['starttime']
                    self.column_values['dur'] = difference.total_seconds()
                    self.column_values['proto'] = data['proto']
                    try:
                        self.column_values['appproto'] = data['app_proto']
                    except KeyError:
                        pass
                    self.column_values['saddr'] = data['src_ip']
                    try:
                        self.column_values['sport'] = data['src_port']
                    except KeyError:
                        # Some protocols like icmp dont have ports
                        self.column_values['sport'] = '0'
                    # leave dir as default
                    self.column_values['daddr'] = data['dest_ip']
                    try:
                        self.column_values['dport'] = data['dest_port']
                    except KeyError:
                        # Some protocols like icmp dont have ports
                        column_values['dport'] = '0'
                    self.column_values['state'] = data['flow']['state']
                    self.column_values['pkts'] = int(data['flow']['pkts_toserver']) + int(data['flow']['pkts_toclient'])
                    self.column_values['spkts'] = int(data['flow']['pkts_toserver'])
                    self.column_values['dpkts'] = int(data['flow']['pkts_toclient'])
                    self.column_values['bytes'] = int(data['flow']['bytes_toserver']) + int(data['flow']['bytes_toclient'])
                    self.column_values['sbytes'] = int(data['flow']['bytes_toserver'])
                    self.column_values['dbytes'] = int(data['flow']['bytes_toclient'])
                elif data_type == 'csv':
                    # Are we using commas or tabs?. Just count them and choose as separator the char with more counts
                    nr_commas = len(line.split(','))
                    nr_tabs = len(line.split('	'))
                    if nr_commas > nr_tabs:
                        # Commas is the separator
                        self.separator = ','
                    elif nr_tabs > nr_commas:
                        # Tabs is the separator
                        self.separator = '	'
                    else:
                        outputqueue.put('0|profiler|Error. The file is not comma or tab separated.')
                        return -2
                    nline = line.strip().split(self.separator)
                    for field in nline:
                        if 'time' in field.lower():
                            self.column_idx['starttime'] = nline.index(field)
                        elif 'dur' in field.lower():
                            self.column_idx['dur'] = nline.index(field)
                        elif 'proto' in field.lower():
                            self.column_idx['proto'] = nline.index(field)
                        elif 'srca' in field.lower():
                            self.column_idx['saddr'] = nline.index(field)
                        elif 'sport' in field.lower():
                            self.column_idx['sport'] = nline.index(field)
                        elif 'dir' in field.lower():
                            self.column_idx['dir'] = nline.index(field)
                        elif 'dsta' in field.lower():
                            self.column_idx['daddr'] = nline.index(field)
                        elif 'dport' in field.lower():
                            self.column_idx['dport'] = nline.index(field)
                        elif 'state' in field.lower():
                            self.column_idx['state'] = nline.index(field)
                        elif 'totpkts' in field.lower():
                            self.column_idx['pkts'] = nline.index(field)
                        elif 'totbytes' in field.lower():
                            self.column_idx['bytes'] = nline.index(field)
                self.columns_defined = True
            except Exception as inst:
                self.outputqueue.put('0|profiler|Problem in process_columns() in profilerProcess')
                self.outputqueue.put('0|profiler|' + str(type(inst)))
                self.outputqueue.put('0|profiler|' + str(inst.args))
                self.outputqueue.put('0|profiler|' + str(inst))
                sys.exit(1)
            # This is the return when the columns were not defined. False
            return False
        # This is the return when the columns were defined. True
        return True

    def get_profile(self, saddr):
        """ See if we have an ip profile for this ip. If not, create it. Store it in the global variables """
        try:
            ipprofile = globaldata.ip_profiles[saddr]
            # We got it
            return ipprofile
        except KeyError:
            ipprofile = IPProfile(self.outputqueue, saddr, self.width, self.timeformat)
            globaldata.ip_profiles[saddr] = ipprofile
            return ipprofile

    def run(self):
        try:
            while True:
                # While the input communication queue is empty
                if self.inputqueue.empty():
                    # Wait to get something
                    pass
                else:
                    # The input communication queue is not empty
                    line = self.inputqueue.get()
                    if 'stop' == line:
                        self.outputqueue.put('0|profiler|Stopping Profiler Process')
                        return True
                    elif line:
                        # Received new data
                        # Extract the columns smartly
                        # self.outputqueue.put('New line: {}'.format(line))
                        if self.process_columns(line):
                            # See if we have this IP profile yet, and if not create it
                            ip_profile = self.get_profile(self.column_values['saddr'])
                            # Add the flow to the profile
                            ip_profile.add_flow(self.column_values)
                            self.outputqueue.put('3|profiler|' + ip_profile.describe())
        except KeyboardInterrupt:
            return True
        except Exception as inst:
            self.outputqueue.put('0|profiler|Problem with Profiler Process()')
            self.outputqueue.put('0|profiler|' + str(type(inst)))
            self.outputqueue.put('0|profiler|' + str(inst.args))
            self.outputqueue.put('0|profiler|' + str(inst))
            sys.exit(1)


class IPProfile(object):
    """ A Class for managing the complete profile of an IP. Including the TimeWindows""" 
    def __init__(self, outputqueue, ip, width, timeformat):
        self.ip = ip
        self.width = width
        self.outputqueue = outputqueue
        self.timeformat = timeformat
        # Some features belong to the IP as a whole. Some features belong to an individual time window. 
        # Also the time windows can be of any length, including 'infinite' which means one time window in the complete capture.
        self.dst_ips = OrderedDict()
        self.dst_nets = OrderedDict()
        self.time_windows = OrderedDict()
        # Debug data
        self.outputqueue.put('1|profiler|A new Profile was created for the IP {}, with time window width {}'.format(self.ip, self.width))

    def add_flow(self, columns):
        """  
        This should be the first, and probably only, function to be called in this object
        Receive the columns of a flow and manage all the data and insertions 
        """
        # Extract the features that belong to the IP profile
        # Extract the features that belong to the current TW
        tw = self.get_timewindow(columns['starttime'])
        tw.add_flow(columns)
        # Add the destination IP to this IP profile
        self.dst_ips[columns['daddr']] = ''

    def get_timewindow(self, flowtime):
        """" 
        This function should get or create the time windows need, accordingly to the current time of the flow
        Returns the time window object
        """
        self.outputqueue.put('2|profiler|\n##########################')
        self.outputqueue.put('2|profiler|Current time of the flow: {}'.format(flowtime))
        # First check of we are not in the last TW
        try:
            lasttw = self.time_windows[list(self.time_windows.keys())[-1]]
            # We have the last TW
            self.outputqueue.put('3|profiler|Found last TW. TW starttime: {}, end {}'.format(lasttw.get_starttime(), lasttw.get_endtime()))
            if lasttw.get_endtime() >= flowtime and lasttw.get_starttime() < flowtime:
                self.outputqueue.put('3|profiler|The flow is on the last time windows')
                return lasttw
            elif flowtime > lasttw.get_endtime():
                # Then check if we dont' need a NEW tw in the future
                # Create as many TW as we need until we reach the time of the current flow. Each tw should start where the last on ended
                tw = TimeWindows(self.outputqueue, lasttw.get_endtime(), self.width)
                self.outputqueue.put('3|profiler|Next TW created. TW starttime: {}, end {}'.format(tw.get_starttime(), tw.get_endtime()))
                while tw.get_endtime() < flowtime:
                    # The flow is still more in the future, create another TW
                    self.outputqueue.put('3|profiler|The new TW didn\'t reach the time of the current flow. Creating another TW')
                    self.time_windows[tw.get_endtime()] = tw
                    lasttw = tw
                    tw = TimeWindows(self.outputqueue, lasttw.get_endtime(), self.width)
                    self.outputqueue.put('3|profiler|Next TW created. TW starttime: {}, end {}'.format(tw.get_starttime(), tw.get_endtime()))
                # We are supposed to be in the TW corresponding to the current flow
                self.time_windows[tw.get_endtime()] = tw
                return tw
            elif flowtime < lasttw.get_starttime():
                # This flow came out of order. Its before the start of the last TW. Search for the correct TW and add it there. This is SLOW
                list_tw_time = list(self.time_windows.keys())
                list_tw_time.reverse()
                for tw_time in list_tw_time:
                    if flowtime >= self.time_windows[tw_time].get_starttime():
                        # We found the past TW where this flow belongs
                        tw = self.time_windows[tw_time]
                        return tw
                    # Continue looking in the for...
                # Out of the for
                # We couldn't find the TW in the past because the flow was the first in time and before the first TW, so we need to create a new TWs until we find its place
                # tw_time holds the endtime of the first TW
                start_of_first_tw = tw_time - timedelta(seconds=self.width*60)
                start_of_new_tw_in_past = start_of_first_tw - timedelta(seconds=self.width*60)
                tw = TimeWindows(self.outputqueue, start_of_new_tw_in_past, self.width)
                self.outputqueue.put('3|profiler|Past TW created. TW starttime: {}, end {}'.format(tw.get_starttime(), tw.get_endtime()))
                self.time_windows[tw.get_endtime()] = tw
                while flowtime < tw.get_starttime():
                    lasttw = tw
                    # If still our flow in more in the past, continue creatting TW for it
                    tw = TimeWindows(self.outputqueue, lasttw.get_starttime() - timedelta(seconds=self.width*60), self.width)
                    self.outputqueue.put('3|profiler|Past TW created. TW starttime: {}, end {}'.format(tw.get_starttime(), tw.get_endtime()))
                    self.time_windows[tw.get_endtime()] = tw
                return tw
        except IndexError:
            # There are no TW yet. Create the first 
            self.outputqueue.put('3|profiler|\n-> There was no first TW. Creating one')
            tw = TimeWindows(self.outputqueue, flowtime, self.width)
            self.time_windows[tw.get_endtime()] = tw
            self.outputqueue.put('3|profiler|First TW created. TW starttime: {}, end {}'.format(tw.get_starttime(), tw.get_endtime()))
            return tw


    def describe(self):
        """ Print a description of the profile """
        text =  ''
        text += 'Profile of IP {}\n'.format(self.ip)
        text += '---------------\n'
        text += 'Dst IPs:\n'
        for dip in self.dst_ips:
            text += '	{}\n'.format(dip)
        text += '\n'
        text += 'Time Windows in this Profile:\n'
        for tw in self.time_windows:
            text += '{}\n'.format(self.time_windows[tw].describe())
        return text


class TimeWindows(object):
    """ A Class for managing the complete time window""" 
    def __init__(self, outputqueue, starttime, width):
        # The time windows can be of any length, including 'infinite' which means one time window in the complete capture.
        self.width = width
        self.outputqueue = outputqueue
        self.starttime = starttime
        self.endtime = self.starttime + timedelta(seconds=self.width*60)
        self.dst_ips = OrderedDict()
        self.dst_ports = []
        self.dst_nets = OrderedDict()

    def add_flow(self, columns):
        """  
        Receive the columns of a flow and manage all the data and insertions 
        """
        # Add the destination IP to this IP profile
        self.dst_ips[columns['daddr']] = ''
        self.dst_ports.append(columns['dport'])

    def get_starttime(self):
        """ Return the start time of the time window """
        return self.starttime 

    def get_endtime(self):
        """ Return the start time of the time window """
        return self.endtime

    def describe(self):
        """ Print a description of the profile """
        text =  ''
        text += '\tTime Windows start: {} (ends: {})\n'.format(self.starttime, self.endtime)
        text += '\tDst IPs:\n'
        for dip in self.dst_ips:
            text += '\t\t{}\n'.format(dip)
        text += '\tDst Ports: '
        for port in self.dst_ports:
            text += '{},'.format(port)
        return text
