#!/usr/bin/env python
# coding: utf-8

import copy
import glob
import os
from pathlib import Path

from pymongo import MongoClient


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


class SubsMaterialsDatabase(object):
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
