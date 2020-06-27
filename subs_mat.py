#!/usr/bin/env python
# coding: utf-8

import copy
import glob
import json
import numpy as np
import os
import random
import re
import shutil
import uuid
from pathlib import Path
from typing import Union, List, Sequence

from collections import Counter
from monty.io import reverse_readfile
from pymatgen.core.composition import Composition
from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure
from pymatgen.io.cif import CifParser, CifWriter
from pymatgen.io.vasp.inputs import Poscar
from pymatgen.io.vasp.outputs import Outcar
from pymatgen.io.vasp.sets import MITRelaxSet
from pymongo import MongoClient

from pymatgen.core.periodic_table import Element, Specie, DummySpecie


if False:
    def load_inputfile(basedir):
        """get files in basedir

        Parameters
        ----------
        basedir: string
            file path

        Returns
        -------
        dict on "basedir","poscar","outcar","ciffile"

        """
        poscar = None
        outcar = None
        ciffile = None
        uuid = None
        outcar_json = None

        filename = os.path.join(basedir, "status.json")
        with open(filename) as f:
            s = f.read()
            dic = json.loads(s)
        current_step = dic["current_step"]

        pattern = re.compile(r'\.cif$')
        for filepath in glob.glob(os.path.join(basedir, current_step, "*")):
            filesplits = os.path.split(filepath)

            filename = filesplits[-1]

            if filename == "POSCAR":
                poscar = filepath
            elif filename == "OUTCAR":
                outcar = filepath
            elif filename == "outcar.json":
                outcar_json = filepath
            elif filename == "_uuid":
                uuid = filepath

            m = pattern.search(filename)
            if m is not None:
                ciffile = filepath

        if poscar is None and ciffile is None:
            print("no geometry file")
            print(basedir)
            raise

        d = {"basedir": basedir,
             "poscar": poscar, "outcar_json": outcar_json,
             "outcar": outcar, "ciffile": ciffile, "uuid": uuid}
        return d


    def make_positionfiles_list(place="Calc/mp-*"):
        """get file information in place

        Parameters
        ----------
        place: string
            file path

        Returns
        -------
        a list of dict
            dict contains poscar,cif,outcar files

        """
        filelist = glob.glob(os.path.join(os.getcwd(), place))
        d_list = []
        for filepath in filelist:
            d = load_inputfile(filepath)
            d_list.append(d)

        d2_list = []
        for d in d_list:
            d2 = {}

            positionfile = {}
            positionfile.update({"hostame": "localhost", "basedir": d["basedir"]})

            filename = d["uuid"]
            uuid_str = None
            with open(filename) as f:
                uuid_str = f.read()
            if uuid_str is None:
                print("error no uuid")
                print(d)

            positionfile.update({"uuid": uuid_str})
            if d["ciffile"] is not None:
                positionfile.update({"kind": "cif", "positionfile": d["ciffile"]})
            else:
                positionfile.update({"kind": "poscar",
                                     "positionfile": d["poscar"]})

            d2.update({"materialfile": positionfile})

            d2.update({"calc_status": None})

            filename = d2["materialfile"]["positionfile"]
            print("filename", filename)
            if filename is None:
                print(d)
                print("possible error")

            structure = SubsStructure.from_file(filename)
            species = structure.element_list()
            d2.update({"species": species, "nspecies": len(species)})
            d2_list.append(d2)

            if False:
                filename = d["outcar_json"]
                print("outcar_json", filename)
                with open(filename) as f:
                    s = f.read()
                outcar_dic = json.loads(s)
                for key in ["converged_electronic", "converged_ionic"]:
                    d2.update({key: outcar_dic[key]})
            d2_list.append(d2)

        return d2_list

