import os.path
import shutil
from optimiser.optimiser import Optimiser
from animated_gif import OptimiseAnimatedGIF
import logging

class OptimiseGIF(Optimiser):
    """
    Optimises gifs. If they aren't animated, it converts them to pngs with ImageMagick before
    optimising them as for pngs.

    Animated gifs get optimised according to the commands in OptimiseAnimatedGIF
    """


    def __init__(self, **kwargs):
        super(OptimiseGIF, self).__init__(**kwargs)

        # the command to execute this optimiser
        if kwargs.get('quiet') == True:
            pngcrush = 'pngcrush -rem alla -brute -reduce -q "__INPUT__" "__OUTPUT__"'
        else:
            pngcrush = 'pngcrush -rem alla -brute -reduce "__INPUT__" "__OUTPUT__"'
        self.commands = ('convert "__INPUT__" png:"__OUTPUT__"',
            'pngnq -n 256 -o "__OUTPUT__" "__INPUT__"',
            pngcrush)

        # variable so we can easily determine whether a gif is animated or not
        self.animated_gif_optimiser = OptimiseAnimatedGIF()

        self.converted_to_png = False
        self.is_animated = False

        # format as returned by 'identify'
        self.format = "GIF"


    def set_input(self, input):
        super(OptimiseGIF, self).set_input(input)
        self.converted_to_png = False
        self.is_animated = False


    def _is_animated(self, input):
        """
        Tests an image to see whether it's an animated gif
        """
        return self.animated_gif_optimiser._is_acceptable_image(input)

    def _get_command(self):
        """
        Returns the next command to apply
        """

        command = False

        # for the first iteration, return the first command
        if self.iterations == 0:
            # if the GIF is animated, optimise it
            if self._is_animated(self.input):
                command = self.animated_gif_optimiser.commands[0]
                self.is_animated = True
            else:             # otherwise convert it to PNG
                command = self.commands[0]

        # execute the png optimisations if the gif was converted to a png
        elif self.converted_to_png and self.iterations < len(self.commands):
            command = self.commands[self.iterations]

        self.iterations += 1

        return command
