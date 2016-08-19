#! /usr/bin/env python3

"""

This script coalesces the results from running Fraunhofer FIT ZETA and
merges all of the output files from the evaluation task.

"""

import os
import pandas as pd
import argparse
import ntpath
import itertools as itt

parser = argparse.ArgumentParser()

parser.add_argument('--input-directory', '-d')
parser.add_argument('--output', '-o')

args = parser.parse_args()

base = os.path.expanduser(args.input_directory)
intervals = 'VAC3-1H96H-20x', 'VAC3-24H96H-20X', 'VAC3-96H96H-20X'

compounds = {
    'Cpd 01': list(range(14, 24)),
    'Cpd 05': list(range(26, 36)),
    'Cpd 10': list(range(38, 48)),
    'Cpd 14': list(range(50, 60)),
    'Cpd 21': list(range(62, 72)),
    'Negative': list(range(74, 84))
}

positive_compounds = sorted(compound for compound in compounds if compound != 'Negative')

valid_wells = set(itt.chain.from_iterable(compounds.values()))

concentrations = {}
calcium = {}
ca = {}

for compound, cwells in compounds.items():
    for well in cwells[0:5]:
        calcium[well] = 'low'
    for well in cwells[5:10]:
        calcium[well] = 'high'
        
    for i in range(5):
        concentrations[cwells[i]] = i + 1
        concentrations[cwells[i + 5]] = i + 1
        
    for well in cwells:
        ca[well] = compound
        
results = {}

for interval in intervals:
    interval_path = os.path.join(base, interval)
    
    if os.path.exists(os.path.join(interval_path, '.DS_Store')):
        os.remove(os.path.join(interval_path, '.DS_Store'))
    
    for well_code in os.listdir(interval_path):
        well_path = os.path.join(interval_path, well_code)
        
        well = int(well_code[1:])
        if well not in valid_wells:
            continue
        
        data_path = min(f for f in os.listdir(well_path) if f.endswith('.csv'))
        df = pd.read_csv(os.path.join(well_path, data_path))

        images = df['Image Path'].map(lambda path: ntpath.basename(os.path.normpath(path)))

        image_well = images.map(lambda v: int(v[1:3]))
        time = images.map(lambda v: 1 if '1H96H' in v else (24 if '24H96H' in v else 96))
        replicate = images.map(lambda v: int(v[-5:-4]))

        df['Image Path'] = images
        df['Well'] = image_well
        df['Interval'] = time
        df['Replicate'] = replicate
        df['Calcium'] = image_well.map(calcium)
        df['Concentration'] = image_well.map(concentrations)
        df['Compound'] = image_well.map(ca)

        del df['Barcode ']
        del df['Site ']
        del df['Class 2 ']
        del df['Well ']
            
        results[interval, well] = df
    
results = pd.concat(list(results.values()))
results.to_csv(args.output)
