#!/usr/bin/env python
''' Converts metafiles to p->q collections.
    Jay Borseth 2019.02.15

'''

import argparse
import collections
import glob
import json
import logging
import math
import os
import sys
import time
from enum import IntEnum
from itertools import islice


# Position codes in metafile
class Edge(IntEnum):
    INVALID = 0
    CENTER = 1  # unused
    LEFT = 2
    TOP = 3
    RIGHT = 4


class MetaToCollection(object):
    ''' Converts a raw TEMCA metafile into a collection json file which the render stack can consume.
    '''


    def tile_from_raster_pos(self, args, col, row, direction=None):
        ''' returns a neighboring tile given a col, row.
            direction is either None (return this tile), LEFT, RIGHT, or TOP
        '''
        if direction is None:
            return args.raster_pos_lookup[str(col) + "_" + str(row)]
        elif direction == Edge.LEFT:
            if col > 0:
                return args.raster_pos_lookup[str(col - 1) + "_" + str(row)]
            else:
                return None
        elif direction == Edge.RIGHT:
            if col < args.tcols:
                return args.raster_pos_lookup[str(col + 1) + "_" + str(row)]
            else:
                return None
        elif direction == Edge.TOP:
            if row > 0:
                return args.raster_pos_lookup[str(col) + "_" + str(row - 1)]
            else:
                return None


    def tile_from_tile(self, args, tile, direction=None):
        ''' returns a neighboring tile given a tile.
            direction is either None (return this tile), LEFT, RIGHT, or TOP
        '''
        col, row = tile['img_meta']['raster_pos']
        return self.tile_from_raster_pos(args, col, row, direction)


    def create_raster_pos_dict(self, args):
        ''' create the look up dictionary for raster pos to nodes '''
        args.raster_pos_lookup = {}
        for tile in args.data:
            rp = tile['img_meta']['raster_pos']
            col, row = rp
            args.raster_pos_lookup[str(col) + "_" + str(row)] = tile


    def get_meta_and_montage_files(self, rootdir):
        '''get the names of the meta and montage files'''
        for name in glob.glob(os.path.join(rootdir, r"_meta*.*")):
            meta = name
        montage = None
        for name in glob.glob(os.path.join(rootdir, r"_montage*.*")):
            montage = name
        return (meta, montage)


    def process(self, args):
        ''' the main thing.'''
        tstart = time.time()
        ''' read in the metadata file and extract relevant info'''
        rootdir = args.directory
        try:
            args.meta_file, args.montage_file = self.get_meta_and_montage_files(
                rootdir)

            with open(args.meta_file) as data_file:
                json_data = json.load(data_file)
        except:
            raise Exception("Cannot find or parse metafile in: " +
                            args.directory)

        metadata = args.metadata = json_data[0]['metadata']
        data = args.data = json_data[1]['data']

        temca_id = metadata["temca_id"]
        session_id = metadata["session_id"]
        specimen_id = metadata["specimen_id"]
        if "tape_id" in metadata:
            tape_id = metadata["tape_id"]
        else:
            tape_id = None
        calibration = metadata['calibration']["highmag"]

        # total number of rows and cols
        args.trows = max([tile['img_meta']['raster_pos'][1] for tile in data])
        args.tcols = max([tile['img_meta']['raster_pos'][0] for tile in data])
        print('rows: ', args.trows, ', cols: ', args.tcols)

        # create a dictionary to look up neighboring tiles
        self.create_raster_pos_dict(args)

        collection = []
        samples = []
        tilespecs = []

        qGroupId = pGroupId = session_id

        # for all tiles
        for index, tile in enumerate(data):
            pId = tile["img_path"]
            # hmm, munge the filenames?
            pId = pId.replace(".tif", "")
            tilespec = {
                'tileId': pId,
                'xstage': float(tile["img_meta"]['stage_pos'][0]),
                'ystage': float(tile["img_meta"]['stage_pos'][1])
            }
            tilespecs.append(tilespec)
            # rp = tile['img_meta']['raster_pos']
            # col, row = rp

            p = [[], []]
            q = [[], []]
            w = []

            if 'matcher' in tile:
                for match in tile['matcher']:
                    position = match['position']
                    match_quality = match['match_quality']
                    if match_quality == -1:
                        # -1 is a flag indicating no matches are possible for this tile edge
                        continue
                    neighbor = self.tile_from_tile(args, tile, position)
                    if neighbor:
                        # print(position, tile['img_meta']['raster_pos'], neighbor['img_meta']['raster_pos'])
                        p = [match["pX"], match["pY"]]
                        q = [match["qX"], match["qY"]]
                        w = [1] * len(match["pX"])
                        # hmm, munge the filenames?
                        qId = neighbor["img_path"]
                        qId = qId.replace(".tif", "")

                        samples.append({
                            'pId': pId,
                            'qId': qId,
                            'pGroupId': pGroupId,
                            'qGroupId': qGroupId,
                            'matches': {
                                'p': p,
                                'q': q,
                                'w': w,
                                'match_count': len(w)
                            }
                        })

        output = {
            'collection': samples,
            "calibration": {
                "nm_per_pix": float(calibration["nm_per_pix"]),
                "angle": float(calibration["angle"])
            },
            'tilespecs': tilespecs
        }
        output = samples

        with open(args.output_file, 'w') as f:
            json.dump(output, f, indent=2)

        return


def main(args):
    parent_parser = argparse.ArgumentParser(
        description='Converts raw TEMCA metadata files to render collections')

    parent_parser.add_argument(
        'directory',
        help='the directory to process.',
        metavar="",
        nargs='?',
        default=r'D:\data\lens_correction8\000000\0')

    parent_parser.add_argument(
        '-o',
        '--output_file',
        type=str,
        default="test.json",
        metavar="",
        help='name of the json output file')

    args = parent_parser.parse_args(args)

    m2c = MetaToCollection()
    m2c.process(args)


if __name__ == "__main__":
    main(sys.argv[1:])