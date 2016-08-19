import lodel.plugin.scripts as lodel_script

##@brief Implements lodel_admin.py discover-plugin action
#
#In depth directory scan to find plugins.
class DiscoverPlugin(lodel_script.LodelScript):
    _action = 'discover-plugin'
    _description = 'Walk through given folders looking for plugins'
    
    @classmethod
    def argparser_config(cls, parser):
        parser.add_argument('-d', '--directory',
            help="Directory to walk through looking for lodel2 plugins",
            nargs='+')
        parser.add_argument('-l', '--list-only', default=False,
            action = 'store_true',
            help="Use this option to print a list of discovered plugins \
without modifying existing cache")

    @classmethod
    def run(cls, args):
        from lodel.plugin.plugins import Plugin
        if args.directory is None or len(args.directory) == 0:
            cls.help_exit("Specify a least one directory")
        no_cache = args.list_only
        res = Plugin.discover(args.directory, no_cache)
        print("Found plugins in : %s" % ', '.join(args.directory))
        for pname, pinfos in res['plugins'].items():
            print("\t- %s(%s) in %s" % (
                pname, pinfos['version'], pinfos['path']))
            
