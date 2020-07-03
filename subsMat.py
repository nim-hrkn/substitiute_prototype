#!/usr/bin/env python
# coding: utf-8

import copy
import glob
import json
import numpy as np
import os
import re
import uuid
from pathlib import Path
from typing import Union, List, Sequence
from collections import Counter

from monty.io import reverse_readfile

from pymatgen.core.composition import Composition
from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure
from pymatgen.io.vasp.inputs import Poscar
from pymatgen.io.cif import CifWriter
from pymatgen.core.periodic_table import Element, Specie, DummySpecie

from pymongo import MongoClient


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
    """database access library

    You can use .collection to access the DB directly.

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

        the same as collection.remove()

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

        also add element columns using elementListExpansion class

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

    def delete_one(self, filterstring):
        """delete DB by filter

        the same as collecton.delete_one()

        Parameters
        ----------
        filterstring: dic
            filter to pass collection.delete_one()

        Returns
        -------
            return value of collection.delete_one()
        """
        return self.collection.delete_one(filterstring)

    def subs_elem_query_sentence(self, subs_elm):
        """make query from sub_elm

        It uses element columns. 

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

    def count_documents(self, query=None):
        """count_documents by collection.count_documents(query)

        Parameters
        ----------
        query: dict
            filter dict

        Returns
        -------
        number of documents = collection.count_documents(query)
        """
        if query is None:
            query = {}
        return self.collection.count_documents(query)

    def find(self, query):
        """find with query by collection.find(query)


        Parameters
        ----------
        query: query sentence for find()
        """
        return self.collection.find(query)

    def find_subs_elems(self, subs_elm):
        """find with materials by subs_elm

        It uses self.subs_elem_query_sentence(subs_elm).

        Parameters
        ----------
        subs_elm: a list of elements to substitiute

        Returns
        -------
        collection.find() result
        """
        query_sentence = self.subs_elem_query_sentence(subs_elm)
        query_sentence.update({"achievement": "completed"})
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

        It uses self.add_files_under().

        Parameters
        ----------
        location: string
            directory name to pass glob.glob

        wrapperclass: class
            a class to load information
            must has .as_dict() to save into the database

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
    """make string from subs_elm list

    It may be usd as postfix.

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


    basedir has subdirectories inside as basedir/{id}.

    basedir has uuid.
    subdir has another uuid.

    metadata contains information on the current directory.

    self.place_files() creats subdirectory if basedir/{id} doesn't exist. 

    """

    def __init__(self, basedir, hostname="localhost",
                 metadata_file="metadata.json", uuid_file="_uuid"):
        """initialize dir_node

        Parameters
        ----------
        basedir: base file path

        hostname: hostname

        create: boolean
            create the first directores or not
        """
        self.__basedir = basedir
        if not os.path.isdir(basedir):
            os.makedirs(basedir)
        self.__metadata_file = metadata_file
        self.__uuid_file = uuid_file
        self.__current_step = self.read_current_step()

        if not os.path.isdir(self.__basedir):
            os.makedirs(self.__basedir)
        self.save_basedir_uuid()

    def set_new_step(self, new_step=None):
        """set new current_step

        Parameters
        ----------
        new_step: string
            new current_step

        Returns
        -------
        None
        """
        if new_step is None:
            new_step = str(uuid.uuid4())
        self.__current_step = new_step

    def read_current_step(self):
        """return current_step

        read_*() members read information from the file on demand.

        Parameters
        ----------
        None

        Returns
        -------
        current_step : string
            directory name
        """
        filename = os.path.join(self.__basedir,
                                self.__metadata_file)
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

    def get_currentdir(self):
        """get current directory full path

        get_*() members make information from variables of the class.

        Parameters
        ----------
        None

        Returns
        -------
        targetdir: string
            taret directory name with current step

        """
        targetdir = os.path.join(self.__basedir, self.__current_step)
        return targetdir

    def read_currentdir_uuid(self):
        """reuturn uuid of the current_step

        Parameters
        ----------
        None

        Returns
        -------
        uuid: string
            UUID
        """
        filename = os.path.join(self.get_currentdir(),
                                self.__uuid_file)
        uuid = None
        with open(filename) as f:
            uuid = f.read()
        return uuid

    def save_basedir_metadata_file(self):
        """save basedir metadata file

        Parameters
        ----------
        None

        Returns
        -------
        True
        """
        filename = os.path.join(self.__basedir,
                                self.__metadata_file)
        status = {"current_step": self.__current_step}
        with open(filename, "w") as f:
            f.write(json.dumps(status))
        return True

    def save_basedir_uuid(self):
        """save basedir uuid
        create it only once.

        Parameters
        ----------
        None

        Returns
        -------
        boolean:
            True if newly created
            False if already existed
        """

        filename = os.path.join(self.__basedir,
                                self.__uuid_file)
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                f.write(str(uuid.uuid4()))
            return True
        else:
            return False

    def save_currentdir_uuid(self, uuidstr=None):
        """save current directory uuid
        create it only once.

        Paremeters
        ----------
        uuidstr: string (default: None)
            uuid

        Returns
        -------
        boolean:
            True if newly created
            False if already existed
        """
        # current UUID
        if uuidstr is None:
            uuidstr = str(uuid.uuid4())
        targetdir = self.get_currentdir()
        filename = os.path.join(targetdir, self.__uuid_file)
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                f.write(uuidstr)
            return True
        else:
            return False

    def place_files(self):
        """place files on the current subdirectory.

        als make the new step, and the new subdirectory when the actual body doesn't exisst

        Parameters
        ----------
        current_step: directory name in self.basedir_prefix

        Returns
        -------
        boolean: always True
        """

        targetdir = self.get_currentdir()
        # make directory if not exist
        if os.path.isdir(targetdir):
            # make new directory
            # save old uuid and step
            # old_uuid = self.read_currentdir_uuid()
            # old_step = self.__current_step
            # make new uuid and step
            currentdir_uuid = str(uuid.uuid4())
            self.set_new_step(currentdir_uuid)
            targetdir = self.get_currentdir()
            os.makedirs(targetdir)
            self.save_currentdir_uuid(currentdir_uuid)
        else:
            os.makedirs(targetdir)
            self.save_currentdir_uuid()
        self.save_basedir_metadata_file()

        return True

    def as_dict(self):
        """get information as dict

        it is used to save them into metadatafile.

        Parameters
        ----------
        None

        Returns
        -------
        dict: information of the content
        """
        hostname = "localhost"
        uuid = self.read_currentdir_uuid()
        dic = {"hostname": hostname,
               "basedir": self.__basedir,
               "uuid": uuid}
        return dic