if False:
    def make_vasp_inputfiles(position_info, write_all=True):
        """make VASP input files

        Parameters
        ----------
        position_info: dict
            contains dict of input files for a material

        write_all: bool = True
            flag to use pymatgen.MITRelaxSet.write_input() or not

        Returns
        -------
        dict: {"local_rundir": }

        """
        if position_info["positionfile"]["kind"] == "poscar":
            structure = Structure.from_file(position_info["positionfile"]["path"])
        elif position_info["positionfile"]["kind"] == "cif":
            parser = CifParser(position_info["positionfile"]["path"])
            structure = parser.get_structures()[0]

        outputdir = os.path.join(position_info["basedir"], "RUN0001")
        try:
            os.mkdir(outputdir)
        except FileExistsError:
            pass

        mitset = MITRelaxSet(structure, standardize=True)

        if write_all:
            mitset.write_input(outputdir)
        else:
            kpoint = mitset.kpoints
            incar = mitset.incar
            poscar = mitset.poscar

            poscarfile = os.path.join(outputdir, "POSCAR")
            poscar.write_file(poscarfile)
            kpointfile = os.path.join(outputdir, "KPOINT")
            kpoint.write_file(kpointfile)
            incarfile = os.path.join(outputdir, "INCAR")
            incar.write_file(incarfile)
            # skip writing "POTCAR"

        return {"local_rundir": outputdir}


    def get_compostion_from_file(filename):
        """read filename structure file and convert into Compostion

        Parameters
        ----------
        filename: string
            filename of POSCAR, cif, inputfile

        Returns
        -------
        Composition object

        """
        structure = Structure.from_file(filename)

        counter = Counter(structure.species)
        elementlist = []
        for x in counter:
            elementlist.append(str(x)+str(counter[x]))

        materialname = "".join(elementlist)

        material = Composition(materialname)
        return material


class Outcar_suppl(object):
    """alternate class for pymatgen Outcar

    read force, converged from Outcar file

    """

    def __init__(self, filename):
        """initialization of Outcar_suppl

        Parameters
        ----------
        filename: filename of VASP outcar
        """
        self.filename = filename
        self.dict = self.get_outcar_force()

    def as_dict(self):
        """return dict
        """
        return self.dict

    def get_outcar_force(self):
        all_lines = []
        for line in reverse_readfile(self.filename):
            clean = line.strip()
            all_lines.append(clean)

        read_force = False
        converged_electronic = True
        converged_ionic = True
        force = []
        force_keywd = "POSITION                                       "\
                      "TOTAL-FORCE (eV/Angst)"
        abort_electron_keywd = "------------------------ "\
                               "aborting loop because EDIFF is reached"\
                               " ----------------------------------------"

        all_lines.reverse()
        for clean in all_lines:
            if read_force:
                m = re.match(r"(([\d\.\-]+)\s+)+", clean)
                if m:
                    toks = [float(i)
                            for i in re.findall(r"[\d\.\-]+", clean)]
                    force.append(toks[3:])
                elif clean.startswith("total drift:"):
                    read_force = False
            if clean == force_keywd:
                read_force = True
            if clean == abort_electron_keywd:
                converged_electronic = False
            # if for converge_ionic ..

        return {"force": force, "converged_electronic": converged_electronic,
                "converged_ionic": converged_ionic}


class elementListExpansion(object):
    """expand a species list to full columns species dic
    """

    def __init__(self):
        self.element_list = [
            'H',
            'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F',
            'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl',
            'Ar', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn',
            'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As',
            'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb',
            'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In',
            'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La',
            'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb',
            'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta',
            'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl',
            'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac',
            'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk',
            'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr', ]
        self.element_dic = self.make_empty_element_dic()

    def make_empty_element_dic(self):
        """initialize element_dic

        Parameters
        ----------
        None

        Returns
        -------
        dict: contains {element_name: False}
        """
        dic = {}
        for x in self.element_list:
            dic[x] = False
        return dic

    def expansion(self, species):
        """expand species to all columns

        Parameters
        ----------
        species: specie list
            a list of [specie,#_of_specie]

        Returns
        -------
        a dic of existence or not of all elements
        """
        element_dic = copy.deepcopy(self.element_dic)
        for elm in species:
            elm_name = elm[0]
            if elm_name in element_dic:
                element_dic[elm_name] = True
            else:
                print("unknown element name {}, "
                      "but continue.".format(elm_name))
        return element_dic


