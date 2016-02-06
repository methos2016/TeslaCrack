"""
TestCases for teslacrypt.

It needs a `bash` (cygwin or git-for-windows) because that was an easy way
to make files/dirs inaccessible, needed for TCs.
"""
from __future__ import print_function

import argparse
import glob
import os
import sys
import textwrap
import unittest

import ddt
import yaml

import teslacrack
import unfactor


app_db_txt = r"""
keys:
    - name     : ankostis
      type     : AES
      encrypted: 7097DDB2E5DD08950D18C263A41FF5700E7F2A01874B20F402680752268E43F4C5B7B26AF2642AE37BD64AB65B6426711A9DC44EA47FC220814E88009C90EA
      decrypted: \x01\x7b\x16\x47\xd4\x24\x2b\xc6\x7c\xe8\xa6\xaa\xec\x4d\x8b\x49\x3f\x35\x51\x9b\xd8\x27\x75\x62\x3d\x86\x18\x21\x67\x14\x8d\xd9
      factors  :
        - 2
        - 7
        - 97
        - 131
        - 14983
        - 28099
        - 4030421
        - 123985129
        - 2124553904704757231
        - 2195185826800714519
        - 5573636538860090464486823831839
        - 23677274243760534899430414029178304942110152493113248247
      crypted_files:
        - tesla2.pdf.vvv

    - name     : hermanndp
      type     : AES
      encrypted: 07E18921C536C112A14966D4EAAD01F10537F77984ADAAE398048F12685E2870CD1968FE3317319693DA16FFECF6A78EDBC325DDA2EE78A3F9DF8EEFD40299D9
      decrypted: \x1b\x5c\x52\xaa\xfc\xff\xda\x2e\x71\x00\x1c\xf1\x88\x0f\xe4\x5c\xb9\x3d\xea\x4c\x71\x32\x8d\xf5\x95\xcb\x5e\xb8\x82\xa3\x97\x9f'
      factors  :
        - 13
        - 3631
        - 129949621
        - 772913651
        - 7004965235626057660321517749245179
        - 4761326544374734107426225922123841005827557
        - 2610294590708970742101938252592668460113250757564649051
      crypted_files:
        - tesla_key3.doc.vvv
        - tesla_key3.pdf.zzz

"""

# def config_yaml():
#     """From http://stackoverflow.com/a/21048064/548792"""
#     yaml.add_representer(OrderedDict, lambda dumper, data:
#             dumper.represent_dict(data.items()))
#     yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
#             lambda loader, node: OrderedDict(loader.construct_pairs(node)))
# config_yaml()

def read_app_db():
    return yaml.load(textwrap.dedent(app_db_txt))

app_db = read_app_db()


@ddt.ddt
class TUnfactor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.chdir(os.path.dirname(__file__))

    @ddt.data(*[k for k in app_db['keys'] if k['type'] == 'AES'])
    def test_undecrypt_AES_keys(self, key_rec):
        for f in key_rec.get('crypted_files', ()):
            factors = [int(fc) for fc in key_rec['factors']]
            exp_aes_key = key_rec['decrypted']
            aes_key = unfactor.undecrypt(f, factors)
            #print(key_rec['name'], f, aes_key, exp_aes_key)
            self.assertIn(exp_aes_key, aes_key,
                    (key_rec['name'], f, aes_key, exp_aes_key))

def chmod(mode, files):
    files = ' '.join("'%s'" % f for f in files)
    cmd = 'bash -c "chmod %s %s"' % (mode, files)
    ret = os.system(cmd)
    if ret:
        print("Bash-cmd `chmod` failed with: %s "
              "\n  TCs below may also fail, unless you mark manually `unreadable*` files!"
              % ret,
              file=sys.stderr)

