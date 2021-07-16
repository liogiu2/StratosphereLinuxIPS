# Must imports
from slips.common.abstracts import Module
import multiprocessing
from slips.core.database import __database__
import configparser
import platform

# Your imports
import sys, os, atexit

class Module(Module, multiprocessing.Process):
    name = 'daemon'
    description = 'This module runs when slips is in daemonized mode'
    authors = ['Alya Gomaa']

    def __init__(self, outputqueue, config):
        multiprocessing.Process.__init__(self)
        # All the printing output should be sent to the outputqueue.
        # The outputqueue is connected to another process called OutputProcess
        self.outputqueue = outputqueue
        # In case you need to read the slips.conf configuration file for
        # your own configurations
        self.config = config
        # Start the DB
        __database__.start(self.config)
        self.timeout = None
        self.read_configuration()

    def read_configuration(self):
        """ Read the configuration file for what we need """
        try:
            self.stdout = self.config.get('modes', 'stdin')
        except (configparser.NoOptionError, configparser.NoSectionError, NameError):
            # There is a conf, but there is no option, or no section or no configuration file specified
            self.stdout = '/dev/null' # todo should the default output file be dev null or a specific file in slips dir?

        try:
            self.stderr = self.config.get('modes', 'stderr')
        except (configparser.NoOptionError, configparser.NoSectionError, NameError):
            # There is a conf, but there is no option, or no section or no configuration file specified
            self.stderr = '/dev/null' # todo should the default stderr file be dev null or a specific file in slips dir?

        # create stderr if it doesn't exist
        if not os.path.exists(self.stdout):
            open(self.stderr,'w').close()

        # we don't use it anyway
        self.stdin='/dev/null'


    def print(self, text, verbose=1, debug=0):
        """
        Function to use to print text using the outputqueue of slips.
        Slips then decides how, when and where to print this text by
        taking all the prcocesses into account

        Input
         verbose: is the minimum verbosity level required for this text to
         be printed
         debug: is the minimum debugging level required for this text to be
         printed
         text: text to print. Can include format like 'Test {}'.format('here')

        If not specified, the minimum verbosity level required is 1, and the
        minimum debugging level is 0
        """

        vd_text = str(int(verbose) * 10 + int(debug))
        self.outputqueue.put(vd_text + '|' + self.name + '|[' + self.name + '] ' + str(text))

    def run(self):
        # Main loop function
        while True:
            try:
                print("**********all gooodd")
            except KeyboardInterrupt:
                # On KeyboardInterrupt, slips.py sends a stop_process msg to all modules, so continue to receive it
                continue
            except Exception as inst:
                self.print('Problem on the run()', 0, 1)
                self.print(str(type(inst)), 0, 1)
                self.print(str(inst.args), 0, 1)
                self.print(str(inst), 0, 1)
                return True

    def on_termination(self):
        pass

    def daemonize(self):
        """
        Does the Unix double-fork to create a daemon
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # os.chdir("/")
        # dissociate the daemon from its controlling terminal.
        # calling setsid means that this child will be the session leader of the new session
        os.setsid()
        os.umask(0)

        # If you want to prevent a process from acquiring a tty, the process shouldn't be the session leader
        # fork again so that the second child is no longer a session leader
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent (aka first child)
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # Now this code is run from the daemon
        # A daemon must close it's input and output file descriptors otherwise, it would still
        # be attached to the terminal it was started in.
        sys.stdout.flush()
        sys.stderr.flush()

        # redirect standard file descriptors
        with open(self.stdin, 'r') as stdin,\
            open(self.stdout, 'a+') as stdout,\
            open(self.stderr,'a+') as stderr:
            os.dup2(stdin.fileno(), sys.stdin.fileno())
            os.dup2(stdout.fileno(), sys.stdout.fileno())
            os.dup2(stderr.fileno(), sys.stderr.fileno())

        # Register a function to be executed if sys.exit() is called or the main module’s execution completes
        atexit.register(self.on_termination())
        pid = str(os.getpid())
        with open(self.pidfile,'w+') as pidfile:
            pidfile.write(pid+'\n')

