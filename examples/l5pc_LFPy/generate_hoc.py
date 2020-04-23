#!/usr/bin/env python

'''Example for generating a hoc template

 $ python generate_hoc.py > test.hoc

 Will save 'test.hoc' file, which can be loaded in neuron with:
     'load_file("test.hoc")'
 Then the hoc template needs to be instantiated with a morphology
     CCell("ignored", "path/to/morphology.swc")
'''
import sys

import l5pc_model


def main():
    '''main'''
    param_values = {
        'gNaTs2_tbar_NaTs2_t.apical': 0.026145,
        'gSKv3_1bar_SKv3_1.apical': 0.004226,
        'gImbar_Im.apical': 0.000143,
        'gNaTa_tbar_NaTa_t.axonal': 3.137968,
        'gK_Tstbar_K_Tst.axonal': 0.089259,
        'gamma_CaDynamics_E2.axonal': 0.002910,
        'gNap_Et2bar_Nap_Et2.axonal': 0.006827,
        'gSK_E2bar_SK_E2.axonal': 0.007104,
        'gCa_HVAbar_Ca_HVA.axonal': 0.000990,
        'gK_Pstbar_K_Pst.axonal': 0.973538,
        'gSKv3_1bar_SKv3_1.axonal': 1.021945,
        'decay_CaDynamics_E2.axonal': 287.198731,
        'gCa_LVAstbar_Ca_LVAst.axonal': 0.008752,
        'gamma_CaDynamics_E2.somatic': 0.000609,
        'gSKv3_1bar_SKv3_1.somatic': 0.303472,
        'gSK_E2bar_SK_E2.somatic': 0.008407,
        'gCa_HVAbar_Ca_HVA.somatic': 0.000994,
        'gNaTs2_tbar_NaTs2_t.somatic': 0.983955,
        'decay_CaDynamics_E2.somatic': 210.485284,
        'gCa_LVAstbar_Ca_LVAst.somatic': 0.000333,
    }
    cell = l5pc_model.create()
    print(cell.create_hoc(param_values))


if __name__ == '__main__':
    if '-h' in sys.argv or '--help' in sys.argv:
        print(__doc__)
    else:
        main()
