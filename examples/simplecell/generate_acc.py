#!/usr/bin/env python

'''Example for generating a mixed JSON/ACC Arbor cable cell description

 $ python generate_acc.py --output-dir test_acc/

 Will save 'simple_cell.json', 'simple_cell_label_dict.acc' and 'simple_cell_decor.acc'
 into the folder 'test_acc' that can be loaded in Arbor with:
     'with open("test_acc/simple_cell_cell.json") as cell_json_file:
        cell_json = json.load(cell_json_file)
      morpho = arbor.load_swc_arbor("test_acc/" + cell_json["morphology"])
      labels = arbor.load_component("test_acc/" + cell_json["label_dict"]).component
      decor = arbor.load_component("test_acc/" + cell_json["decor"]).component'
 An Arbor cable cell is then created with
     cell = arbor.cable_cell(morpho, labels, decor)
 The resulting cable cell can be output to ACC for visual inspection 
 in the Arbor GUI (File > Cable cell > Load) using
     arbor.write_component(cell, "simple_cell.acc")
'''
import os
import argparse
import shutil

import simplecell_model
from generate_hoc import param_values


def main():
    '''main'''
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    parser.add_argument('-o', '--output-dir', dest='output_dir',
                        help='Output directory for JSON/ACC files')
    args = parser.parse_args()

    # Arbor does not support do_replace_axon=True
    cell = simplecell_model.create(do_replace_axon=False)

    output = cell.create_acc(param_values, template='acc/*_template.jinja2')

    if args.output_dir is not None:
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        for comp, comp_rendered in output.items():
            comp_filename = os.path.join(args.output_dir, comp)
            if os.path.exists(comp_filename):
                raise RuntimeError("%s already exists!" % comp_filename)
            with open(os.path.join(args.output_dir, comp), 'w') as f:
                f.write(comp_rendered)

        morph_filename = os.path.join(args.output_dir,
                                      os.path.basename(cell.morphology.morphology_path))
        if os.path.exists(morph_filename):
            raise RuntimeError("%s already exists!" % morph_filename)
        shutil.copy2(cell.morphology.morphology_path, args.output_dir)
    else:
        for el, val in output.items():
            print("%s:\n%s\n" % (el, val))


if __name__ == '__main__':
    main()
