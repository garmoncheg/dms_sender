import urllib
import urllib2
import io
import os
import sys
import mimetools, mimetypes
import itertools
import ConfigParser
import datetime

__version__ = '0.4'

PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])
DEFAULT_CFG_FILE = 'dms_sender.cfg'
DEFAULT_CFG_CHAPTER = 'main'
DEFAULT_CFG_OPTIONS = [
    'user',
    'pass',
    'host',
    'url',
    'directory',
    'mimetype',
    'files_type',
    'user_agent'
]
DEFAULT_API_LOCATION = 'api/file/'
DEFAULT_USER_AGENT = 'Adlibre DMS API file uploader version: %s' % __version__
DEFAULT_FILE_TYPE = 'pdf'
DEFAULT_MIMETYPE = 'application/pdf'
ERROR_FILE_PREFIX = '.error'
ERROR_FILE_MAIN = 'error.txt'
DEFAUULT_ERROR_MESSAGES = {
    'no_host': 'You should provide host to connect to. Please refer to help, running with -help',
    'no_config_or_console': 'Nothing to do. you should provide config and/or console parameters. Exiting.',
    'no_url': 'You should not provide an empty url',
    'no_mimetype': 'You should not provide an empty mimetype. Try to run with -h for help.',
    'no_data': 'You have missed data to be sent. Please provide -dir or -f to be sent into API. Refer to -h for help.',
    'no_username': 'You should provide username. Using config or -user param. Refer to -h for help.',
    'no_password': 'You should provide password. Using config or -pass param. Refer to -h for help.',
    'no_filetype': 'You must configure and/or provide extension of files to scan in the directory you have provided.',
    'no_proper_data': 'You made provided directory instead of file, reverse or target file/directory does not exist. Please recheck location in your config. Refer to -h for help.',
}

#host = 'http://127.0.0.1:8000/' #'http://jtg-stage.dms.adlibre.net/'
#USERNAME = 'admin'
#PASSWORD = 'admin'
#
#filename = 'ADL-0001.pdf'
#file_type = 'pdf'
#mimetype = 'application/pdf'
#

#user_agent =
#
#error_file_prefix = '.error'
#
#error_files_directory = '/errors/'

help_text = """
Command line Adlibre DMS file uploader utility.
Version """ + __version__ +"""

Uploads file/directory into Adlibre DMS Api, depending on options/config specified.
Looks for options file called options.conf in the folder directory and uses it's data for posting.

In order to function it must have configuration file, usually called '""" + DEFAULT_CFG_FILE + """'.
you may override those settings by calcifying alternative configuration file with '-config' key.

Available options:
(Config file options are marked in [] and are equivalent)

    -config
        alternative configuration file you must specify in your system absolute path,
        or simply it's filename in case it lays in this program directory.
        e.g. '-config myconfig.cfg'
        will try to load your alternative configuration file called 'myconfig.cfg' that lays in the program path.
        e.g. '-config C:\mydir\congigfile.cfg'
        will try to load file 'configfile.cfg' in your 'C:\mydir\'
    -chapter
        alternative configuration file chapter
        usually marked with [] scopes.
        e.g. [jtg-dms] is marking the section 'jtg-dms' in config and can be handled separately.
        you must call this section specifying it's name directly after parameters.
        e.g. '-chapter jtg-dms'
        This way you can call this to upload into any Adlibre DMS instance API,
        with only specifying it's section name in same configuration file.
    -s
        Silence option.
        Makes your programm output nothing into console whatever happens
    -f
        Filenmae to upload.
        In case of this option set properly program uploads only this file and quits.
        you should pecify it with file name and path,
        e.g. '-f C:\some\path\myfile.pdf'
        or unix ver:
        e.g. '-f ../somedir/file.pdf
    -dir
    [directory=C:\somepath\in\system\]] in config
        Directory to scan files into.
        Scans and sends into API all files,
        in case of this is specified and option -f (single file) not provided
        Can be relative and/or full path to the directory to scan files into.
        e.g.(for windows): C:\scan\documents\adlibre\
        e.g.(for unix): ../../somedir/files/lie/into/
    -user
    [user=your_user_name] in config
        DMS Username to access API
    -pass
    [pass=your_password] in config
        DMS Password to access API
    -host
    [host=http://.....] in config
        host of the api
    -url
    [url=api/file/] in config
        Your Adlibre DMS API location to connect to.
        Default is set to 'api/file/'
        Note you must specify it without the first '/' symbol in order to build the upload url normally.
    -ft
    [file_type=pdf] in config
        Files type to scan for/suggest to API.
        Default is set to 'pdf'
        This needs to be set up if you have provided a -dir setting.
        (In order to know files to scan in provided directory)
    -mimetype
    [mimetype=application/pdf] in config
        mimetype of file to be sent. Default is: application/pdf

Note: Console commands are for overriding config one's.
e.g. In case you will run '""" + sys.argv[0] + """ -f somefile.pdf'
it will assume you want to send one file, you have provided and ignore directory setting at config,
even with provided -config and/or -chapter setting.
"""

