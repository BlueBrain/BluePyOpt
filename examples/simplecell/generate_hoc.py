#!/usr/bin/env python

'''Example for generating a hoc template

 $ python generate_hoc.py > test.hoc

 Will save 'test.hoc' file, which can be loaded in neuron with:
     'load_file("test.hoc")'
 Then the hoc template needs to be instantiated with a morphology
     CCell("ignored", "path/to/morphology.swc")
'''
import sys

import simplecell_model


param_values = {
    'gnabar_hh': 0.10299326453483033, 
    'gkbar_hh': 0.027124836082684685
}


def main():
    '''main'''
    cell = simplecell_model.create(do_replace_axon=True)

    output = cell.create_hoc(param_values, template='cell_template.jinja2')
    print(output)


if __name__ == '__main__':
    if '-h' in sys.argv or '--help' in sys.argv:
        print(__doc__)
    else:
        main()
