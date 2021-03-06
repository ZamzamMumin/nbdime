#!/usr/bin/env python
"""A git difftool plugin for notebooks.

Uses nbdime to display diffs of notebooks instead of plain text diffs of JSON.
Other files are displayed via `git diff`.

Enable in your global git config with:

    git-nbdifftool config --enable [--global | --system]

Use with:

    git difftool [<commit> [<commit>]]
"""
import os
import sys
from subprocess import check_call, check_output, CalledProcessError

import nbdime.log
from .args import add_generic_args, add_git_config_subcommand
from .webapp import nbdifftool


def enable(scope=None, set_default=False):
    """Enable nbdime git difftool"""
    cmd = ['git', 'config']
    if scope:
        assert scope in ('global', 'system')
        cmd.append('--' + scope)

    check_call(cmd + ['difftool.nbdime.cmd', 'git-nbdifftool diff "$LOCAL" "$REMOTE"'])
    if set_default:
        check_call(cmd + ['diff.guitool', 'nbdime'])

    # Common setting:
    check_call(cmd + ['difftool.prompt', 'false'])


def disable(scope=None, *args):
    """Disable nbdime git difftool"""
    cmd = ['git', 'config']
    if scope:
        assert scope in ('global', 'system')
        cmd.append('--' + scope)
    try:
        tool = check_output(cmd + ['diff.guitool']).decode('utf8', 'replace').strip()
    except CalledProcessError:
        pass
    else:
        if tool == 'nbdime':
            try:
                check_call(cmd + ['--unset', 'diff.guitool'])
            except CalledProcessError:
                # already unset
                pass


def show_diff(before, after, opts):
    """Run the difftool

    If we are diffing a notebook, show the diff via nbdiff-web.
    Otherwise, call out to `git diff`.
    """
    if before.endswith('.ipynb') or after.endswith('ipynb'):
        return nbdifftool.main_parsed(opts)
    else:
        # Never returns
        os.execvp('git', ['git', 'diff', before, after])


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import argparse
    parser = argparse.ArgumentParser('git-nbdifftool', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_generic_args(parser)
    subparsers = parser.add_subparsers(dest='subcommand')

    diff_parser = subparsers.add_parser('diff',
        description="The actual entrypoint for the diff tool. Git will call this."
    )
    nbdifftool.build_arg_parser(diff_parser)

    config = add_git_config_subcommand(subparsers,
        enable, disable,
        subparser_help="Configure git to use nbdime via `git difftool`",
        enable_help="enable nbdime difftool via git config",
        disable_help="disable nbdime difftool via git config")
    config.add_argument('--set-default', action='store_true', dest='set_default',
        help="set nbdime as default gui difftool"
    )

    opts = parser.parse_args(args)
    nbdime.log.init_logging(level=opts.log_level)
    if opts.subcommand == 'diff':
        return show_diff(opts.local, opts.remote, opts)
    elif opts.subcommand == 'config':
        opts.config_func(opts.scope, opts.set_default)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
