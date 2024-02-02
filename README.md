# Description
N-STRUCT is a Python-based database tool automating the minimization of redudancy for data structures.

In simpler terms, any object that exists, we treat as a collection of less complex objects. We do this only by reference, thereby saving on resource usage when using the complex objects. All objects are synonymous with blueprints, things that describe how to build the object piece by piece.

# Features
This section is separated into two sections: **Core** and **Extras**. Each section is just a set of features N-STRUCT offers.

Core features are required for N-STRUCT to be a functional tool, like how a computer is required to run computer programs.

Extra features provide QOL to users. These could end up being customizable addons in the future, time will tell.

## Core
- **File I/O**: Allows reading and writing string and byte data to disk.
- **Database**: Utilizes a structured database system to store and manage data on the disk. All of the information in the database is contained in a single Structure Database File (SDB).
- **Catalog**: Automation which minimizes redudancy in the Database. Refer to the Cataloguing section below for more information.

### Cataloguing
Newly stored data is judged for redundancy by structure and content. If the content of the data does not already exist in the database, meaning there are no existing structures which can be combined to represent the content, it is appended to the database and assigned a new structure ID (ID is just the index in the database). Otherwise, it is still appended and given a new structure ID, but the content will then be replaced by a set of existing structure IDs (sub-structures). Structures can contain sub-structures, structures may only contain data, but all structures in the database must correspond to an ID.

#### **KEY NOTE**:
Structures comprised of sub-structures only show as being comprised of the highest level existing structures, rather than the full hierarchy of sub-structures from highest to lowest complexity. The full tree of sub-structures can only be known by referencing them individually. This too, is meant to save on resources, specifically for cataloguing new structures being added to the database.

## Extras
- **Manager**: The tool provides a system for users to interact with core systems.
- **Error Handling**: The tool has built-in error handling to catch and report errors during execution.
- **Settings**: The tool can load and save settings from an .ini file.
- **Operations**: The tool can perform operations on data in memory. Currently supported operations include refining, simplifying, and converting data to other types.

## Usage
To use N-STRUCT, you can run these commands:
1. Install
```
pip install -r requirements.txt
```
2. Run
```
python manager.py <file path> <auto catalog>
```

For more detailed usage instructions, please refer to the individual documentation for each class.
