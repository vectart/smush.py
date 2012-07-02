import os.path
from optimiser.optimiser import Optimiser

class OptimisePNG(Optimiser):
    """
    Optimises pngs. Uses pngnq (http://pngnq.sourceforge.net/) to quantise them, then uses pngcrush
    (http://pmt.sourceforge.net/pngcrush/) to crush them.
    """


    def __init__(self, **kwargs):
        super(OptimisePNG, self).__init__(**kwargs)

        if kwargs.get('quiet') == True:
            # pngcrush = 'pngcrush -rem alla -brute -reduce -q "__INPUT__" "__OUTPUT__"'
            optipng =  u"optipng -quiet -force -o7 '__INPUT__' -out '__OUTPUT__'"
            advpng  =  u"advpng -z4 '__OUTPUT__'"
            pngcrush =  u"pngcrush -q -rem gAMA -rem alla -rem cHRM -rem iCCP -rem sRGB -rem time -ext '__OUTPUT__'"
        else:
            # pngcrush = 'pngcrush -rem alla -brute -reduce "__INPUT__" "__OUTPUT__"'
            optipng =  u"optipng -force -o7 '__INPUT__' -out '__OUTPUT__'"
            advpng  =  u"advpng -z4 '__OUTPUT__'"
            pngcrush =  u"pngcrush -rem gAMA -rem alla -rem cHRM -rem iCCP -rem sRGB -rem time -ext '__OUTPUT__'"
        rm =  u"rm '__OUTPUT__'"

        # the command to execute this optimiser
        #self.commands = ('pngnq -n 256 -o "__OUTPUT__" "__INPUT__"', pngcrush)
        self.commands = (optipng,advpng,pngcrush,)

        # format as returned by 'identify'
        self.format = "PNG"


    def _get_output_file_name(self):
       """
       Returns the input file name with Optimiser.output_suffix inserted before the extension
       """
       (basename, extension) = os.path.splitext(self.input)

       if extension.lower() == '.png':
           return basename + Optimiser.output_suffix

       return self.input + Optimiser.output_suffix