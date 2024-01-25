# Description
N-STRUCT is a Python-based database tool automating the minimization of redudancy for data structures.

# Features
This section is separated into Core and Additional sections.

Core features are required for N-STRUCT to be a functional tool.

Additional features provide QOL to users.

## Core
- **File I/O**: Allows reading and writing string and byte data to disk.
- **Database**: Utilizes a structured database system to store and manage data on the disk. All of the information in the database is contained in a single Structure Database File (SDB).
- **Catalogue**: Automation which minimizes redudancy in the Database. Refer to the Cataloguing section below for more information.

### Cataloguing
Newly stored data is judged for redundancy by structure and content. If the content of the data does not already exist in the database, meaning there are no existing structures which can be combined to represent the content, it is assigned a new structure ID. Otherwise, the content will be replaced by a set of structure IDs in a tree-like fashion. Some structures contain other structures, some may only contain data, but all structures in the database correspond to an ID.

## Additional
- **Error Handling**: The tool has built-in error handling to catch and report errors during execution.
- **Settings**: The tool can load and save settings from an .ini file.
- **Operations**: The tool can perform operations on data in memory. Currently supported operations include refining, simplifying, and converting data to other types.

## Usage
To use N-STRUCT, you need to create an instance of the `Manager` class. This class initializes the settings, database, and catalogue. Once initialized, you can use the methods provided by these classes to interact with the tool.

For more detailed usage instructions, please refer to the individual documentation for each class.