###########################################################################################
############################## MULTIPART FORM EMULATOR ####################################
###########################################################################################
class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return

    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.
        parts = []
        part_boundary = '--' + self.boundary

        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value,
              ]
                for name, value in self.form_fields
        )

        # Add the files to upload
        parts.extend(
            [ part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' %\
              (field_name, filename),
              'Content-Type: %s' % content_type,
              '',
              body,
              ]
                for field_name, filename, content_type, body in self.files
        )

        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)


def upload_file(
        host,
        username,
        password,
        url=None,
        user_agent=None,
        mimetype=None,
        file_place=None,
        silent=False
        ):
    """
    Main uploader function
    """
    # Creating Auth Opener
    # create a password manager
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    # Add the username and password.
    # If we knew the realm, we could use it instead of ``None``.
    password_mgr.add_password(None, host, username, password)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    # create "opener" (OpenerDirector instance)
    opener = urllib2.build_opener(handler)
    # Install the opener.
    # Now all calls to urllib2.urlopen use our opener.
    urllib2.install_opener(opener)

    # File upload
    # Opening file for operations
    work_file = open(file_place, "rb")
    # Initializing the form
    form = MultiPartForm()

    # Extracting filename
    file_name = get_full_filename(file_place)

    # Adding our file to form
    form.add_file('file', file_name, fileHandle=work_file, mimetype=mimetype)

    # Build the request
    full_url = url+file_name
    request = urllib2.Request(full_url)
    request.add_header('User-agent', user_agent)
    body = str(form)
    request.add_header('Content-type', form.get_content_type())
    request.add_header('Content-length', len(body))
    request.add_data(body)

    if not silent:
        print 'SENDING FILE: %s' % file_place
    response = None
    try:
        response = opener.open(request)
    except urllib2.HTTPError, e:
        if not silent:
            print 'SERVER RESPONSE: %s' % e
            print 'Writing Error file'
        raise_error(e, file_place)
        pass
    if response:
        if not silent:
            print 'SERVER RESPONSE: OK'

def get_full_filename(name):
    """
    Extracts only filename from full path
    """
    if os.sep or os.pardir in name:
        name = os.path.split(name)[1]
    return name

def getopts(argv):
    """
    Gets options from sys.argv and transfers them into handy dictionary
    """
    opts = {}
    while argv:
        if argv[0][0] == '-':               # find "-name value" pairs
            try:
                # Getting value of this option
                opts[argv[0]] = argv[1]     # dict key is "-name" arg
                argv = argv[2:]
            except IndexError:
                # option has no argv left in the end
                opts[argv[0]] = None
                argv = argv[1:]
        else:
            argv = argv[1:]
    return opts

def parse_config(config_file_name=None, cfg_chapter=False, silent=False):
    """
    Parses specified config file or uses system set.
    """

    def get_option(config, option, config_options):
        # looks for option and appends it to options dictionary
        try:
            try:
                opt_value = config.get(cfg_chapter or DEFAULT_CFG_CHAPTER, option)
                config_options[option] = opt_value
            except ConfigParser.NoOptionError:
                pass
        except ConfigParser.NoSectionError, e:
            if not silent:
                print 'Config file Error:', e

    config_instance = None
    # Getting conf file defined
    if config_file_name:
        confile = config_file_name
    else:
        confile = DEFAULT_CFG_FILE
    # Trying to open file and getting default config if failed.
    try:
        config_instance = open(os.path.join(PROJECT_PATH, confile), "rb")

    except IOError, e:
        if not silent:
            print e
            print 'Trying to read standard config file: ./' + DEFAULT_CFG_FILE
        # Trying to get config from default file if exists
        try:
            config_instance = open(DEFAULT_CFG_FILE, "rb")
        except IOError, e:
            if not silent:
                print e
                print 'Not found standard config. can now function only with console params'
        pass

    if not config_instance:
        if not silent:
            print 'config used ......................................................no'
        return None

    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.readfp(config_instance)

    config_options = {}
    for option in DEFAULT_CFG_OPTIONS:
        get_option(config, option, config_options)

    if not silent:
        print 'config used ......................................................yes'
    return config_options

def raise_error(message=None, error_file_name=None):
    """
    Breaks program with error, message provided.
    Writes down error text to file.
    """
    if error_file_name:
        error_file = open(str(error_file_name)+ERROR_FILE_PREFIX, 'w')
        error_file.seek(0)
        try:
            for line in message.readlines():
                error_file.write(line)
        except Exception:
            error_file.write(unicode(message))
            pass
        error_file.close()
    if message and not error_file_name:
        if os.path.isfile(ERROR_FILE_MAIN):
            err_file = open(ERROR_FILE_MAIN, 'a')
            err_file.write('\n-----------------------------------------------------------------------------\n')
            err_file.write(str(datetime.datetime.now())+'\n')
            err_file.write('-----------------------------------------------------------------------------\n')
        else:
            err_file = open(ERROR_FILE_MAIN, 'w')
            err_file.seek(0)

        err_file.write(message)
        err_file.close()
        print message
        quit()

