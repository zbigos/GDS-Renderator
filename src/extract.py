import sys # read command-line arguments
import os
import json
import gdspy # open gds file
import argparse
import logging
import uuid
import copy
import svgwrite
import subprocess

log_format = logging.Formatter('%(asctime)s - %(module)-10s - %(levelname)-8s - %(message)s')
logger = logging.getLogger('')
logger.setLevel(logging.NOTSET)
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(log_format)
logger.addHandler(ch)

def generate_layermask(layer_name: str, polys):
    logging.info(f"generating {layer_name} with {len(polys)} polygons")
    dwg = svgwrite.Drawing(f'masks/{layer_name}.svg', profile='tiny')
    for p in polys:
        dwg.add(svgwrite.shapes.Polygon(p.tolist(), fill='red'))
    dwg.save()

def read_gds(filepath: str):
    logger.info(f"trying to read {filepath} as .gds file...")
    gdsii = gdspy.GdsLibrary()
    gdsii.read_gds(filepath, units='import')
    cells = [c for c in gdsii]
    logger.info(f"found {len(cells)} cells")

    logger.info(f"I will now attempt to flatten and find the biggest cell...")
    cells_by_polys = []
    for cit, cell in enumerate(cells):
        cell_flat = copy.deepcopy(cell).flatten()
        cells_by_polys.append((len(cell_flat.polygons), uuid.uuid4(), cell_flat))
        logger.debug(f"{cell.name}: {cit} of {len(cells)} done...")
        if cit > 50:
            break

    cc, _, cell = sorted(cells_by_polys)[-1]
    logger.info(f"it looks like {cell.name} is the major with {cc} polys.")
    layers = cell.get_polygons(True)
    logger.info(f"{cell.name} has {len(layers)} layers. Iterating and creating polygons...")
    for lname, polys in layers.items():
        generate_layermask(lname, polys)

#read_gds("../caravel_user_project/openlane/user_project_wrapper/runs/user_project_wrapper/results/magic/user_project_wrapper.gds")

def emit_stl(filename):
    logger.info(f"working on {filename}")

    try:
        os.rm("stls/generate_stl.scad")
    except:
        pass
    
    with open("stls/generate_stl.scad", "w+") as f:
        f.write("linear_extrude(height = 0.1, center = true, scale = 1.0)")
        f.write(f"import(file = \"{os.getcwd()}/masks/{filename}\", center = false, dpi = 96);")

    subprocess.call(["openscad", "stls/generate_stl.scad", "-o", f"{os.getcwd()}/stls/{filename}.stl"])

def convert_to_stls():
    logger.info(f"since blender is stupid, I'll generate .stl from .svg using openscad")
    files = os.listdir("masks/")
    for mfile in files:
        emit_stl(mfile)
        
read_gds("../caravel_user_project/openlane/user_project_wrapper/runs/user_project_wrapper/results/magic/user_project_wrapper.gds")
convert_to_stls()
#python3 gds_to_json.py -g ../../caravel_user_project/openlane/user_project_wrapper/runs/user_project_wrapper/results/magic/user_project_wrapper.gds 
# -l ../../caravel_user_project/openlane/user_project_wrapper/runs/user_project_wrapper/results/lvs/user_project_wrapper.lvs.lef.json -o out.json