class subsMaterialsDatabase(object):
    """subsMaterialsDatabase access library

    Please use .collection to access the DB directly.

    """

    def __init__(self, database_name='elem_subst_database',
                 collection_name='material_collection'):
        self.client = MongoClient()
        self.database_name = database_name
        self.collection_name = collection_name
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]

    def collection_remove(self, query=None):
        """remove collection

        Parameters
        ----------
        query: string
            query to pass collection.remove()

        Returns
        -------
        retrun status of collection.remove()
        """
        if query is None:
            ret = self.collection.remove()
        else:
            ret = self.collection.remove(query)
        return ret

    def insert_one(self, doc, element_expansion=True):
        """insert doc

        Parameters
        ----------
        doc: document
            document to insert by insert_one()

        element_expansion: boolean
            add all element columns to DB

        Returns
        -------
        collection.insert_one(doc)
        """
        doc = copy.deepcopy(doc)
        if element_expansion:
            species_longcolumns = doc["species"]
            elm_long = elementListExpansion().expansion(species_longcolumns)
            doc.update(elm_long)
        return self.collection.insert_one(doc)

    def subs_elem_query_sentence(self,subs_elm):
        """make query from sub_elm

        Parameters
        ----------
        subs_elm : alist of elements
            a list of substitute elements, e.g. [["Fe","Co"],["Gd","Sm"]]

        Returns
        -------
        query dic
            {"Fe": True, "Gd": True}
        """
        query_elm_dic = {}
        for x in subs_elm:
            query_elm_dic.update({x[0]: True})
        return query_elm_dic

    def count_documents(self, query):
        """count_documents

        Parameters
        ----------
        query: dict
            filter dict

        Returns
        -------
        number of documents = collection.count_documents(query)
        """
        return self.collection.count_documents(query)

    def find(self,query):
        """find()

        Parameters
        ----------
        query: query sentence for find()
        """
        return self.collection.find(query)

    def find_subs_elems(self,subs_elm):
        """find with subs_elm

        Parameters
        ----------
        subs_elm: a list of elements to substitiute

        Returns
        -------
        collection.find() result
        """
        query_sentence = self.subs_elem_query_sentence(subs_elm)
        return self.find(query_sentence)


    def add_files_under(self, dirname, wrapperclass, absolute_path=True):
        """initialize database using files under dirname directory

        Parameters
        ----------
        dirname: string
            directory name

        wrapperclass: class
            a class to load information
            must has .as_dixt() to save into the database

        absolute_path: boolean
            True (default) will generate absolute path of dirname in DB

        Returns
        -------
        self
        """

        if absolute_path:
            absolute_dirname = str(Path(dirname).resolve())
            dic = wrapperclass(absolute_dirname).as_dict()
        else:
            dic = wrapperclass(dirname).as_dict()
        self.insert_one(dic)

        return self

    def initialize_with_dirs(self, location, wrapperclass):
        """initialize database using files under location directory

        Parameters
        ----------
        location: string
            directory name to pass glob.glob

        wrapperclass: class
            a class to load information
            must has .as_dixt() to save into the database

        Returns
        -------
        self
        """

        self.collection_remove()
        dirlist = glob.glob(os.path.join(location))
        for dirname in dirlist:
            self.add_files_under(dirname, wrapperclass)

        return self



def subs_elms_to_prefix(subs_elm):
    """make prefix from subs_elm list

    Parameters
    ----------
    subs_elm: list of list
        elements to substitute e.g., [["Fe","Co"],["Gd","Sm"]]

    Returns
    -------
    String: substitute elements string, e.g., "Fe_Co,Gd_Sm"
    """
    subs_prefix_list = []
    for x in subs_elm:
        subs_prefix_list.append("_".join(x))
    subs_prefix = ",".join(subs_prefix_list)
    return subs_prefix


