# Description
N-STRUCT is a Python-based database tool which can identify and minimize redundancy in data.

In more specific terms, we find how bits and bytes relate in some segment of data, then perform abstraction to represent the segment as a single structure. By saving these abstractions in a database, we can represent the original data (or any similar data) by references instead of bits and bytes, saving resources.

This project is the foundation for a suite of tools, using the abstractions saved here to more easily act on the higher level features of data. In other words, it is the stage of learning where knowledge is crystalized.

# Features

## Core
These features are required, and together they accomplish the goal of minimizing redundancy.

- **File I/O**: Allows reading and writing string and byte data to disk.
- **Database**: Utilizes a structured database system to store and manage data on the disk. The information in the database is saved as Structure Database Files (SDB).
- **Catalog**: . Refer to the Cataloguing section below for more information.

## Extras
These features provide QOL to users. These could end up being customizable addons in the future, time will tell.

### Cataloguing
Data runs through three processes before being sent to the database:
1. Judging
2. Abstracting
3. Blueprinting

#### **Judging**
Here, the data gets compared to the database.
- If it matches 1:1 to a blueprint in the database, we skip to **Blueprinting**
- Otherwise, we try replacing segments in the data with matching structures in the database
- Any data left over, means we move to **Abstracting**

#### **Abstracting** (WIP)
This is the current **Work in Progress** phase of the project, and what is stated here is fairly contentious and could change at any time.

Currently, the idea is to construct a map of relationships in the data. Each data point (bit/byte/segment/etc) has a relationship with every other data point in an entire dataset.

To do so, we need a rigorously defined set of parameters which define what a "relationship" is.
1. **Appearance** - How a data point "looks", bit/byte/sequence/etc, what it is composed of
2. **Frequency** - How often a data point appears with respect to some dataset
3. **Relativity** - Where the data point is with respect to other data points, including data points with the same appearance
4. **Others?** - More than likely, these will all be contextual

The first three parameters are simple and general and (as of writing) not enough time has been spent to find other obviously simple parameters (this is effectively a human gradient descent prior).


#### **Blueprinting**
The final data abstractions are packaged into a single file called a "Blueprint". The previous steps replaced individual bits and bytes with known concepts, relations, and patterns. Thus, when those concepts are linked together, they form a single coherent and unique object.

We then save the object to the database, and now we can use what we've learned from the catalogued file, to catalog other files.

## Extras
#### **Error Handling**
The tool has built-in error handling to catch and report errors during execution.
#### **Settings**
The tool can load and save settings from an .ini file.
#### **Operations**
The tool should support operations on data in memory. Currently, there are no operations implemented.

## Usage
To use N-STRUCT, you can run these commands:
1. Install
```
pip install -r requirements.txt
```
2. Run
```
python manager.py <file path>
```

For more detailed usage instructions (developers), please refer to the individual documentation for each class.

## TODO
- Support refine, simplify, and convert operations.
- Segment the codebase to match the cataloguing process.