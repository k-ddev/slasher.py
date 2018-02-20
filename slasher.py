#!/usr/bin/env python3

"""
A directory bruteforce tool. Requires Python 3
 - k-ddev

Possible functionality ideas for future:
    scanning optimizations, hotkeys to control flow,
    scraping for URIs on fetched pages, session pause/save/resume,
    maybe others...
"""

import sys
import getopt
import grequests

# usage
def usage():
    print("Usage: slasher.py <host> <dictionary>")
    print("  options:")
    print("  -c --conc <num>        :: manually select number of concurrent requests. Defaults to 15")
    print("  -h --help              :: display usage (what you're seeing now)")
    print("  -a --all               :: scan every page found, not just ones we *think* are directories.")
    print("  -l --listable          :: scan listable directories (which aren't scanned by default)")
    print("  -t --tree              :: view site map as tree once scan is done (not yet implemented)")
    print("  -o --out <path>        :: print site tree to outfile (not yet implemented)")
    print("  -q --quiet             :: don't echo page URLs when a page is found")

def main():

    # globals
    global concurrent # how many concurrent requests to make at once
    global host       # collection of all Page objects (see class Page), starting w/ passed target URL
    global dictionary # loaded words
    global quiet      # shh
    global schema     # webpage request schema (http:// or https://)

    # collect options and arguments
    try:
        options, a = getopt.getopt(sys.argv[1:], "c:halto:q", [
            "conc=",
            "help",
            "all",
            "listable",
            "tree",
            "out=",
            "quiet"
        ])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(1)

    # init flag / config variables
    man_args = a # program takes mandatory positional args, so anything not option-flagged goes here.
    all_flag = False
    list_flag = False
    tree_flag = False
    out_file = None
    concurrent = 15
    quiet = False

    # now handle our options
    for option, argument in options:
        if option in ("-c", "--conc"):
            try:
                concurrent = int(argument)
            except ValueError:
                print("We both know %s needs to be passed a number. Don't be a shithead.\n" % option)
                usage()
                sys.exit(1)

        elif option in ("-h", "--help"):
            usage()
            sys.exit(0)

        elif option in ("-a", "--all"):
            all_flag = True

        elif option in ("-t", "--tree"):
            tree_flag = True

        elif option in ("-l", "--listable"):
            list_flag = True

        elif option in ("-o", "--out"):
            out_file = argument

        elif option in ("-q", "--quiet"):
            quiet = True

        else:
            assert False, "unhandled option"
    
    # handle mandatory / positional arguments
    if len(man_args) < 2:
        print("Error: Missing %d of 2 mandatory arguments!" % (2 - len(man_args)))
        print("  required syntax: slasher.py <host> <dictionary>")
        print("  run with -h or --help for usage")
        sys.exit(1)

    elif len(man_args) >= 3:
        print("[!] Unrecognized positional arguments:")
        print("    " + str(man_args[2:]) + " will not be used!")

        while True:
            r = input("    Continue? Y/N\n    > ")
            if r in "yY":
                print("[*] Proceeding, gnoring unrecognized args...")
                break

            elif r in "nN":
                print("[!] User chose to end scan.")
                sys.exit(1)

            print("\n[!] Invalid response. Please try again.")

    # setup our starting page and get path to our wordlist
    host = [ [Page(man_args[0], None, False, True)] ] # 2d list. ctrl+f "main scan loop" for deets on why it's this way
    top = host[0][0] # this is just for convenience when we need to reference only the main site page.
    list_path = man_args[1]

    # get schema
    if "https://" in top.uri:
        schema = "https://"
        top.uri = top.uri[8:]

    elif "http://" in top.uri:
        schema = "http://"
        top.uri = top.uri[7:]

    else:
        schema = "http://"

    # take credit ;)
    if 1:
        print("")
        print("           #         ##")
        print("         ##       ###")
        print("        ## ### ###")
        print("      ###########")
        print("     #############")
        print("    ################")
        print("    ##################")
        print("   #######  ############")
        print("  ######      ############")
        print("   ###          ############")
        print("\n----------------------------")
        print(" slasher.py     v1.1.0")
        print("  by k-ddev")
        print("")
        print("  A directory scanner\n")
    else:
        print("\n----------------------------")
    print("  Target host  - %s" % top.uri)
    print("  Wordlist     - %s" % list_path)
    print("  Requests     - %d" % concurrent)
    print("  Enabled modes:")
    if all_flag:
        print("    [*] scan all") 
    if list_flag:
        print("    > scan listable")
    print("----------------------------\n")

    # make sure top is even connectable
    print ("[*] Checking for remote host connection at [%s]" % (schema + top.uri))
    response = grequests.map([grequests.get(schema + top.uri)])[0]
    try:
        if response.status_code >= 200 and response.status_code < 300:
            print ("[*] Great Success!")

        else:
            print ("[!] No connection to [%s]\n[*] Exiting." % (schema + top.uri))
            sys.exit(1)
    except:
        print ("[!] No connection to [%s]\n[*] Exiting." % (schema + top.uri))
        sys.exit(1)

    # make sure the dictionary works
    print("\n[*] Checking dictionary: [%s]" % list_path)
    try:
        with open(list_path) as f:
            dictionary = f.read().strip().split('\n')
        print("[*] Successfully set up them the bomb with [%d] paths to try" % (len(dictionary)))
    except IOError:
        print("[!] Something went wrong :(")
        print("[*] Failed to read [%s]" % list_path)
        sys.exit(1)

    # main scan loop
    """
    Here's where our collection 'host' comes into play. Each index of host
    represents a level of the site. host[0] as seen already contains only
    the top page. host[1] will be each page below top, and host[2] will
    contain every subpage of every page in host[1], and so on. Our loop
    will scan every page in host[i], collecting found pages into host[i+1].
    If host[i+1] contains no pages, we know there's nothing else to find.   
    """
    print("\n[*] Starting scan.")
    depth = 0
    while True:
        # allocate a new index of host for any pages we find
        host.append([])
        try:
            assert len(host) == depth + 2
        except AssertionError:
            print("[!] Something weird happened. The greatest depth of the site as we know it")
            print("    should be 1 greater than the depth of the pages currently being scanned,")
            print("    but is not.")
            sys.exit(0)

        # scan every page on current depth and collect found pages
        for page in host[depth]:
            if all_flag or page.may_be_directory:
                if not list_flag and page.is_listable:
                    print("\r\033[K\n[*] skipped listable directory: %s" % page.get_url())
                    print("    specify -l to scan listable")

                else:
                    found = scan(page)
                    for f in found:
                        host[-1].append(f)

        # if no more pages were found, we're done. Otherwise, go to next depth
        if len(host[-1]) == 0:
            break

        else:
            depth += 1

    print("\r\033[K\n[*] All their subpage are belong to us!")

