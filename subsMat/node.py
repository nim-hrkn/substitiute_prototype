#!/usr/bin/env python
# coding: utf-8

import json
import os
import uuid

from pymatgen.io.vasp.inputs import Poscar
from pymatgen.io.cif import CifWriter

from .misc import element_list
from .structure import SubsStructure


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

        als make the new step, and the new subdirectory
        when the actual body doesn't exist

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