class DirNode(object):
    """dirctory access interface for automatic calculation
    """

    def __init__(self, basedir_prefix, hostname="localhost"):
        """initialize dir_node

        Parameters
        ----------
        basedir_prefix: base file path

        hostname: hostname

        create: boolean
            create the first directores or not
        """
        self.basedir_prefix = basedir_prefix
        if not os.path.isdir(self.basedir_prefix):
            os.makedirs(self.basedir_prefix)

        self.status_file = "status.json"
        self.uuid_file = "_uuid"
        self.current_step = self.get_current_step()

    def get_current_step(self):
        """return current_step

        Parameters
        ----------
        None

        Returns
        -------
        current_step : string
            directory name
        """
        filename = os.path.join(self.basedir_prefix, self.status_file)
        status = None
        if os.path.isfile(filename):
            with open(filename) as f:
                status = json.loads(f.read())
            if status is not None:
                return status["current_step"]
        else:
            current_step = "0"
            status = {"current_step": current_step}
            with open(filename, "w") as f:
                f.write(json.dumps(status))
            return current_step

    def get_current_uuid(self):
        """reuturn uuid of the current_step

        Parameters
        ----------
        None

        Returns
        uuid: string
            UUID
        """
        filename = os.path.join(self.basedir_prefix,
                                self.get_current_step(), self.uuid_file)
        uuid = None
        with open(filename) as f:
            uuid = f.read()
        return uuid

    def get_current_dir(self):
        """get current directory full path

        """
        targetdir = os.path.join(self.basedir_prefix, self.current_step)
        return targetdir

    def place_files(self):
        """generate real place

        Parameters
        ----------
        current_step: directory name in self.basedir_prefix

        Returns
        -------
        boolean: True if created
                 False if not created
        """

        basedir_prefix = self.basedir_prefix
        print("targetdir", basedir_prefix, self.current_step)

        targetdir = os.path.join(basedir_prefix, self.current_step)
        # make directory if not exist
        if os.path.isdir(targetdir):
            return False
        else:
            os.makedirs(targetdir)

        filename = os.path.join(basedir_prefix, self.status_file)
        if not os.path.isfile(filename):
            status = {"current_step": self.current_step}
            with open(filename, "w") as f:
                f.write(json.dumps(status))

        # directory UUID
        filename = os.path.join(basedir_prefix, self.uuid_file)
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                f.write(str(uuid.uuid4()))

        # current UUID
        filename = os.path.join(targetdir, self.uuid_file)
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                f.write(str(uuid.uuid4()))

        return True

    def as_dict(self):
        """get information as dict

        Parameters
        ----------
        None

        Returns
        -------
        dict: information of the content 
        """
        hostname = "localhost"
        uuid = self.get_current_uuid()
        dic = {"hostname": hostname,
               "basedir_prefix": self.basedir_prefix,
               "current_dir":  self.get_current_dir(),
               "uuid" : uuid}
        return dic


class StructureNode(DirNode):
    """vasp directory access interface for automatic calculation
    """

    def __init__(self, basedir_prefix, kind="cif"):
        super().__init__(basedir_prefix)

        self.metadata_file = "metadata.json"
        self.structurefile_kind = "cif"
        self.cif_filename = "subs.cif"

    def as_dict(self):
        """get information as dict

        Parameters
        ----------
        None

        Returns
        -------
        dict: information of the content 
        """
        dic = super().as_dict()
        current_dir = self.get_current_dir()

        if False:
            kind = self.structurefile_kind
            if kind == "cif":
                structure_file = os.path.join(current_dir,self.cif_filename)
            elif kind == "poscar":
                structure_file = os.path.join(current_dir,"POSCAR")

            structure = SubsStructure.from_file(structure_file)
            species = structure.element_list()

            dic.update({"positionfile": structure_file,
                         "species": species, "nspecies": len(species)})

        metadata_file = os.path.join(current_dir,self.metadata_file)
        with open(metadata_file) as f:
            d = json.loads(f.read())
            dic.update(d)
 
        return dic

    def place_files(self, structure, source_uuid=None, metadata=None):
        """copy files from source_prefix

        Parameters
        ----------
        source_step : string
            directory full path

        Returns
        -------
        boolean: True if created
                False if not created
        """


        super_place_files = super().place_files()

        if super_place_files:

            targetdir = os.path.join(self.basedir_prefix, self.current_step)
            if source_uuid is not None:
                dic = {"source_uuid": source_uuid}
            else:
                dic = {}
            if metadata is not None:
                dic.update(metadata)

            kind = self.structurefile_kind
            dic.update({"kind": kind})
            if kind == "cif":
                # as cif file
                ciffilename = self.cif_filename
                dic.update({"positionfile": ciffilename})
                cifpath = os.path.join(targetdir, ciffilename)
                cifwriter = CifWriter(structure)
                cifwriter.write_file(cifpath)
                print("write", cifpath)
            else:
                # as POSCAR
                poscarfilename = "POSCAR"
                dic.update({"positionfile": poscarfilename})
                poscarpath = os.path.join(targetdir, poscarfilename)
                poscar = Poscar(structure)
                poscar.write_file(poscarpath)
                print("write", poscarpath)

            species = structure.element_list()
            dic.update({"species": species, "nspecies": len(species)})

            filename = os.path.join(targetdir, self.metadata_file)
            with open(filename, "w") as f:
                f.write(json.dumps(dic))

            return True
        else:
            return False

