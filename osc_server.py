from liblo import *
import sys
import time
from collections import deque
import math
import urllib2

DEBUG = True
POLITICALLY_CORRECT = True
EXAMPLE_REQUESTS = False

IP = '10.69.177.59'

ACC_DEQUE_LEN = 220
# ACC_X_THRESHOLD = 440  # math.sqrt(2)
ACC_Z_THRESHOLD = 220  # math.sqrt(2)
MIN_ZEROS = 4

MIN_CLENCHES_INHIBIT_BLINK = 4

MIN_BLINK = 0.05
MAX_BLINK = 0.5

MIN_CLENCHES = 12

MIN_DISCONNECT_TIME = 5

# acc_x_deque = deque([0] * ACC_DEQUE_LEN, ACC_DEQUE_LEN)
acc_z_deque = deque([0] * ACC_DEQUE_LEN, ACC_DEQUE_LEN)

last_blink = 0
last_no_blink = 0

clench_count = 0
clench_acked = False

disconnect_time = 0
disconnect_acked = False

is_last_connection_good = False
is_connection_dubious = True

if DEBUG:
    f = open('jackrabbit', 'w')
    e = open('jerkrabbit', 'w')

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def is_sinusoidal(acc_deque, acc_threshold):
    acc_max = max(acc_deque)
    acc_min = min(acc_deque)
    acc_avg = (acc_max+acc_min) / 2
    # acc_range = acc_max - acc_min
    acc_pos_min = acc_avg + acc_threshold  # (acc_max-acc_avg)/ACC_THRESHOLD
    acc_neg_max = acc_avg - acc_threshold  # (acc_avg-acc_min)/ACC_THRESHOLD
    zeros = []
    signs = []
    for i in xrange(ACC_DEQUE_LEN - 1):
        if acc_deque[i] < acc_avg < acc_deque[i + 1]:
            zeros.append(i)
            signs.append(-1)
        elif acc_deque[i] > acc_avg > acc_deque[i + 1]:
            zeros.append(i)
            signs.append(1)
    if len(zeros) < MIN_ZEROS:
        return False
    for i in xrange(len(zeros) - 1):
        if signs[i + 1] == 1 and max(list(acc_deque)[zeros[i]:zeros[i + 1]]) > acc_pos_min:
            continue
        if signs[i + 1] == -1 and min(list(acc_deque)[zeros[i]:zeros[i + 1]]) < acc_neg_max:
            continue
        return False
    return True

