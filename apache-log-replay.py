"""Replay requests from an HTTP access log file.
"""

import sys
import time
import urllib2
from datetime import datetime
from optparse import OptionParser

# Constants that specify access log format (indices
# specify position after splitting on spaces)
HOST_INDEX = 0
TIME_INDEX = 3
PATH_INDEX = 6

def main(filename, proxy, speedup=1):
    """Setup and start replaying."""    
    requests = _parse_logfile(filename)
    _setup_http_client(proxy)
    _replay(requests, speedup)

def _replay(requests, speedup):
    """Replay the requests passed as argument"""
    replay_start = datetime.now()
    log_start = requests[0][0]
    total_delta = requests[-1][0] - log_start
    print "%d requests to go (time: %s)" % (len(requests), total_delta)        
    for request_time, host, path in requests:
        _delay_request(request_time, log_start, replay_start, speedup)
        url = "http://" + host + path
        req_result = "OK"
        try:
            urllib2.urlopen(url)
        except Exception:
            req_result = "FAILED"
        print ("[%s] %s -- %s"
            % (request_time.strftime("%H:%M:%S"), req_result, url))

def _delay_request(request_time, log_start, replay_start, speedup):
    log_delta = request_time - log_start        
    replay_delta = (datetime.now() - replay_start) * speedup
    if replay_delta < log_delta:
        wait_delta = log_delta - replay_delta
        if wait_delta.seconds > 3:
            print "(next request in %d seconds)" % wait_delta.seconds
        time.sleep(wait_delta.seconds)        
        
def _setup_http_client(proxy):
    """Configure proxy server and install HTTP opener"""
    proxy_config = {'http': proxy} if proxy else {}
    proxy_handler = urllib2.ProxyHandler(proxy_config)
    opener = urllib2.build_opener(proxy_handler)
    urllib2.install_opener(opener)

def _parse_logfile(filename):
    """Parse the logfile and return a list with tuples of the form
    (<request time>, <requested host>, <requested url>)
    """
    logfile = open(filename, "r")
    requests = []
    for line in logfile:
        parts = line.split(" ")
        time_text = parts[TIME_INDEX][1:]
        request_time = datetime.strptime(time_text, "%d/%b/%Y:%H:%M:%S")
        host = parts[HOST_INDEX]
        path = parts[PATH_INDEX]
        requests.append((request_time, host, path))
    if not requests:
        print "Seems like I don't know how to parse this file!"
    return requests
        
if __name__ == "__main__":
    """Parse command line options."""
    usage = "usage: %prog [options] logfile"
    parser = OptionParser(usage)
    parser.add_option('-p', '--proxy',
        help='send requests to server PROXY',
        dest='proxy',
        default=None)
    parser.add_option('-s', '--speedup',
        help='make time run faster by factor SPEEDUP',
        dest='speedup',
        type='int',
        default=1)
    (options, args) = parser.parse_args()
    if len(args) == 1:
        main(args[0], options.proxy, options.speedup)
    else:
        parser.error("incorrect number of arguments")
        