"""
to keep track of website's directories and subdirectories, each valid page found
is stored as a Page object, with a collection into which other Page objects
can be inserted, each being able to reference the page in which they're being
inserted as their superpage. This makes it easy to keep track of the site's
architecture.
"""
class Page():
    def __init__(self, uri, superpage, is_listable, may_be_directory):
        self.uri = uri
        self.subpages = []
        self.superpage = superpage
        self.is_listable = is_listable
        self.may_be_directory = may_be_directory

    # since our page object stores a URI, we need to be able to get the actual URL
    # by going up through our superpages
    def get_url(self):
        path = ""
        if self.superpage != None:
            path = (self.superpage.get_url() + "/" + self.uri).replace("//", "/")

        else:
            path = self.uri

        return path
            
    # check if a set of subpages exists
    def test_subpages(self, subpaths):
        urls = []

        for s in subpaths:
            urls.append(schema + (self.get_url() + "/" + s).replace("//", "/"))

        reqs = (grequests.get(u) for u in urls)
        responses = grequests.map(reqs)

        for response in responses:
            try:
                if response.status_code >= 200 and response.status_code < 300:
                    found_uri = response.url.split("/")[-1]

                    # account for '/' on end of uri
                    if not found_uri:
                        found_uri = response.url.split("/")[-2] + "/"

                    # check for hints the page is listable
                    listable = False

                    for foo in [
                        "Parent Directory",
                        "Up To ",
                        "Atr�s A ",
                        "Directory Listing For"
                    ]:
                        if foo in response.text:
                            listable = True
                    
                    # check if we got something that could be HTML doc (may be directory), or not
                    directory = False
                    if "<!DOCTYPE" in response.text and not ".php" in response.url[-4:]:
                        directory = True

                    self.subpages.append(Page(found_uri, self, listable, directory))

                    if not quiet:
                        print("\r      └──> Found /%s" % found_uri + "\033[K")
            except:
                # no connection to page. Nothing else to do
                pass

# scan a page by supplying word collections to calls of test_subpages
# return a collection of found pages.
def scan(page):
    print("\r\033[K")
    print("[*] ──╼━═ Scanning %s ═━╾──" % (schema + page.get_url()))
    windex = 0 # for cleaning windows ;)

    while windex < len(dictionary):
        requested = []

        while len(requested) < concurrent and windex < len(dictionary):
            requested.append(dictionary[windex])
            windex += 1

        sys.stdout.write("\r[ ] Trying words: %d/%d" % (windex, len(dictionary)) + "\033[K")
        sys.stdout.flush()
        page.test_subpages(requested)

    return page.subpages

# call to main()
try:
    main()
except KeyboardInterrupt:
    print("\n[!] User keyboard interrupt")
    sys.exit(1)
