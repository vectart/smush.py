#!/usr/bin/env python

import sys, os, os.path, getopt, time, shlex, subprocess, logging, shutil
from subprocess import CalledProcessError
from optimiser.formats.png import OptimisePNG
from optimiser.formats.jpg import OptimiseJPG
from optimiser.formats.gif import OptimiseGIF
from optimiser.formats.animated_gif import OptimiseAnimatedGIF
from scratch import Scratch

__author__     = 'al, Takashi Mizohata'
__credit__     = ['al', 'Takashi Mizohata']
__maintainer__ = 'Takashi Mizohata'

# there should be an option to keep or strip meta data (e.g. exif data) from jpegs

class Smush():
    def __init__(self, **kwargs):
        self.optimisers = {
            'PNG': OptimisePNG(**kwargs),
            'JPEG': OptimiseJPG(**kwargs),
            'GIF': OptimiseGIF(**kwargs),
            'GIFGIF': OptimiseAnimatedGIF(**kwargs)
        }

        self.__files_scanned = 0
        self.__start_time = time.time()
        self.exclude = {}
        for dir in kwargs.get('exclude'):
            if len(dir) == 0:
                continue
            self.exclude[dir] = True
        self.quiet = kwargs.get('quiet')
        self.identify_mime = kwargs.get('identify_mime')

        # setup tempfile for stdout and stderr
        self.stdout = Scratch()
        self.stderr = Scratch()

    def __del__(self):
        self.stdout.destruct()
        self.stderr.destruct()

    def __smush(self, file):
        """
        Optimises a file
        """
        key = self.__get_image_format(file)

        if key in self.optimisers:
            logging.info('optimising file %s' % (file))
            self.__files_scanned += 1
            self.optimisers[key].set_input(file)
            self.optimisers[key].optimise(self.original_dir)


    def process(self, dir, recursive):
        """
        Iterates through the input directory optimising files
        """
        self.original_dir = dir
        if recursive:
            self.__walk(dir, self.__smush)
        else:
            if os.path.isdir(dir):
                dir = os.path.abspath(dir)
                for file in os.listdir(dir):
                    if self.__checkExclude(file):
                        continue
                        
                    if self.identify_mime:
                        import mimetypes
                        (type,encoding) = mimetypes.guess_type(file)
                        if type and (type[:5] != "image"):
                            continue

                    self.__smush(os.path.join(dir, file))
            elif os.path.isfile(dir):
                self.__smush(dir)


    def __walk(self, dir, callback):
        """ Walks a directory, and executes a callback on each file """
        dir = os.path.abspath(dir)
        logging.info('walking %s' % (dir))
        for file in os.listdir(dir):
            if self.__checkExclude(file):
                continue
            
            if self.identify_mime:
                import mimetypes
                (type,encoding) = mimetypes.guess_type(file)        
                if type and (type[:5] != "image"):
                    continue

            nfile = os.path.join(dir, file)
            callback(nfile)
            if os.path.isdir(nfile):
                self.__walk(nfile, callback)


    def __get_image_format(self, input):
        """
        Returns the image format for a file.
        """
        test_command = 'identify -format %%m "%s"' % input
        args = shlex.split(test_command)

        try:
            retcode = subprocess.call(args, stdout=self.stdout.opened, stderr=self.stderr.opened)
            if retcode != 0:
                if self.quiet == False:
                    logging.warning(self.stderr.read().strip())
                return False

        except OSError:
            logging.error('Error executing command %s. Error was %s' % (test_command, OSError))
            sys.exit(1)
        except:
            # most likely no file matched
            if self.quiet == False:
                logging.warning('Cannot identify file.')
            return False

        return self.stdout.read().strip()[:6]


    def stats(self):
        output = []
        output.append('\n%d files scanned:' % (self.__files_scanned))
        arr = []

        for key, optimiser in self.optimisers.iteritems():
            # divide optimiser.files_optimised by 2 for each optimiser since each optimised file
            # gets counted twice
            output.append('    %d %ss' % (
                    optimiser.files_scanned,
                    key,))

            arr.extend(optimiser.array_optimised_file)

        modified = []

        if (len(arr) != 0):
            output.append('Optimised files:')
            for f in arr:
                if f['bytes_saved_percent']:
                    modified.append(f)
                    output.append('    %(bytes_saved_percent)s%% saved\t[%(input_size)s > %(output_size)s]\t%(name)s' % f)
        output.append('Total time taken: %.2f seconds' % (time.time() - self.__start_time))
        return {'output': "\n".join(output), 'modified': modified}


    def __checkExclude(self, file):
        if file in self.exclude:
            logging.info('%s is excluded.' % (file))
            return True
        return False


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hrqs', ['help', 'recursive', 'quiet', 'strip-meta', 'exclude=','identify-mime', 'min-percent=', 'save-optimized='])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    if len(args) == 0:
        usage()
        sys.exit()

    recursive = False
    quiet = False
    strip_jpg_meta = False
    exclude = ['.bzr', '.git', '.hg', '.svn']
    list_only = True
    min_percent = 3
    identify_mime = False
    save_optimized = None

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-r', '--recursive'):
            recursive = True
        elif opt in ('-q', '--quiet'):
            quiet = True
        elif opt in ('-s', '--strip-meta'):
            strip_jpg_meta = True
        elif opt in ('--identify-mime'):
            identify_mime = True
        elif opt in ('--exclude'):
            exclude.extend(arg.strip().split(','))
        elif opt in ('--min-percent'):
            min_percent = int(arg)
        elif opt in ('--save-optimized'):
            save_optimized = arg
        else:
            # unsupported option given
            usage()
            sys.exit(2)

    if quiet == True:
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')

    smush = Smush(strip_jpg_meta=strip_jpg_meta, exclude=exclude, list_only=list_only, quiet=quiet, identify_mime=identify_mime, min_percent=min_percent, save_optimized=save_optimized)

    if save_optimized and os.path.isdir(save_optimized):
        shutil.rmtree(save_optimized, True)

    for arg in args:
        try:
            smush.process(arg, recursive)
            logging.info('\nSmushing Finished')
        except KeyboardInterrupt:
            logging.info('\nSmushing aborted')

    result = smush.stats()
    if list_only and len(result['modified']) > 0:
        logging.error(result['output'])
        sys.exit(1)
    print result['output']
    sys.exit(0)

def usage():
    print """Losslessly optimises image files - this saves bandwidth when displaying them
on the web.

  Usage: """ + sys.argv[0] + """ [options] FILES...

  Example: """ + sys.argv[0] + """ --strip-meta --save-optimized=DIR --recursive DIR

    FILES can be a space-separated list of files or directories to optimise

  Options are any of:
  -h, --help             Display this help message and exit
  -r, --recursive        Recurse through given directories optimising images
  -q, --quiet            Don't display optimisation statistics at the end
  -s, --strip-meta       Strip all meta-data from JPEGs

  --min-percent=INT      Minimum percent of optimisation to warn about (default is > 3%)
  --save-optimized=DIR   Directory to save optimised files
  --exclude=EXCLUDES     Comma separated value for excluding files
  --identify-mime        Fast identify image files via mimetype

  Dependencies:
    sudo apt-get install imagemagick trimage gifsicle libjpeg-progs jpegoptim pngcrush pngnq optipng

  Could be builded by cxfreeze:
    cxfreeze smush.py --include-modules=encodings.ascii --target-dir build/
"""

if __name__ == '__main__':
    main()
