import json
import os
import glob
from lens_correction.meta_to_montage_and_collection import (
        MetaToMontageAndCollection,
        get_z_from_metafile,
        check_failed_from_metafile)
from lens_correction.upload_montage import UploadToRender
from lens_correction.montage_plots import MontagePlots
from EMaligner.EMaligner import EMaligner
import numpy as np

#refdir = "/data/em-131fs3/lctest/T6_13/20190307140403_reference/0"
#zr = np.concatenate([[3197, 3198, 3199, 3202, 3203], range(3205, 3226), [3232, 3239, 3240]])
#zr = [3198]
#
#refdir = "/data/em-131fs3/lctest/T4_02/20190312121454_reference/0"
#monbase = "/data/em-131fs3/lctest/T4_02"
#zr = range(1848, 1881)
#
#refdir = "/data/em-131fs3/lctest/T4_03/20190313102111_reference/0"
#monbase = "/data/em-131fs3/lctest/T4_03"
#zr = range(1880, 1886)
#zr = [1880]

refdir = "/data/em-131fs3/lctest/AI007_large_aperture_test/20190313145211_reference/0"
monbase = "/data/em-131fs3/lctest/AI007_large_aperture_test"
zr = [46]
#refdir = "/data/em-131fs3/lctest/AI007_large_aperture_test/20190313153231_reference/0"
#monbase = "/data/em-131fs3/lctest/AI007_large_aperture_test"
#zr = [58]
#refdir = "/data/em-131fs3/lctest/AI007_large_aperture_test/20190313162722_reference/0"
#monbase = "/data/em-131fs3/lctest/AI007_large_aperture_test"
#zr = [117]
#refdir = "/data/em-131fs3/lctest/AI007_large_aperture_test/20190314120221_reference/0"
#monbase = "/data/em-131fs3/lctest/AI007_large_aperture_test"
#zr = [122]

refdir = "/data/em-131fs3/lctest/T4_07/20190315150001_reference/0"
monbase = "/data/em-131fs3/lctest/T4_07"
zr = [1935]

refdir = "/data/em-131fs3/lctest/T4_07/20190315142205_reference/0"
monbase = "/data/em-131fs3/lctest/T4_07"
zr = [1931]

#refdir = "/data/em-131fs3/lctest/T4_05/20190313171227_reference/0"
#monbase = "/data/em-131fs3/lctest/T4_05"
#zr = range(1894, 1903)
#refdir = "/data/em-131fs3/lctest/T4_05/20190313211417_reference/0"
#monbase = "/data/em-131fs3/lctest/T4_05"
#zr = range(1903, 1912)
#refdir = "/data/em-131fs3/lctest/T4_05/20190314011548_reference/0"
#monbase = "/data/em-131fs3/lctest/T4_05"
#zr = range(1912, 1922)
#refdir = "/data/em-131fs3/lctest/T4_05/20190314011548_reference/0"
#monbase = "/data/em-131fs3/lctest/T4_05"
#zr = range(1912, 1922)
#refdir = "/data/em-131fs3/lctest/T4_06/20190314112300_reference/0"
#monbase = "/data/em-131fs3/lctest/T4_06"
#zr = range(1931, 1933)
#zr = [1933]


for z in zr:
    mondir = os.path.join(monbase,"%06d/0" % z)

    with open('./lens_correction/templates/meta_template.json') as f:
        meta_args = json.load(f)
    with open('./lens_correction/templates/upload_template.json') as f:
        upload_args = json.load(f)
    with open('./lens_correction/templates/montage_template.json') as f:
        solver_args = json.load(f)
    with open('./lens_correction/templates/mplots_template.json') as f:
        mplot_args = json.load(f)
    
    meta_args['data_dir'] = mondir
    meta_args['output_dir'] = mondir
    meta_args['ref_transform'] = glob.glob(
            os.path.join(refdir, "lens_correction_transform.json"))[0]
    
    upload_args['data_dir'] = mondir
    rndr_name = monbase.replace("/", "_").replace("-", "")[1:]
    upload_args['stack'] = rndr_name
    upload_args['collection'] = rndr_name
    
    solver_args['input_stack']['name'] = rndr_name
    solver_args['pointmatch']['name'] = rndr_name
    solver_args['output_stack']['name'] = rndr_name + '_solved'
    metap = glob.glob(os.path.join(
        mondir, "_metadata*.json"))[-1]
    z = get_z_from_metafile(metap)
    solver_args['first_section'] = z
    solver_args['last_section'] = z
    #solver_args['regularization']['default_lambda'] = 1000
    #solver_args['transformation'] = 'Polynomial2DTransform'
    
    mplot_args['stack'] = solver_args['output_stack']['name']
    mplot_args['collection'] = solver_args['pointmatch']['name']
    mplot_args['output_dir'] = mondir
    mplot_args['z'] = z
    mplot_args['make_plot'] = True
    mplot_args['save_json'] = True
    
    failed = check_failed_from_metafile(metap)
    
    if failed:
        print('%s indicates failed QC' % metap)
    else:
        try:
            mmod = MetaToMontageAndCollection(input_data=meta_args, args=[])
            mmod.run()

            umod = UploadToRender(input_data=upload_args, args=[])
            umod.run()
    
            smod = EMaligner(input_data=solver_args, args=[])
            smod.run()

            collection = os.path.join(
                meta_args['output_dir'],
                "montage_collection.json")
            with open(collection, 'r') as f:
                mplot_args['sectionId'] = json.load(f)[0]['pGroupId']

            mpmod = MontagePlots(input_data=mplot_args, args=[])
            mpmod.run()
        except:
            pass