class MuseServer(ServerThread):
    #listen for messages on port 5001
    def __init__(self):
        ServerThread.__init__(self, 5000)

    #receive accelrometer data
    @make_method('/muse/acc', 'fff')
    def acc_callback(self, path, args):
        global acc_x_deque
        global acc_z_deque
        acc_x, acc_y, acc_z = args
        # print "%s %f %f %f" % (path, acc_x, acc_y, acc_z)
        # acc_x_deque.popleft()
        # acc_x_deque.append(acc_x)
        # acc_x_is_sinusoidal = is_sinusoidal(acc_x_deque, ACC_X_THRESHOLD)
        # if acc_x_is_sinusoidal:
        #     print 'jajaja'
        #     print 'up n down motherfuckers'
        #     print 'yayayaya'
        acc_z_deque.popleft()
        acc_z_deque.append(acc_z)
        if is_sinusoidal(acc_z_deque, ACC_Z_THRESHOLD):
            print bcolors.OKBLUE + 'HEAD_SHAKE' + bcolors.ENDC
            if DEBUG and not POLITICALLY_CORRECT:
                print 'xaxaxa'
                print 'shake it side to side!'
                print 'kekeke'
            if DEBUG:
                if EXAMPLE_REQUESTS:
                    print urllib2.urlopen("http://www.example.com/").read().splitlines()[0]
                else:
                    print urllib2.urlopen("http://" + IP + ":8080/mindcontrol/nav").read()
            else:
                if EXAMPLE_REQUESTS:
                    urllib2.urlopen('http://www.example.com/')
                else:
                    urllib2.urlopen('http://' + IP + ':8080/mindcontrol/nav')
            # acc_x_deque = deque([0] * ACC_DEQUE_LEN, ACC_DEQUE_LEN)
            acc_z_deque = deque([0] * ACC_DEQUE_LEN, ACC_DEQUE_LEN)
            time.sleep(1)

    #receive EEG data
    @make_method('/muse/eeg', 'ffff')
    def eeg_callback(self, path, args):
        l_ear, l_forehead, r_forehead, r_ear = args
        print "%s %f %f %f %f" % (path, l_ear, l_forehead, r_forehead, r_ear)

    @make_method('/muse/elements/blink', 'i')
    def blink_callback(self, path, args):
        global clench_count
        global last_blink
        global last_no_blink
        if clench_count > MIN_CLENCHES_INHIBIT_BLINK or not is_last_connection_good:
            return
        now = time.time()
        if DEBUG:
            e.write('{}\n'.format(args[0]))
            e.flush()
        if args[0] == 1:
            if MIN_BLINK < now - last_blink < MAX_BLINK and last_blink < last_no_blink < now:
                print bcolors.OKBLUE + 'BLINK' + bcolors.ENDC
                if DEBUG:
                    if POLITICALLY_CORRECT:
                        print 'last_blink:', last_blink
                        print 'last_no_blink:', last_no_blink
                        print 'now:', now
                    else:
                        print "this dude fucking blinked"
                        print "first boom:", last_blink
                        print "the quiet:", last_no_blink
                        print "boom boom bitches", now
                if DEBUG:
                    if EXAMPLE_REQUESTS:
                        print urllib2.urlopen("http://www.example.com/").read().splitlines()[0]
                    else:
                        print urllib2.urlopen("http://" + IP + ":8080/mindcontrol/next").read()
                else:
                    if EXAMPLE_REQUESTS:
                        urllib2.urlopen('http://www.example.com/')
                    else:
                        urllib2.urlopen('http://' + IP + ':8080/mindcontrol/next')
                time.sleep(1)
            else: 
                last_blink = now
        else:
            last_no_blink = now

    @make_method('/muse/elements/jaw_clench', 'i')
    def jaw_clench_callback(self, path, args):
        global clench_count
        global clench_acked
        if DEBUG:
            f.write('{}\n'.format(args[0]))
            f.flush()
        if disconnect_time or is_connection_dubious:
            return
        if args[0] == 1:
            clench_count += 1
            if clench_count > MIN_CLENCHES and not clench_acked:
                print bcolors.OKBLUE + 'JAW_CLENCH' + bcolors.ENDC
                if DEBUG and not POLITICALLY_CORRECT:
                    print "this dude fucking clenched"
                clench_acked = True
                if DEBUG:
                    if EXAMPLE_REQUESTS:
                        print urllib2.urlopen("http://www.example.com/").read().splitlines()[0]
                    else:
                        print urllib2.urlopen("http://" + IP + ":8080/mindcontrol/comedy").read()
                else:
                    if EXAMPLE_REQUESTS:
                        urllib2.urlopen('http://www.example.com/')
                    else:
                        urllib2.urlopen('http://' + IP + ':8080/mindcontrol/comedy')
                time.sleep(1)
        else:
            clench_count = 0
            clench_acked = False

    @make_method('/muse/elements/touching_forehead', 'i')
    def touching_forehead_callback(self, path, args):
        global disconnect_time
        global disconnect_acked
        if args[0] == 0:
            if not disconnect_time:
                disconnect_time = time.time()
            if time.time() - disconnect_time > MIN_DISCONNECT_TIME and not disconnect_acked:
                print bcolors.WARNING + 'DISCONNECT' + bcolors.ENDC
                if DEBUG:
                    if POLITICALLY_CORRECT:
                        print 'disconnected after', time.time() - disconnect_time, 'seconds'
                    else:
                        print "This bitch ditches you after", time.time() - disconnect_time, "seconds you didn't touch her"
                disconnect_acked = True
                if DEBUG:
                    if EXAMPLE_REQUESTS:
                        print urllib2.urlopen("http://www.example.com/").read().splitlines()[0]
                    else:
                        print urllib2.urlopen("http://" + IP + ":8080/mindcontrol/close").read()
                else:
                    if EXAMPLE_REQUESTS:
                        urllib2.urlopen('http://www.example.com/')
                    else:
                        urllib2.urlopen('http://' + IP + ':8080/mindcontrol/close')
        else:
            disconnect_time = 0
            disconnect_acked = False

    @make_method('/muse/elements/is_good','iiii')
    def is_good(self, path, args):
        global is_last_connection_good
        global is_connection_dubious
        is_current_connection_good = all(args)
        if is_current_connection_good != is_last_connection_good:
            if is_current_connection_good:
                print bcolors.OKGREEN + 'device reconnected' + bcolors.ENDC
                if DEBUG and not POLITICALLY_CORRECT:
                    print "con fucking gratys"
                is_connection_dubious = False
            else:
                print bcolors.FAIL + 'device disconnected' + bcolors.ENDC
                if DEBUG and not POLITICALLY_CORRECT:
                    print "Wear your fucking device well bro"
                if sum(args) <= 1:
                    is_connection_dubious = True
        is_last_connection_good = is_current_connection_good

  #   #handle unexpected messages
  #   @make_method(None, None)
  #   def fallback(self, path, args, types, src):
  #       print "Unknown message \
		# \n\t Source: '%s' \
		# \n\t Address: '%s' \
		# \n\t Types: '%s ' \
		# \n\t Payload: '%s'" \
		# % (src.url, path, types, args)

try:
    server = MuseServer()
except ServerError, err:
    print str(err)
    sys.exit()

server.start()

if __name__ == "__main__":
    while 1:
        time.sleep(1)
