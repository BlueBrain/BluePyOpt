#!/usr/bin/env python

'''Example for generating a hoc template

 $ python generate_hoc.py > test.hoc

 Will save 'test.hoc' file, which can be loaded in neuron with:
     'load_file("test.hoc")'
 Then the hoc template needs to be instantiated with a morphology
     CCell("ignored", "path/to/morphology.swc")
'''
import sys
import os
import shutil
from pprint import pprint

import simplecell_model


def main():
    '''main'''
    param_values = {
        'gnabar_hh.somatic': 0.10299326453483033, 
        'gkbar_hh.somatic': 0.027124836082684685
    }
    
    cell = simplecell_model.create()
    output = cell.create_hoc(param_values, template='acc/*_template.jinja2')
    pprint(output)
    if isinstance(output, dict):
        output_dir = os.getcwd()
        for comp, comp_rendered in output.items():
            with open(os.path.join(output_dir, comp),'w') as f:
                f.write(comp_rendered)
        shutil.copy2(cell.morphology.morphology_path, output_dir)




if __name__ == '__main__':
    if '-h' in sys.argv or '--help' in sys.argv:
        print(__doc__)
    else:
        main()