if False:
    def copy_files_to_calc_directory(souce_prefix, target_base):
        """create basedir_prefix directory
        copy OUTCAR,POSCAR,*cif to basedir_prefix/

        Parameters
        ----------
        source_prefix: string
            directory name to pass glob

        basedir_prefix: string
            base directory name to write

        Returns
        -------
        None

        """

        filelist = list(glob.glob(souce_prefix))

        for filepath in filelist:
            filepath_ce_list = list(glob.glob(os.path.join(filepath, "[CE]_*")))
            if len(filepath_ce_list) > 1:
                print(">1", filepath_ce_list)
                continue
            if len(filepath_ce_list) == 0:
                print("no files", filepath_ce_list)
                raise
            filepath_ce = glob.glob(os.path.join(filepath, "[CE]_*"))[0]
            dirsplits = filepath_ce.split("/")
            basedir_prefix = os.path.join(target_base, dirsplits[3])

            structure_file = glob.glob(os.path.join(filepath_ce,"*.cif"))[0]
            structure = Structure.from_file(structure_file)

            structurenode = StructureNode(basedir_prefix)
            ret = structurenode.place_files(structure)
            print(ret,structure_file)


class SubsStructure(Structure):
    def __init__(self,
                 lattice: Union[List, np.ndarray, Lattice],
                 species: Sequence[Union[str, Element, Specie, DummySpecie, Composition]],
                 coords: Sequence[Sequence[float]],
                 charge: float = None,
                 validate_proximity: bool = False,
                 to_unit_cell: bool = False,
                 coords_are_cartesian: bool = False,
                 site_properties: dict = None):
        super().__init__(
            lattice, species, coords, charge=charge,
            validate_proximity=validate_proximity, to_unit_cell=to_unit_cell,
            coords_are_cartesian=coords_are_cartesian,
            site_properties=site_properties)


    def substitute_elements(self, subs_elems):
        """substitute elements specified by subs_elems

        Parameters
        ----------
        structure: Structure
            Structure object

        subs_elems: a list of a list
            elements to substitute
            e.g., [["Cu","Co"],["Yb","Sm"]:

        Returns
        -------
        Structure: substituted Structure object
        """

        struc_dic = self.as_dict()
        sites = struc_dic["sites"]
        for elem1, elem2 in subs_elems:

            sites2 = []
            for x in sites:
                label = {"label": x["label"]}
                if x["label"] == elem1:
                    label = {"label": elem2}

                specie = x["species"]
                specie2 = []
                for specie0 in specie:
                    if specie0["element"] == elem1:
                        specie0["element"] = elem2
                    specie2.append(specie0)
                specie = specie2

                x.update(label)
                x.update({"species": specie})
                sites2.append(x)

            sites = sites2

        struc_dic["sites"] = sites

        return SubsStructure.from_dict(struc_dic)


    def randomize_structure(self):
        """make new structure with random modification

        Parameters
        ----------
        struc: pymatgen.Struture

        Returns
        -------
        pymatgen.Struture with small ramdon modification
        """

        def make_new_lattice(lattice):
            """make new lattice with small modification

            Parameters
            ----------
            lattice : Structure.lattice

            Returns
            -------
            Structure.lattice
                new structure with small modification
            """
            afac = 0.1
            alphafac = 2

            r = np.random.rand(6)
            a = lattice.a + r[0] * afac
            b = lattice.b + r[1] * afac
            c = lattice.c + r[2] * afac
            alpha = lattice.alpha + r[3] * alphafac
            beta = lattice.beta + r[4] * alphafac
            gamma = lattice.gamma + r[5] * alphafac

            new_lattice = Lattice.from_parameters(a, b, c, alpha, beta, gamma)
            return new_lattice


        def make_new_frac_coors(frac_coords):
            """ make new frac coord with small modification

            Parameters
            ----------
            frac_coords : np.array, Structure.frac_coords

            Returns
            -------
            np.array
                frac coord with small modification
            """
            fac = 0.01
            rr = np.random.rand(frac_coords.shape[0], frac_coords.shape[1]) * fac
            rr[0, :] = [0, 0, 0]
            rr
            new_frac_coords = frac_coords - rr
            return new_frac_coords


        new_lattice = make_new_lattice(self.lattice)
        new_frac_coords = make_new_frac_coors(self.frac_coords)
        newstruc = SubsStructure(lattice=new_lattice, species=self.species,
                                 coords=new_frac_coords, coords_are_cartesian=False)
        return newstruc


    def element_list(self):
        """make species of material

        Parameters
        ----------
        structure: pymatgen.Structure
            material structure

        Returns
        -------
        species: dict (Structure.species)
        """
        counter = Counter(self.species)
        elementlist = []
        for x in counter:
            elementlist.append([str(x), counter[x]])
        return elementlist
