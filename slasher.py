"""
A directory bruteforce tool. Requires Python 3
 - k-ddev

Planned functionalities for future:
    scanning optimizations, maybe hotkeys to control flow,
    maybe scraping for subpage URIs, session pause/save/resume,
    maybe others...
"""

import sys
import socket
import getopt
import grequests

# usage
def usage():
    print("Usage: slasher.py <host> <dictionary>")
    print("  options:")
    print("  -c --conc <num>        :: manually select number of concurrent requests. Defaults to 15")
    print("  -h --help              :: display usage (what you're seeing now)")
    print("  -t --tree              :: view site map as tree once scan is done (not yet implemented)")
    print("  -o --out <path>        :: print site tree to outfile (not yet implemented)")
    print("  -q --quiet             :: don't echo page URLs when a page is found")
    sys.exit(0)

def main():
    # globals
    global concurrent # how many concurrent requests to make at once
    global host       # target website
    global dictionary # loaded words
    global quiet      # shh

    # collect options and arguments
    try:
        options, a = getopt.getopt(sys.argv[1:], "c:hto:q", ["conc=", "help", "tree", "out=", "quiet"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    # now handle them.
    man_args = a # program takes mandatory positional args, so anything not option-flagged goes here.
    tree_flag = False
    out_file = None
    concurrent = 15
    quiet = False
    for option, argument in options:
        if option in ("-c", "--conc"):
            try:
                concurrent = int(argument)
            except ValueError:
                print("We both know %s needs to be passed a number. Don't be a shithead.\n" % option)
                usage()
        elif option in ("-h", "--help"):
            usage()
        elif option in ("-t", "--tree"):
            tree_flag = True
        elif option in ("-o", "--out"):
            out_file = argument
        elif option in ("-q", "--quiet"):
            quiet = True
        else:
            assert False, "unhandled option"
    
    # handle mandatory arguments
    if len(man_args) < 2:
        print("Error: Missing %d of 2 mandatory arguments!" % (2 - len(man_args)))
        print("  required syntax: slasher.py <host> <dictionary>")
        print("  run with -h or --help for usage")
        sys.exit(1)
    elif len(man_args) >= 3:
        print("[!] Unrecognized positional arguments:")
        print("    " + str(man_args[2:]) + " will not be used!\n")
        while True:
            r = raw_input("    Continue? Y/N\n    > ")
            if r in "yY":
                break
            elif r in "nN":
                sys.exit(1)

    # setup our starting page and get path to our wordlist
    host = Page(man_args[0])
    list_path = man_args[1]

    # take credit ;)
    print("\n           #         ##\n\
         ##       ###\n\
        ## ### ###\n\
      ###########\n\
     #############\n\
    ################\n\
    ##################\n\
   #######  ############\n\
  ######      ############\n\
   ###          ############")

    print("\n----------------------------")
    print(" slasher.py     v1.0.0")
    print("  by k-ddev")
    print("----------------------------\n")
    print("  A directory scanner\n")
    print("  target host  : %s" % host.path)
    print("  wordlist     : %s" % list_path)
    print("  reqs at once : %d\n" % concurrent)

    # try a test connection
    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        testaddr = host.path.replace("http://", "").replace("https://", "")
        print ("[*] Checking for remote host connection at [%s]" % testaddr)
        result = test_sock.connect_ex((testaddr, 80))
        test_sock.close()
        if result == 0:
            print ("[*] Great Success!")
        else:
            print ("[!] No connection to [%s]\n[*] Exiting." % testaddr)
            sys.exit(1)
    except socket.error:
        print ("[!] No connection to [%s]\n[*] Exiting." % testaddr)
        sys.exit(1)

    # make sure the dictionary works
    print("\n[*] Checking dictionary: %s" % list_path)
    try:
        with open(list_path) as f:
            dictionary = f.read().strip().split('\n')
        print("[*] Successfully set up them the bomb with [%d] paths to try" % (len(dictionary)))
    except IOError:
        print("[!] Something went wrong :(")
        print("[*] Failed to read [%s]" % list_path)
        sys.exit(1)

    # if no schema was passed, default to http
    if not "http://" in host.path and not "https://" in host.path:
        host.path = "http://" + host.path

    # call our recursive loop
    print("\n[*] Starting scan.")
    scan(host)

    print("\r\033[K\n[*] All their subpage are belong to us!")

"""
to keep track of website's directories and subdirectories, each valid URL
is stored as a Page object, with a collection into which other Page objects
can be inserted. This makes it easy to keep track of the site architecture.
"""
class Page():
    def __init__(self, path):
        self.path = path
        self.subpages = []

    # check if a set of subpages exists
    def test_subpages(self, subpaths):
        urls = []
        for s in subpaths:
            urls.append(self.path + "/" + s)

        reqs = (grequests.get(u) for u in urls)
        responses = grequests.map(reqs)
        for response in responses:
            if response.status_code >= 200 and response.status_code < 300:
                if response.url 
                self.subpages.append(Page(response.url))
                if not quiet:
                    print("\r      └──> Found %s" % response.url + "\033[K")

# primary recursive function
def scan(page):
    print("\r\033[K")
    print("[*] ──╼━═ Scanning in %s ═━╾──" % page.path)
    windex = 0 # for cleaning windows
    while windex < len(dictionary):
        requests = []
        while len(requests) < concurrent and windex < len(dictionary):
            requests.append(dictionary[windex])
            windex += 1
        sys.stdout.write("\r[*] Trying words: %d/%d" % (windex, len(dictionary)) + "\033[K")
        sys.stdout.flush()
        page.test_subpages(requests) 
        
    for subpage in page.subpages:
        scan(subpage) 

# call to main()
try:
    main()
except KeyboardInterrupt:
    print("\n[!] User interrupted scan.")
    sys.exit(1)