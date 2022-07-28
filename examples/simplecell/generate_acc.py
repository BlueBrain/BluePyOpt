#!/usr/bin/env python

'''Example for generating a mixed JSON/ACC Arbor cable cell description

 $ python generate_acc.py --output-dir test_acc/ --replace-axon

 Will save 'simple_cell.json', 'simple_cell_label_dict.acc' and 'simple_cell_decor.acc'
 into the folder 'test_acc' that can be loaded in Arbor with:
     'with open("test_acc/simple_cell_cell.json") as cell_json_file:
        cell_json = json.load(cell_json_file)
      morpho = arbor.load_swc_arbor("test_acc/" + cell_json["morphology"]["path"])
      labels = arbor.load_component("test_acc/" + cell_json["label_dict"]).component
      decor = arbor.load_component("test_acc/" + cell_json["decor"]).component'
 An implementation with axon-replacement is available in ephys.create_acc.read_acc.
 An Arbor cable cell is then created with
     cell = arbor.cable_cell(morpho, labels, decor)
 The resulting cable cell can be output to ACC for visual inspection 
 in the Arbor GUI (File > Cable cell > Load) using
     arbor.write_component(cell, "simple_cell.acc")
'''
import argparse

from bluepyopt import ephys

import simplecell_model
from generate_hoc import param_values


def main():
    '''main'''
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    parser.add_argument('-o', '--output-dir', dest='output_dir',
                        help='Output directory for JSON/ACC files')
    parser.add_argument('-ra', '--replace-axon', action='store_true',
                        help='Replace axon with Neuron-dependent policy')
    args = parser.parse_args()

    cell = simplecell_model.create(do_replace_axon=args.replace_axon)
    if args.replace_axon:
        nrn_sim = ephys.simulators.NrnSimulator()
        cell.instantiate_morphology(nrn_sim)

    if args.output_dir is not None:
        ephys.create_acc.output_acc(args.output_dir, cell, param_values)
    else:
        output = cell.create_acc(
            param_values, template='acc/*_template.jinja2')
        for el, val in output.items():
            print("%s:\n%s\n" % (el, val))


if __name__ == '__main__':
    main()
