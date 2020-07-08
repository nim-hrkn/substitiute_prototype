#!/usr/bin/env python
# coding: utf-8

import numpy as np
from typing import Union, List, Sequence

from pymatgen.core.composition import Composition
from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure
from pymatgen.core.periodic_table import Element, Specie, DummySpecie

from .misc import element_list


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
