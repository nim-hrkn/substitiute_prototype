# substitute_prototype

This software includes the work that is distributed in the Apache License 2.0.


# Basic Design

## Real and virtual bodies

The implementation uses a file and a database (mongoDB).
The file is the entity and the information on the database is the virtual body for speeding up the process.
To put an entity in the database, it is implemented so that the entity is placed in a file and the content (entity) of the file is read into the database once.

The purpose of this is to enable reconstruction of results from files even if the database is destroyed and even if the database is not used.

## Directory to place the structure
The files are placed in the directory specified in the baseir for each substance.
directories and subdirectories have a name and an id.

The substance is stored on the filesystem in a subdirectory under the baseir/.
SCF, etc. many times, and a different subdirectory is created to store the results in a different subdirectory.

basedir/{id1name} -> basedir/{id2name} -> basedir/{id3name}

and the history proceeds. (Each id?name has an id?name.)

## metadata in the directory
The metadata in the basedir contains descriptive information about the subdirectory currently being used.
The metadata of the subdirectory has descriptive information about the subdirectory.

When the user specifies a directory in the baseir, the user gets the current subdirectory position specified in the baseir's metadata, and then accesses the structure, etc. from that subdirectory.

## elements of basedir
basedir must have the following files.

* basedir/_uuid: uuid of basedir

The id will not be overwritten.

* basedir/metadata.json: metadata of basedir

The metadata has the current directory information of the baseir.

* basedir/{idname}: basedir subdirectory

The first idname (not the same as the id) is defined as 0.

## basedir/{id} elements
basedir/{idname} must have the following files.
* basedir/{idname}/_uuid: id of basedir/{idname}

The id will not be overwritten.

* basedir/{idname}/metadata.json: metadata of basedir/{idname}