def element_list(species):
    """make species of material

    helper subroutine

    Parameters
    ----------
    species: a list of atomic species
        material species

    Returns
    -------
    species: dict (Structure.species)
    """
    counter = Counter(species)
    elementlist = []
    for x in counter:
        elementlist.append([str(x), counter[x]])
    return elementlist


class StructureNode(DirNode):
    """vasp directory access interface
    """

    def __init__(self, basedir_prefix, kind="cif"):
        super().__init__(basedir_prefix)

        self.metadata_file = "metadata.json"
        self.structurefile_kind = "cif"
        self.cif_filename = "subs.cif"

    def as_dict(self):
        """get information as dict

        It is used to save them into the metadata file.

        Parameters
        ----------
        None

        Returns
        -------
        dict: information of the content
        """
        dic = super().as_dict()
        current_dir = self.get_currentdir()

        if False:
            kind = self.structurefile_kind
            if kind == "cif":
                structure_file = os.path.join(current_dir, self.cif_filename)
            elif kind == "poscar":
                structure_file = os.path.join(current_dir, "POSCAR")

            structure = SubsStructure.from_file(structure_file)
            species = structure.element_list()

            dic.update({"positionfile": structure_file,
                        "species": species, "nspecies": len(species)})

        metadata_file = os.path.join(current_dir, self.metadata_file)
        with open(metadata_file) as f:
            d = json.loads(f.read())
            dic.update(d)

        return dic

    def save_currentdir_metadata(self, dic):
        """save dic into the currentdir metadata file

        Parameters
        ----------
        dic: dict
            dictionary to save

        Returns
        -------
        None

        """
        targetdir = self.get_currentdir()
        filename = os.path.join(targetdir, self.metadata_file)
        with open(filename, "w") as f:
            f.write(json.dumps(dic))

    def load_currentdir_metadata(self):
        """load currentdir metadata file

        Parameters
        ----------
        None

        Returns
        -------
        dict: the content of the metadata file

        """
        targetdir = self.get_currentdir()
        filename = os.path.join(targetdir, self.metadata_file)
        with open(filename) as f:
            dic = json.loads(f.read())
        return dic

    def update_currentdir_metadata(self, dic):
        """update currentdir metadata file

        Parameters
        ----------
        dic: dict
            dictionary to add

        Returns
        -------
        dict
        """
        d = self.load_currentdir_metadata()
        d.update(dic)
        self.save_currentdir_metadata(d)
        return d

    def place_files(self, structure, source_uuid=None, metadata=None):
        """place files

        Parameters
        ----------
        structure: pymatgen.structure
            material structure
        source_uuid : string
            uuid file
        metadata: dic
            metadata to add

        Returns
        -------
        boolean: True if created
                 False if not created
        """

        super_place_files = super().place_files()

        if super_place_files:

            targetdir = self.get_currentdir()
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
            else:
                # as POSCAR
                poscarfilename = "POSCAR"
                dic.update({"positionfile": poscarfilename})
                poscarpath = os.path.join(targetdir, poscarfilename)
                poscar = Poscar(structure)
                poscar.write_file(poscarpath)

            species = element_list(structure.species)
            dic.update({"species": species, "nspecies": len(species)})
            self.save_currentdir_metadata(dic)
            return True
        else:
            return False


