import os.path
import os
import shlex
import subprocess
import sys
import shutil
import logging
import tempfile
from scratch import Scratch

class Optimiser(object):
    """
    Super-class for optimisers
    """

    input_placeholder = "__INPUT__"
    output_placeholder = "__OUTPUT__"

    # string to place between the basename and extension of output images
    output_suffix = "-opt.smush"


    def __init__(self, **kwargs):
        # the number of times the _get_command iterator has been run
        self.iterations = 0
        self.files_scanned = 0
        self.files_optimised = 0
        self.bytes_saved = 0
        self.list_only = kwargs.get('list_only')
        self.min_percent = kwargs.get('min_percent')
        self.save_optimized = kwargs.get('save_optimized')
        self.array_optimised_file = []
        self.quiet = kwargs.get('quiet')
        self.stdout = Scratch()
        self.stderr = Scratch()

    def __del__(self):
        self.stdout.destruct()
        self.stderr.destruct()

    def set_input(self, input):
        self.iterations = 0
        self.input = input


    def _get_command(self):
        """
        Returns the next command to apply
        """
        command = False
        
        if self.iterations < len(self.commands):
            command = self.commands[self.iterations]
            self.iterations += 1

        return command


    def _get_output_file_name(self):
        """
        Returns the input file name with Optimiser.output_suffix inserted before the extension
        """
        temp = tempfile.mkstemp(suffix=Optimiser.output_suffix)
        try:
            output_file_name = temp[1]
            os.unlink(output_file_name)
            return output_file_name
        finally:
            os.close(temp[0])


    def __replace_placeholders(self, command, input, output):
        """
        Replaces the input and output placeholders in a string with actual parameter values
        """
        return command.replace(Optimiser.input_placeholder, input).replace(Optimiser.output_placeholder, output)


    def _is_acceptable_image(self, input):
        """
        Returns whether the input image can be used by a particular optimiser.

        All optimisers are expected to define a variable called 'format' containing the file format
        as returned by 'identify -format %m'
        """
        test_command = 'identify -format %%m "%s"' % input
        args = shlex.split(test_command)

        try:
            retcode = subprocess.call(args, stdout=self.stdout.opened, stderr=self.stderr.opened)
        except OSError:
            logging.error("Error executing command %s. Error was %s" % (test_command, OSError))
            sys.exit(1)
        except:
            # most likely no file matched
            if self.quiet == False:
                logging.warning("Cannot identify file.")
            return False
        if retcode != 0:
            if self.quiet == False:
                logging.warning("Cannot identify file.")
            return False
        output = self.stdout.read().strip()
        return output.startswith(self.format)


    def optimise(self, original_dir):
        """
        Calls the 'optimise_image' method on the object. Tests the 'optimised' file size. If the
        generated file is larger than the original file, discard it, otherwise discard the input file.
        """
        # make sure the input image is acceptable for this optimiser
        if not self._is_acceptable_image(self.input):
            logging.warning("%s is not a valid image for this optimiser" % (self.input))
            return

        self.files_scanned += 1

        while True:
            command = self._get_command()
            output_file_name = self._get_output_file_name()

            if command:
                command = self.__replace_placeholders(command, self.input, output_file_name)
                logging.info("Executing %s" % (command))
                args = shlex.split(command)
                
                try:
                    retcode = subprocess.call(args, stdout=self.stdout.opened, stderr=self.stderr.opened)
                except OSError:
                    logging.error("Error executing command %s. Error was %s" % (command, OSError))
                    sys.exit(1)

                if retcode != 0:
                    # gifsicle seems to fail by the file size?
                    if os.path.isfile(output_file_name):
                        os.unlink(output_file_name)
                else:
                    if self.list_only == False:
                        # compare file sizes if the command executed successfully
                        self._keep_smallest_file(self.input, output_file_name)
            else:
                if self.list_only == True:
                    is_optimised = self._list_only(self.input, output_file_name)
                    if self.save_optimized and is_optimised:
                        optimized_path = os.path.join(os.path.abspath(self.save_optimized), os.path.relpath(self.input, original_dir))
                        optimized_dir = os.path.dirname(optimized_path)

                        if not os.path.exists(optimized_dir):
                            os.makedirs(optimized_dir)

                        logging.info("Saving optimised image to %s" % (optimized_path))
                        shutil.copyfile(output_file_name, optimized_path)

                if os.path.isfile(output_file_name):
                    os.unlink(output_file_name)
                break


    def _list_only(self, input, output):
        """
        Always keeps input, but still compares the sizes of two files
        """
        if os.path.isfile(input) and os.path.isfile(output):
            input_size = os.path.getsize(input)
            output_size = os.path.getsize(output)

            if (output_size > 0 and output_size < input_size):
                bytes_saved = (input_size - output_size)
                bytes_saved_percent = int(100 - round((output_size / float(input_size)) * 100))
                self.files_optimised += 1
                self.bytes_saved += bytes_saved

                if bytes_saved_percent > self.min_percent:
                    self.array_optimised_file.append({
                        'name': input,
                        'input_size': input_size,
                        'output_size': output_size,
                        'bytes_saved': bytes_saved,
                        'bytes_saved_percent': bytes_saved_percent,
                    })

                    return True
        return False

    def _keep_smallest_file(self, input, output):
        """
        Compares the sizes of two files, and discards the larger one
        """
        if os.path.isfile(input) and os.path.isfile(output):
            input_size = os.path.getsize(input)
            output_size = os.path.getsize(output)

            # if the image was optimised (output is smaller than input), overwrite the input file with the output
            # file.
            if (output_size > 0 and output_size < input_size):
                try:
                    shutil.copyfile(output, input)
                    self.files_optimised += 1
                    self.bytes_saved += (input_size - output_size)
                except IOError:
                    logging.error("Unable to copy %s to %s: %s" % (output, input, IOError))
                    sys.exit(1)
        