class TTeslacrack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.chdir(os.path.dirname(__file__))
        ## Mark unreadable-files.
        chmod('115', glob.glob('unreadable*'))


    @classmethod
    def tearDownClass(cls):
        os.chdir(os.path.dirname(__file__))
        ## UNMark unreadable-files.
        chmod('775', glob.glob('unreadable*'))


    min_scanned_files = 18

    def setUp(self):
        """
        Delete all generated decrypted-files.

        Note that tests below should not modify git-files.
        """
        #
        skip_ext = ['.py', '.ccc', '.vvv', '.zzz']
        skip_files = ['bad_decrypted', 'README']
        for f in glob.glob('*'):
            if (os.path.isfile(f) and
                    os.path.splitext(f)[1] not in skip_ext and
                    not [sf for sf in skip_files if sf in f]):
                os.unlink(f)

    def test_statistics_normal(self):
        opts = argparse.Namespace(delete=False, delete_old=False, dry_run=False,
                fix=False, fpaths=['.'], overwrite=False, progress=False,
                verbose=True)
        stats = teslacrack.teslacrack(opts)
        self.assertGreater(stats.scanned_nfiles, self.min_scanned_files)
        stats.scanned_nfiles = -1 ## arbitrary
        #print(stats)
        exp_stats = argparse.Namespace(
                badexisting_nfiles=1,
                badheader_nfiles=1,
                crypted_nfiles=11,
                decrypted_nfiles=6,
                deleted_nfiles=0,
                failed_nfiles=2,
                ndirs=-1,
                noaccess_ndirs=1,
                overwrite_nfiles=0,
                scanned_nfiles=-1,
                skip_nfiles=2,
                tesla_nfiles=13,
                unknown_nfiles=2,
                visited_ndirs=9)

        self.assertEquals(stats, exp_stats)


    def test_statistics_fix_dryrun(self):
        opts = argparse.Namespace(delete=False, delete_old=False, dry_run=False,
                fix=False, fpaths=['.'], overwrite=False, progress=False,
                verbose=True)
        teslacrack.teslacrack(opts)
        opts.dry_run=True
        opts.fix=True
        stats = teslacrack.teslacrack(opts)
        self.assertGreater(stats.scanned_nfiles, self.min_scanned_files)
        stats.scanned_nfiles = -1 ## arbitrary
        #print(stats)
        exp_stats = argparse.Namespace(badexisting_nfiles=1,
                badheader_nfiles=1,
                crypted_nfiles=11,
                decrypted_nfiles=1,
                deleted_nfiles=0,
                failed_nfiles=2,
                ndirs=-1,
                noaccess_ndirs=1,
                overwrite_nfiles=1,
                scanned_nfiles=-1,
                skip_nfiles=7,
                tesla_nfiles=13,
                unknown_nfiles=2,
                visited_ndirs=9)
        self.assertEquals(stats, exp_stats)


    def test_statistics_overwrite_dryrun(self):
        opts = argparse.Namespace(delete=False, delete_old=False, dry_run=False,
                fix=False, fpaths=['.'], overwrite=False, progress=False,
                verbose=True)
        teslacrack.teslacrack(opts)
        opts.dry_run=True
        opts.overwrite=True
        stats = teslacrack.teslacrack(opts)
        self.assertGreater(stats.scanned_nfiles, self.min_scanned_files)
        stats.scanned_nfiles = -1 ## arbitrary
        print(stats)
        exp_stats = argparse.Namespace(badexisting_nfiles=0,
                    badheader_nfiles=1,
                    crypted_nfiles=11,
                    decrypted_nfiles=8,
                    deleted_nfiles=0,
                    failed_nfiles=2,
                    ndirs=-1,
                    noaccess_ndirs=1,
                    overwrite_nfiles=8,
                    scanned_nfiles=-1,
                    skip_nfiles=0,
                    tesla_nfiles=13,
                    unknown_nfiles=2,
                    visited_ndirs=9)
        self.assertEquals(stats, exp_stats)


    def test_statistics_delete_dryrun(self):
        opts = argparse.Namespace(delete=False, delete_old=False, dry_run=False,
                fix=False, fpaths=['.'], overwrite=False, progress=False,
                verbose=True)
        teslacrack.teslacrack(opts)
        opts.dry_run=True
        opts.delete=True
        stats = teslacrack.teslacrack(opts)
        self.assertGreater(stats.scanned_nfiles, self.min_scanned_files)
        self.assertGreater(stats.scanned_nfiles, self.min_scanned_files)
        stats.scanned_nfiles = -1 ## arbitrary
        #print(stats)
        exp_stats = argparse.Namespace(badexisting_nfiles=1,
                badheader_nfiles=1,
                crypted_nfiles=11,
                decrypted_nfiles=0,
                deleted_nfiles=0,
                failed_nfiles=2,
                ndirs=-1,
                noaccess_ndirs=1,
                overwrite_nfiles=0,
                scanned_nfiles=-1,
                skip_nfiles=8,
                tesla_nfiles=13,
                unknown_nfiles=2,
                visited_ndirs=9)
        self.assertEquals(stats, exp_stats)


    def test_statistics_delete_old_dryrun(self):
        opts = argparse.Namespace(delete=False, delete_old=False, dry_run=False,
                fix=False, fpaths=['.'], overwrite=False, progress=False,
                verbose=True)
        teslacrack.teslacrack(opts)
        opts.dry_run=True
        opts.delete_old=True
        stats = teslacrack.teslacrack(opts)
        self.assertGreater(stats.scanned_nfiles, self.min_scanned_files)
        stats.scanned_nfiles = -1 ## arbitrary
        #print(stats)
        exp_stats = argparse.Namespace(badexisting_nfiles=1,
                    badheader_nfiles=1,
                    crypted_nfiles=11,
                    decrypted_nfiles=0,
                    deleted_nfiles=8,
                    failed_nfiles=2,
                    ndirs=-1,
                    noaccess_ndirs=1,
                    overwrite_nfiles=0,
                    scanned_nfiles=-1,
                    skip_nfiles=8,
                    tesla_nfiles=13,
                    unknown_nfiles=2,
                    visited_ndirs=9)
        self.assertEquals(stats, exp_stats)


