h1. Command line Adlibre DMS file uploader utility.

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
e.g. In case you will run 'script_name.py -f somefile.pdf'
it will assume you want to send one file, you have provided and ignore directory setting at config,
even with provided -config and/or -chapter setting.

