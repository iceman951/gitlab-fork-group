#!/usr/bin/env python3.7
"""GitLab Group Fork - Fork and entire group of projects in a tree to another namespace"""

import sys
import os
import argparse
import logging
import gitlab
from treelib import Tree

def main():
    """Main Function"""
    logging.basicConfig(level=logging.DEBUG)
    options = parse_cli()
    glab = gitlab.Gitlab(options.url, options.token)
    read_src_group(glab, options.srcGroup)


def parse_cli():
    """Parse CLI Options and return, fail on no valid token"""
    logging.debug('parse_cli: Parsing CLI Arguments')
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--url",
                        dest="url",
                        default="https://gitlab.com",
                        help="base URL of the GitLab instance")

    parser.add_argument("-t", "--token",
                        dest="token",
                        default='',
                        help="API token")

    parser.add_argument("srcGroup", help="Source namespace to copy")

    parser.add_argument("destGroup", help="Destination namespace to create")

    options = parser.parse_args()

    if options.token == "":
        logging.debug('parse_cli: Did not find token in cli options')
        if os.getenv("GITLAB_TOKEN") is not None:
            logging.debug('parse_cli: Found token in system environment variable GITLAB_TOKEN')
            options.token = os.getenv("GITLAB_TOKEN")
        else:
            logging.debug('parse_cli: Did not find token in environment variable, quitting')
            print("API Token Required - Not found in options or environment variables")
            sys.exit(1)
    return options

def read_src_group(gl, src):
    """Read source group tree from gitlab server"""
    logging.info("Attemping to read source group '%s/%s'", gl.url, src)
    src_group_tree = Tree()
    top_level_group = gl.groups.get(src, include_subgroups=True)
    src_group_tree.create_node(top_level_group.path, top_level_group.id, data=top_level_group.name)
    def get_sub_groups(parent):
        logging.debug('Looking for sub-groups in %s', parent.full_path)
        new_top = gl.groups.get(parent.full_path, include_subgroups=True)
        subgroups = new_top.subgroups.list(all_available=True)
        for sub in subgroups:
            logging.debug('Found sub-group %s', sub.full_path)
            src_group_tree.create_node(sub.path, sub.id, parent=new_top.id, data=sub.name)
            logging.debug('Added node to tree with id %s', sub.id)
            new_parent = gl.groups.get(sub.full_path, include_subgroups=True)
            new_subgroup = new_parent.subgroups.list(all_available=True)
            for child in new_subgroup:
                logging.debug('Traversing group %s', child.full_path)
                get_sub_groups(new_parent)
    get_sub_groups(top_level_group)
    src_group_tree.show()
    print(src_group_tree.to_json(with_data=True))
    return src_group_tree


if __name__ == "__main__":
    main()

logging.debug('End of Script')
