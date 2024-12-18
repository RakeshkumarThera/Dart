# Copyright (c) 2016, Teradata, Inc.  All rights reserved.
# Teradata Confidential
#
# Primary owner: Mark.Gilkey@Teradata.com
# Secondary owner:
#


"""
PURPOSE:
    Given a list of names (e.g. file names), of which N-1 exist,
    rename the items in a "rotation" pattern.
    E.g. suppose that we have a list of file names:
        file1
        file2
        file3
    and suppose that currently file1 and file3 exist.  We will:
        rename file1 to file2
        rename file3 to file1
    An example of when you'd want to use this is when rotating among
    different serviceports.json files (with different port numbers).

    Although usually N - 1 of the named items will exist, this code
        actually works for the range 2 to N-1; i.e. if at least 2,
        and no more than N-1, of the names exist, this will work.
    Although this is intended for files, I've generalized it so that
        it should work for any type of item as long as you can write:
        a) an "exists()" function (which must return True if there is an
           item, such as a file, with this name).  For files, the "exists()"
           function is merely os.path.exists().
        b) a "rename()" function, which will rename the item from the
           current ("old") name to the new name.  For files, the "rename"
           function is merely os.rename().
WARNINGS:
    1) If the "exists()" function is "expensive", this code is inefficient
       because it checks the existence of each item more than once.
    2) This function is not atomic, so:
    2A) It will probably behave badly if anyone else is adding, renaming,
       or deleting items with the names we are processing.
    2B) It could behave badly if interrupted at the wrong time.
"""


import os.path


def count(name_list, exists_func):
    """
    PURPOSE:
       Return the number of elements in the name_list that actually exist.
    INPUTS:
       name_list: a list of names (e.g. file names) of items that might exist
          (i.e. some files might exist and some might not)
       exists_func: This is a function (e.g. os.path.exists()) that will tell
          us whether an item (e.g. file) with this name exists.
    RETURNS:
       Returns the number of elements in the name_list that actually exist.
    """
    num_names = len(name_list)
    num_items = 0
    for i in range(0, num_names):
        name = name_list[i]
        if exists_func(name):
            num_items += 1
    return num_items


def find_first_hole(name_list, exists_func):
    """
    PURPOSE:
       Given a list of objects that might exist, return the first one
       that does NOT exist.  Returns -1 if they all exist.
    INPUTS:
       name_list: a list of names (e.g. file names) of items that might exist
          (i.e. some files might exist and some might not).
       exists_func: This is a function (e.g. os.path.exists()) that will tell
          us whether an item with this name exists.
    """
    num_items = len(name_list)
    i = 0
    while i < num_items:
        name = name_list[i]
        if not exists_func(name):
            return i
        i += 1

    return -1


def rotate(name_list, exists_func, rename_func):

    """
    PURPOSE:
        Given a list of names (e.g. file names), of which N-1 must exist,
        rename in a "rotation" pattern.
        E.g. suppose that we have a list of file names:
            file1
            file2
            file3
        and suppose that currently file1 and file3 exist.  We will:
            rename file1 to file2
            rename file3 to file1
        An example of when you'd want to use this is when rotating among
        different serviceports.json files (with different port numbers).
    INPUTS:
        name_list: The list (or tuple) of file names. Again, N-1 should exist.
        exists_func: A function that tells you whether a specified name
            exists, e.g. whether there is a file with this name.  For example,
            you could pass os.path.exists() to see whether a file exists.
        rename_func: A function that will change the name from the
            old/current name to the new name.
            For example, you could pass os.rename() to rename a file.
    RETURNS:
        Currently, this doesn't return anything.  It will raise an
        exception if it detects an error.
    WARNINGS:
        See the module-level warnings.
    """

    # The number of item (e.g. file) NAMES.
    name_count = len(name_list)

    # The number of items that EXIST.
    item_count = count(name_list, exists_func)
    if item_count < 2 or item_count > name_count - 1:
        msg = "rotate(): Number of existing items must be >=2 and <= all."
        raise Exception(msg)

    # This is the index/slotNumber of the item (file) that does NOT exist.
    hole_index = find_first_hole(name_list, exists_func)

    #print "DDDIAGNOSTIC: name_count, item_count, empty slot"
    #print name_count, item_count, hole_index

    # Rotate the files, assuming that hole_index is the array index
    # of the "hole" (e.g. in the example above, if file2 does not exist
    # then hole_index = 1 (second slot)),
    i = 0
    while i < name_count - 1:
        new_name_index = hole_index
        old_name_index = new_name_index - 1
        if old_name_index == -1:
            old_name_index = name_count - 1     # wrap around
        old_name = name_list[old_name_index]
        new_name = name_list[new_name_index]
        if exists_func(old_name):
            rename_func(old_name, new_name)
        # Keep track of where the "hole" is now.
        hole_index = old_name_index
        i += 1


def partial_rotation_test():

    """
    PURPOSE:
        This is a quick sanity test of the "rotate" function.
    """

    file_name_list = ("a", "b", "c", "d", "e")
    # Note that we are passing the FUNCTIONS os.path.exists() and os.rename(),
    # which we will call from inside the rotate() function.
    rotate(file_name_list, os.path.exists, os.rename)

    # !!! This doesn't verify the output.  You can do that manually by doing
    # the following
    #    touch a b c
    # and then repeatedly running the following pair of commands:
    #    python rotate.py ; ls a b c d
    # You should see a sequence like:
    #    a b c
    #    b c d
    #    c d a
    #    d a b
    #    a b c



# ----------------------------------------------------------------------------
if __name__ == '__main__':
    partial_rotation_test()

