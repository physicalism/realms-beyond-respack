"""Build a release, optionally push commits, then create a GitHub draft release."""
import argparse
import shutil
import subprocess
import sys
from build import ROOT, build, version


def run(*args, capture=False):
    result = subprocess.run(args, cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--push', action='store_true', help='Push main before creating the draft; never force-push.')
    parser.add_argument('--dry-run', action='store_true', help='Build and show the release command without changing GitHub.')
    parser.add_argument('--publish', action='store_true', help='Publish directly instead of creating a draft.')
    args = parser.parse_args()
    output = build()
    tag = 'v'+version()
    if args.dry_run:
        print(f'Would create GitHub draft {tag}, attaching {output.name} and its checksum.')
        print('Would push main first.' if args.push else 'Requires main to have been pushed already.')
        return
    if not shutil.which('gh'):
        raise ValueError('GitHub CLI is required. Install it and run gh auth login first.')
    if run('git', 'branch', '--show-current', capture=True) != 'main':
        raise ValueError('Switch to main before making a release.')
    status = run('git', 'status', '--porcelain', capture=True)
    pending = [line for line in status.splitlines() if not line.startswith('?? builds/')]
    if pending:
        raise ValueError('Commit or set aside local changes before making a release.')
    run('gh', 'auth', 'status')
    commit = run('git', 'rev-parse', 'HEAD', capture=True)
    if args.push:
        run('git', 'push', 'origin', 'main')
    remote = run('git', 'ls-remote', 'origin', 'refs/heads/main', capture=True)
    if not remote or remote.split()[0] != commit:
        raise ValueError('Remote main does not match this commit. Push it in GitHub Desktop, or use --push.')
    run('gh', 'release', 'create', tag, str(output), str(output.with_suffix('.zip.sha256')),
        '--target', commit, *([] if args.publish else ['--draft']), '--title', f'Realms Beyond {tag}', '--notes-file', str(ROOT/'tools'/'release-notes.md'))
    print('Release published.' if args.publish else 'Draft release created.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(f'Release failed: {error}')
