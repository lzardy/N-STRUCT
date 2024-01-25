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
- **Catalogue**: Automation which minimizes redudancy in the Database. Refer to the Cataloguing section below for more information.

### Cataloguing
Newly stored data is judged for redundancy by structure and content. If the content of the data does not already exist in the database, meaning there are no existing structures which can be combined to represent the content, it is assigned a new structure ID. Otherwise, the content will be replaced by a set of structure IDs in a tree-like fashion. Some structures contain other structures, some may only contain data, but all structures in the database correspond to an ID.

## Extras
- **Error Handling**: The tool has built-in error handling to catch and report errors during execution.
- **Settings**: The tool can load and save settings from an .ini file.
- **Operations**: The tool can perform operations on data in memory. Currently supported operations include refining, simplifying, and converting data to other types.

## Usage
To use N-STRUCT, you need to create an instance of the `Manager` class. This class initializes the settings, database, and catalogue. Once initialized, you can use the methods provided by these classes to interact with the tool.

For more detailed usage instructions, please refer to the individual documentation for each class.