def walk_directory(rootdir, file_type=None):
    """
    Walks through directory with files of provided format and
    returns the list of their name with path (ready to open) or empty list.
    """
    fileList = []
    for root, subFolders, files in os.walk(rootdir):
        for file in files:
            if file_type:
                if '.' in file:
                    if os.path.splitext(file)[1] == ('.' + str(file_type)):
                        fileList.append(os.path.join(root,file))
            else:
                fileList.append(os.path.join(root,file))
    return fileList

###########################################################################################
##################################### MAIN FUNCTION #######################################
###########################################################################################
if __name__ == '__main__':

    app_args = getopts(sys.argv)

    silent = False
    if '-s' in app_args:
        silent = True

    cfg_chapter = False
    if '-chapter' in app_args:
        cfg_chapter = app_args['-chapter']

    config_file_name = False
    if '-config' in app_args:
        config_file_name = app_args['-config']

    filename = None
    if '-f' in app_args:
        filename = app_args['-f']

    if ('-h' or '-help') in app_args.iterkeys():
        print help_text
        if not silent:
            raw_input("Press Enter to exit...")
            quit()

    config = parse_config(config_file_name=config_file_name, cfg_chapter=cfg_chapter, silent=silent)

    if not app_args and not config:
        if not silent:
            raise_error(DEFAUULT_ERROR_MESSAGES['no_config_or_console'])

    # Getting option from sys.argv first then trying config file
    username = ''
    if '-user' in app_args:
        username = app_args['-user']
    if not username:
        if 'user' in config:
            username = config['user']

    password = ''
    if '-pass' in app_args:
        password = app_args['-pass']
    if not password:
        if 'pass' in config:
            password = config['pass']

    # Setting/Reading and debugging HOST + URL combinations.
    host = ''
    if '-host' in app_args:
        host = app_args['-host']
    if not host:
        if 'host' in config:
            host = config['host']
    if not host:
        raise_error(DEFAUULT_ERROR_MESSAGES['no_host'])

    url = host + DEFAULT_API_LOCATION
    if '-url' in app_args:
        url = host + app_args['-url']
    if not url:
        if 'url' in config:
            url = host + config['url']
    if url == DEFAULT_API_LOCATION:
        raise_error(DEFAUULT_ERROR_MESSAGES['no_host'])
    if url == host:
        if not silent:
            print 'Warning!:'
            print (DEFAUULT_ERROR_MESSAGES['no_url'])
        url = host + DEFAULT_API_LOCATION
        if not silent:
            print 'Api url forced set to default: %s' % url

    # Reading file operational settings
    file_type = DEFAULT_FILE_TYPE
    if '-ft' in app_args:
        file_type = app_args['-ft']
    if not host:
        if 'file_type' in config:
            file_type = config['file_type']
    if not silent:
        print 'Uploading files of type: %s' % file_type

    mimetype = DEFAULT_MIMETYPE
    if '-mimetype' in app_args:
        mimetype = app_args['-mimetype']
    if not mimetype:
        if 'mimetype' in config:
            mimetype = config['mimetype']
    if not silent:
        print 'Using Mimetype: %s' % mimetype
    if not mimetype:
        raise_error(DEFAUULT_ERROR_MESSAGES['no_mimetype'])

    directory = ''
    if '-dir' in app_args:
        directory = app_args['-dir']
    if not directory:
        if 'directory' in config:
            directory = config['directory']
    if (not directory) and (not filename):
        if not silent:
            raise_error(DEFAUULT_ERROR_MESSAGES['no_data'])
    # Forcing filename provided to override default sending directory of files
    if filename:
        if not os.path.isfile(filename):
            raise_error(DEFAUULT_ERROR_MESSAGES['no_proper_data'])
        directory = ''

    # Other miscellaneous error handling
    if directory:
        if not os.path.isdir(directory):
            raise_error(DEFAUULT_ERROR_MESSAGES['no_proper_data'])
        if not file_type:
            raise_error(DEFAUULT_ERROR_MESSAGES['no_filetype'])
    if not mimetype:
        raise_error(DEFAUULT_ERROR_MESSAGES['no_mimetype'])
    if not username:
        raise_error(DEFAUULT_ERROR_MESSAGES['no_username'])
    if not password:
        raise_error(DEFAUULT_ERROR_MESSAGES['no_password'])
    if not host:
        raise_error(DEFAUULT_ERROR_MESSAGES['no_host'])


    # Calling main send function for either one file or directory with directory walker
    if filename:
        upload_file(
                        host,
                        username,
                        password,
                        url=url,
                        user_agent=DEFAULT_USER_AGENT,
                        mimetype=mimetype,
                        file_place=filename,
                        silent=silent
                    )
    elif directory:
        filenames = walk_directory(directory, file_type)
        if not silent:
            print 'Sending files: %s' % filenames
        if not filenames:
            if not silent:
                print 'Nothing to send in this directory.'
            quit()
        for name in filenames:
            upload_file(
                            host,
                            username,
                            password,
                            url=url,
                            user_agent=DEFAULT_USER_AGENT,
                            mimetype=mimetype,
                            file_place=name,
                            silent=silent
                        )