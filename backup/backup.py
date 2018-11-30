import py
from datetime import date
import os
ROOT = py.path.local(__file__).dirpath('..')
BACKUP = ROOT.join('backup')
DB = ROOT.join('project.db')

newname = 'project-%s.db' % (date.today().isoformat())
DEST = BACKUP.join(newname)
DB.copy(DEST)
os.system('bzip2 "%s"' % DEST)