The metadata in {basedir/{idname} has the id of the source structure of the current structure.
The id of the source structure should be the id of another basedir.

### The elements of the metadata
The metadata in basedir/{idname} has
* purpose
* its achievement.

### Description of purpose and achievement

The following is a description of the achievement of each objective.

#### in the case of "purpose"=="prototype"

The subdirectory has a structure that has been optimized by something, such as experimental values or structural optimization.

It has a combination of the following.

{"purpose": "prototype", "achievement": "completed"}


#### in the case of "purpose"=="converged_ionic"

It shows that a structure with a subdirectory performs structural optimization.

##### Definition of Achievement
It has the following achievement states.

1. "achievement": "to_relax"

It indicates the state that we are about to perform structural optimization. It has a structure file only.

The state transition from
{"purpose": "prototype", "achievement": "completed"} to
{"purpose": "converged_ionic", "achievement": "to_relax"}


2. "achievement": "running"

It shows the state in which the structural optimization program input is created and the structural optimization program is being executed.

3. "achievement": "executed"

It indicates that the structural optimization program has been completed.

4. "achievement", "completed"

It indicates that structural optimization has been completed.

##### Transition of achievement state

1. -> 2. -> 3. -> (1. or 4.)


# Sample Description

Search by purpose and achievement and operate on the substance in the corresponding state. do. In the process, the state is changed.

We do not have an implementation for sequential programming languages.
We implemented it assuming parallel methods such as tuple space, but it can be converted to sequence flowcharts.

## initial structure creation process

A database is also used in the following process.

### 20_add_fake_data.py

Increasing material by copying it from another directory and substituting elements.
Element-substituted materials are not structure-optimized because they are only generated for test data.
The state is changed to {"purpose": "prototype", "achievement": " completed"} and put it in the database.

### 30_generate_subs.py
Replace elements in materials in {"purpose": "prototype", "achievement": " completed"} and place them in different baseir.
The status of the subdirectory is changed to
{"purpose": "converged_ionic", "achievement": "to_relax"}


## structural optimization process
Material used below has entities under the directory specified by "basedir".
It changes {"purpose": "converged_ionic", "achievement". ":?? } to describe the state.
If you want to implement a different purpose, change the purpose. (Change the subdirectory as well.)

### 40_fakevasprun.py

To check the operation.
Create vasp inputs and execute them virtually for a substance that is
{"purpose": "converged_ionic", "achievement": "to_relax"}.

Virtual means that it is not executed, but instead it changes
{"purpose": "converged_ionic", "achievement": "running"} in a metadata of the subdirectory.



### 50_fakevaspresult.py
For materials,
{"purpose": "converged_ionic", "achievement": "running"}
virtually it changes the state to
{"purpose": "converged_ionic", "achievement": "executed"}

It also randomly produces a result (whether or not converged_ionic was achieved)
in the file.

### 60_retieve_vaspresult.py
For materials,
{"purpose": "converged_ionic", "achievement": "executed"},
it changes  "achievement": "completed" if converged_ionic is fulfilled.
it changes "achievement": "to_relax" if not.

If there are any material left in the "achievement": "to_relax" again 40_fakevasprun.py must be run.

## DB View and Delete

### 90_show_db.py

Displays the contents of the database.

### 95_remove_collection.py

Removal of the collection.


# Execution example

Run it under sample/ directory.

## 20_add_fake_data.py
```
$ python 20_add_fake_data.py
initial database size 71
subsitute elements [['Fe', 'Cu']]
3 directories are created.
subsitute elements [['Ni', 'Cu']]
/home/kino/anaconda3/lib/python3.7/site-packages/pymatgen/io/cif.py:1099: UserWarning: Issues encountered while parsing CIF: Some fractional co-ordinates rounded to ideal values to avoid issues with finite precision.
  warnings.warn("Issues encountered while parsing CIF: %s" % "\n".join(self.warnings))
7 directories are created.
subsitute elements [['Cu', 'Co']]
5 directories are created.
subsitute elements [['Zn', 'Cu']]
6 directories are created.
subsitute elements [['Gd', 'Y']]
19 directories are created.
subsitute elements [['Yb', 'Y']]
34 directories are created.
total 74 directories are created.
final database size 145
```

## 30_generate_subs.py
```
$ python 30_generate_subs.py
substitute elements [['Cu', 'Fe']]
new_basedir /home/kino/tmp/substitute_prototype/Calc/MGI/mp-21305_GdNi5,Ni_Cu,Cu_Fe
new_basedir /home/kino/tmp/substitute_prototype/Calc/MGI/mp-542437_Gd2Zn17,Zn_Cu,Cu_Fe
...
new_basedir /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1261_EuZn,Zn_Cu,Cu_Co
database size 220
75 data to relax
```
## 40_fakevasprun.py
```
$ python 40_fakevasprun.py
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-21305_GdNi5,Ni_Cu,Cu_Fe
/home/kino/anaconda3/lib/python3.7/site-packages/pymatgen/io/vasp/sets.py:418: BadInputSetWarning: Relaxation of likely metal with ISMEAR < 1 detected. Please see VASP recommendations on ISMEAR for metals.
  "ISMEAR for metals.", BadInputSetWarning)
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-542437_Gd2Zn17,Zn_Cu,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-657_YbZn2,Zn_Cu,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-567538_YbCu2,Yb_Y,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-580354_CeNi3,Ni_Cu,Cu_Fe
...
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-581942_CeCu6,Cu_Co
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1261_EuZn,Zn_Cu,Cu_Co
75 running
```
## 50_fakevaspresult.py
```
$ python 50_fakevaspresult.py
Counter({True: 58, False: 17}) True if converged
75 executed
```

## 60_retieve_vaspresult.py
```
$ python 60_retieve_vaspresult.py
75 data processed.
Counter({'completed': 58, 'to_relax': 17})
```

## 40_fakevasprun.py
```
$ python 40_fakevasprun.py
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-22311_EuNi5,Ni_Cu,Cu_Fe
/home/kino/anaconda3/lib/python3.7/site-packages/pymatgen/io/vasp/sets.py:418: BadInputSetWarning: Relaxation of likely metal with ISMEAR < 1 detected. Please see VASP recommendations on ISMEAR for metals.
  "ISMEAR for metals.", BadInputSetWarning)
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-614455_GdCu,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-636253_GdCu5,Gd_Y,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-567538_YbCu2,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1703_YbZn,Zn_Cu,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-567538_YbCu2,Yb_Y,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-581734_Gd2Fe17,Fe_Cu,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-22311_EuNi5,Ni_Cu,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-20089_GdFe2,Fe_Cu,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1607_YbCu5,Yb_Y,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-2645_YbNi5,Ni_Cu,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1665_YbFe2,Fe_Cu,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-21305_GdNi5,Ni_Cu,Cu_Co
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-567538_YbCu2,Cu_Co
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1703_YbZn,Zn_Cu,Cu_Co
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-636253_GdCu5,Cu_Co
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-581942_CeCu6,Cu_Co
17 running
```

## 50_fakevaspresult.py
```
$ python 50_fakevaspresult.py
Counter({True: 15, False: 2}) True if converged
17 executed
```

## 60_retieve_vaspresult.py
```
$ python 60_retieve_vaspresult.py
17 data processed.
Counter({'completed': 15, 'to_relax': 2})
```

## 40_fakevasprun.py
```
$ python 40_fakevasprun.py
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-20089_GdFe2,Fe_Cu,Cu_Ni
/home/kino/anaconda3/lib/python3.7/site-packages/pymatgen/io/vasp/sets.py:418: BadInputSetWarning: Relaxation of likely metal with ISMEAR < 1 detected. Please see VASP recommendations on ISMEAR for metals.
  "ISMEAR for metals.", BadInputSetWarning)
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-636253_GdCu5,Cu_Co
2 running
```

## 50_fakevaspresult.py
```
$ python 50_fakevaspresult.py
Counter({True: 2}) True if converged
2 executed
```

## 60_retieve_vaspresult.py
```
$ python 60_retieve_vaspresult.py
2 data processed.
Counter({'completed': 2})
```

## 90_show_collection.py
```
$ python 90_show_collection.py
[['all', 220], ['to_relax', 0], ['running', 0], ['executed', 0], ['completed', 220]]
```