class SubsStructure(Structure):
    """Another pymatgen.Structure class for element substitution
    """
    def __init__(self,
                 lattice: Union[List, np.ndarray, Lattice],
                 species: Sequence[Union[str, Element, Specie,
                                   DummySpecie, Composition]],
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

        def make_new_lattice(lattice, afac=0.1, alphafac=2):
            """make new lattice with small modification

            Parameters
            ----------
            lattice: Structure.lattice
                lattice information
            afac: float
                a factor for lattice length modification
            alphafac: float
                a factor for lattice angle modification

            Returns
            -------
            Structure.lattice
                new structure with small modification
            """

            r = np.random.rand(6)
            a = lattice.a + r[0] * afac
            b = lattice.b + r[1] * afac
            c = lattice.c + r[2] * afac
            alpha = lattice.alpha + r[3] * alphafac
            beta = lattice.beta + r[4] * alphafac
            gamma = lattice.gamma + r[5] * alphafac

            new_lattice = Lattice.from_parameters(a, b, c, alpha, beta, gamma)
            return new_lattice

        def make_new_frac_coors(frac_coords, fac=0.01):
            """ make new frac coord with small modification

            Parameters
            ----------
            frac_coords : np.array, Structure.frac_coords
                atomic posiiton

            fac: float
                factor for random displacement.

            Returns
            -------
            np.array
                frac coord with small modification
            """
            rr = np.random.rand(frac_coords.shape[0],
                                frac_coords.shape[1]) * fac
            rr[0, :] = [0, 0, 0]
            new_frac_coords = frac_coords - rr
            return new_frac_coords

        new_lattice = make_new_lattice(self.lattice)
        new_frac_coords = make_new_frac_coors(self.frac_coords)
        newstruc = SubsStructure(lattice=new_lattice, species=self.species,
                                 coords=new_frac_coords,
                                 coords_are_cartesian=False)
        return newstruc

    def element_list(self):
        """make species of material

        call external element_list()

        Parameters
        ----------
        structure: pymatgen.Structure
            material structure

        Returns
        -------
        species: dict (Structure.species)
        """
        return element_list(self.species)
